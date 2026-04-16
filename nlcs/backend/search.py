# PageIndex-backed hybrid search for Natural Language Candidate Search

import hashlib
import json
import os
import re
import sys
import time
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from collections import Counter, defaultdict
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.orm import Session

current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

load_dotenv(parent_dir / ".env")

try:
    from models import Candidate
except ImportError:
    from backend.models import Candidate

try:
    from prompts import SINGLE_RESUME_PROMPT
except ImportError:
    from backend.prompts import SINGLE_RESUME_PROMPT

try:
    from ingest import build_pageindex_tree_from_pdf, compress_tree
except ImportError:
    from backend.ingest import build_pageindex_tree_from_pdf, compress_tree

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if GROQ_AVAILABLE and GROQ_API_KEY:
    groq_client = Groq(api_key=GROQ_API_KEY)
else:
    groq_client = None

RESULTS_LIMIT = 5
SHORTLIST_SIZE = 12
CACHE_TTL = 3600
SEARCH_VERSION = "v7"
GROQ_MODELS = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
ENABLE_LLM_ROUTING = os.getenv("ENABLE_LLM_ROUTING", "false").lower() == "true"
ROUTING_TIMEOUT_SEC = float(os.getenv("ROUTING_TIMEOUT_SEC", "1.2"))
RERANK_TIMEOUT_SEC = float(os.getenv("RERANK_TIMEOUT_SEC", "3.2"))
MAX_TOTAL_LATENCY_MS = float(os.getenv("MAX_TOTAL_LATENCY_MS", "6000"))


STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in",
    "is", "it", "of", "on", "or", "that", "the", "this", "to", "with",
    "who", "what", "when", "where", "why", "how", "find", "show", "me",
    "search", "candidate", "candidates", "someone", "person", "role", "need",
    "looking", "for"
}

search_cache = {}
llm_executor = ThreadPoolExecutor(max_workers=2)

# Domain anchors to keep stage-1 routing grounded in query evidence.
CATEGORY_ANCHORS = {
    "information technology": {
        "it", "helpdesk", "itsm", "ticket", "tickets", "network", "desktop", "server",
        "troubleshoot", "troubleshooting", "active directory", "user account", "support", "technical"
    },
    "engineering": {"engineer", "engineering", "systems", "infrastructure", "network", "hardware"},
    "finance": {"finance", "financial", "valuation", "accounting", "analyst", "banking", "m&a"},
    "accountant": {"accountant", "ledger", "reconciliation", "audit", "balance", "payroll"},
    "banking": {"banking", "investment", "m&a", "valuation", "portfolio", "analyst"},
    "hr": {"hr", "human resources", "employee relations", "talent", "recruitment", "workforce"},
    "healthcare": {"healthcare", "clinical", "patient", "provider", "hospital", "nurse", "physician"},
    "sales": {"sales", "quota", "pipeline", "territory", "account", "revenue"},
    "digital media": {"digital", "media", "campaign", "ads", "marketing", "newsletter", "press"},
    "public relations": {"public relations", "press", "media", "communications", "editorial"},
}


def category_anchor_score(query: str, category_name: str) -> float:
    """Score category relevance from explicit domain anchors in the query."""
    query_norm = normalize_text(query)
    anchors = CATEGORY_ANCHORS.get(normalize_text(category_name), set())
    score = 0.0
    for anchor in anchors:
        if anchor in query_norm:
            score += 2.5 if " " in anchor else 1.2
    return score


def infer_preferred_categories(query: str) -> set:
    """Infer preferred categories from strong intent phrases in query text."""
    q = normalize_text(query)
    preferred = set()
    if any(term in q for term in ["helpdesk", "itsm", "user account", "desktop", "network troubleshooting", "technical support"]):
        preferred.update({"Information Technology", "Engineering"})
    if any(term in q for term in ["hr", "human resources", "employee relations", "workforce planning", "talent acquisition"]):
        preferred.add("Hr")
    if any(term in q for term in ["healthcare", "clinical", "provider", "physician", "nurse"]):
        preferred.add("Healthcare")
    if any(term in q for term in ["accounting", "ledger", "reconciliation", "payroll", "audit"]):
        preferred.add("Accountant")
    if any(term in q for term in ["investment banking", "valuation", "m&a", "portfolio"]):
        preferred.add("Banking")
    return preferred


def infer_excluded_categories(query: str) -> set:
    """Infer categories to avoid when intent clearly points elsewhere."""
    q = normalize_text(query)
    excluded = set()

    it_support_intent = any(
        term in q
        for term in ["helpdesk", "itsm", "user account", "desktop", "network troubleshooting", "technical support"]
    )
    has_finance_terms = any(term in q for term in ["finance", "financial", "accounting", "valuation", "m&a", "banking"])

    if it_support_intent and not has_finance_terms:
        excluded.update({"Finance", "Accountant", "Banking"})

    return excluded


def normalize_text(value: str) -> str:
    """Normalize text for matching."""
    value = value or ""
    value = value.lower()
    value = re.sub(r"[^a-z0-9\s]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def extract_query_terms(query: str) -> list:
    """Extract unigram, bigram, and trigram search terms."""
    tokens = [token for token in normalize_text(query).split() if len(token) >= 3 and token not in STOPWORDS]
    terms = []
    seen = set()

    def add(term: str):
        if term and term not in seen:
            seen.add(term)
            terms.append(term)

    for token in tokens:
        add(token)

    for size in (2, 3):
        for index in range(len(tokens) - size + 1):
            add(" ".join(tokens[index:index + size]))

    return terms


def get_cache_key(query: str, candidate_count: int) -> str:
    """Generate a cache key that invalidates when the search strategy changes."""
    return hashlib.md5(f"{SEARCH_VERSION}|{query}|{candidate_count}".encode()).hexdigest()


def candidate_search_blob(candidate) -> str:
    """Build a searchable string from a candidate's stored tree and metadata."""
    parts = [candidate.name or "", candidate.category or "", candidate.file_path or ""]
    try:
        tree = json.loads(candidate.tree_compressed) if candidate.tree_compressed else []
    except Exception:
        tree = []

    if isinstance(tree, list):
        for node in tree:
            if isinstance(node, dict):
                parts.append(str(node.get("title", "")))
                parts.append(str(node.get("summary", "")))

    return normalize_text(" ".join(parts))


def extract_keywords(text: str, limit: int = 20) -> list:
    """Extract frequent non-stopword tokens for meta-tree summaries."""
    tokens = [t for t in normalize_text(text).split() if len(t) >= 3 and t not in STOPWORDS]
    if not tokens:
        return []
    freq = Counter(tokens)
    return [token for token, _ in freq.most_common(limit)]


def build_meta_tree(candidates: list) -> dict:
    """Build a lightweight meta tree over all candidates.

    Structure:
    root
      └── category nodes (with top keywords + candidate ids)
    """
    by_category = defaultdict(list)
    for candidate in candidates:
        category = (candidate.category or "Uncategorized").strip() or "Uncategorized"
        by_category[category].append(candidate)

    categories = []
    for category_name, rows in sorted(by_category.items(), key=lambda x: x[0].lower()):
        aggregate_blob = " ".join(candidate_search_blob(row) for row in rows)
        top_keywords = extract_keywords(aggregate_blob, limit=25)
        categories.append(
            {
                "name": category_name,
                "candidate_count": len(rows),
                "candidate_ids": [row.id for row in rows],
                "keywords": top_keywords,
            }
        )

    return {
        "total_candidates": len(candidates),
        "category_count": len(categories),
        "categories": categories,
    }


def meta_tree_for_prompt(meta_tree: dict) -> str:
    """Render compact meta tree for stage-1 LLM routing."""
    lines = [
        f"total_candidates: {meta_tree.get('total_candidates', 0)}",
        f"category_count: {meta_tree.get('category_count', 0)}",
        "categories:",
    ]

    for cat in meta_tree.get("categories", []):
        lines.append(
            f"- {cat['name']} | count={cat['candidate_count']} | keywords={', '.join(cat.get('keywords', [])[:15])}"
        )
    return "\n".join(lines)


def llm_route_meta_tree(query: str, meta_tree: dict) -> dict | None:
    """Stage-1 route: choose best categories before drilling into candidate trees."""
    if not groq_client:
        return None

    prompt = f"""You are routing a recruiter query to the best resume branches.

Query:
{query}

Meta tree:
{meta_tree_for_prompt(meta_tree)}

Task:
- Select up to 3 most relevant categories.
- Give a short reason.

Return ONLY valid JSON in this format:
{{
  "selected_categories": ["Information Technology", "Finance"],
  "reasoning": "Why these categories are best for the query"
}}"""

    last_error = None
    for model in GROQ_MODELS:
        try:
            future = llm_executor.submit(
                groq_client.chat.completions.create,
                model=model,
                messages=[
                    {"role": "system", "content": "Return only valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=180,
                response_format={"type": "json_object"},
            )
            response = future.result(timeout=ROUTING_TIMEOUT_SEC)
            return json.loads(response.choices[0].message.content)
        except FutureTimeoutError:
            last_error = f"timeout@{model}"
        except Exception as exc:
            last_error = exc

    if last_error:
        print(f"⚠️ Meta-tree routing unavailable: {str(last_error)[:120]}")
    return None


def deterministic_category_routing(query: str, meta_tree: dict, top_k: int = 3) -> list:
    """Fallback stage-1 routing using keyword overlap on category summaries."""
    terms = extract_query_terms(query)
    scored = []
    for cat in meta_tree.get("categories", []):
        text = normalize_text(" ".join([cat["name"]] + cat.get("keywords", [])))
        score = 0.0
        for term in terms:
            if term in text:
                score += 2.0 if " " in term else 1.0
        scored.append((score, cat["name"]))

    scored.sort(key=lambda x: (-x[0], x[1]))
    return [name for score, name in scored[:top_k] if score > 0]


def merge_unique(primary: list, secondary: list) -> list:
    """Merge category lists while preserving the first-seen order."""
    merged = []
    seen = set()
    for item in primary + secondary:
        if item and item not in seen:
            seen.add(item)
            merged.append(item)
    return merged


def candidate_relevance_score(query: str, candidate) -> float:
    """Deterministic shortlist score using stored PageIndex tree text."""
    query_terms = extract_query_terms(query)
    searchable = candidate_search_blob(candidate)
    title_blob = normalize_text(f"{candidate.name or ''} {candidate.category or ''}")

    score = 0.0
    for term in query_terms:
        if term in searchable:
            score += 3.5 if " " in term else 1.8
        if term in title_blob:
            score += 1.2

    if normalize_text(query) and normalize_text(query) in searchable:
        score += 8.0

    section_boosts = {
        "skills": 2.5,
        "experience": 2.5,
        "projects": 2.0,
        "education": 1.0,
        "summary": 1.0,
    }
    for section, boost in section_boosts.items():
        if section in searchable:
            score += boost

    if any(term in normalize_text(query) for term in ["lead", "manage", "team", "ownership"]):
        if any(term in searchable for term in ["led", "manage", "managed", "lead", "team"]):
            score += 4.0

    preferred_categories = infer_preferred_categories(query)
    candidate_category = (candidate.category or "").strip()
    if preferred_categories:
        if candidate_category in preferred_categories:
            score += 6.0
        elif candidate_category:
            score -= 1.5

    return score


def token_set(text: str) -> set:
    """Token set for overlap calculations."""
    return set(extract_query_terms(text))


def overlap_ratio(query: str, candidate) -> float:
    """How much of query terms appear in candidate text."""
    q_terms = token_set(query)
    if not q_terms:
        return 0.0
    c_terms = token_set(candidate_search_blob(candidate))
    if not c_terms:
        return 0.0
    common = q_terms.intersection(c_terms)
    return len(common) / max(1, len(q_terms))


def query_looks_like_resume_excerpt(query: str) -> bool:
    """Detect pasted resume text so routing can favor global overlap over category guesses."""
    normalized = query or ""
    token_count = len(extract_query_terms(normalized))
    line_breaks = normalized.count("\n")
    bullet_markers = normalized.count("-") + normalized.count("•")
    return token_count >= 24 or line_breaks >= 3 or bullet_markers >= 4


def build_candidate_context(candidate, score_hint: float) -> str:
    """Create compact context for LLM ranking."""
    try:
        tree = json.loads(candidate.tree_compressed) if candidate.tree_compressed else []
    except Exception:
        tree = []

    lines = [
        f"candidate_id: {candidate.id}",
        f"name: {candidate.name}",
        f"category: {candidate.category}",
        f"score_hint: {score_hint:.2f}",
        "tree:"
    ]

    if isinstance(tree, list) and tree:
        for node in tree[:3]:
            if isinstance(node, dict):
                lines.append(f"- {node.get('title', '')}: {node.get('summary', '')[:150]}")
    else:
        lines.append("- No tree data available")

    return "\n".join(lines)


def extract_section_evidence(candidate, query: str, max_sections: int = 3) -> list:
    """Extract the strongest PageIndex section matches for a candidate."""
    query_terms = extract_query_terms(query)
    if not query_terms:
        return []

    try:
        tree = json.loads(candidate.tree_compressed) if candidate.tree_compressed else []
    except Exception:
        tree = []

    if not isinstance(tree, list):
        return []

    evidence = []
    for node in tree:
        if not isinstance(node, dict):
            continue

        title = str(node.get("title", "")).strip()
        summary = str(node.get("summary", "")).strip()
        searchable = normalize_text(f"{title} {summary}")
        matched_terms = [term for term in query_terms if term in searchable]
        if not matched_terms:
            continue

        unique_terms = list(dict.fromkeys(matched_terms))
        section_score = 2.0 * len(unique_terms)
        section_score += sum(1.1 if " " in term else 0.7 for term in unique_terms)

        normalized_title = normalize_text(title)
        if normalized_title in {"summary", "skills", "experience", "projects", "education", "education and training", "accomplishments", "certifications"}:
            section_score += 1.0

        evidence.append({
            "title": title or "Unknown section",
            "matched_terms": unique_terms,
            "score": section_score,
        })

    evidence.sort(key=lambda item: (-item["score"], item["title"].lower()))
    return evidence[:max_sections]


def format_section_evidence(evidence: list) -> list:
    """Render matched section evidence for API responses."""
    formatted = []
    for item in evidence:
        title = item.get("title", "Unknown section")
        terms = item.get("matched_terms", [])[:5]
        if terms:
            formatted.append(f"{title} ({', '.join(terms)})")
        else:
            formatted.append(title)
    return formatted


def build_candidate_explanation(candidate, query: str, evidence: list | None = None) -> tuple[list, str, set]:
    """Build a deterministic explanation from the stored PageIndex tree."""
    evidence = evidence if evidence is not None else extract_section_evidence(candidate, query)
    matched_terms = set()
    for item in evidence:
        matched_terms.update(item.get("matched_terms", []))

    if evidence:
        section_bits = []
        for item in evidence:
            title = item.get("title", "Unknown section")
            terms = ", ".join(item.get("matched_terms", [])[:5])
            section_bits.append(f"{title}: {terms}" if terms else title)

        strongest = evidence[0]
        explanation = (
            f"Matched {len(evidence)} PageIndex section(s): {'; '.join(section_bits)}. "
            f"Strongest hit was {strongest.get('title', 'Unknown section')} with {', '.join(strongest.get('matched_terms', [])[:5])}."
        )
        return format_section_evidence(evidence), explanation, matched_terms

    category = candidate.category or "Unknown"
    explanation = (
        f"No exact section overlap found in the compressed tree; kept because the resume metadata and {category} category still align with the query."
    )
    return [f"{candidate.category or 'Unknown'} category metadata"], explanation, matched_terms


def build_search_reasoning(query: str, selected_categories: list, final_results: list, candidate_lookup: dict, ranking_method: str, anchor_candidate=None, anchor_overlap: float = 0.0) -> str:
    """Summarize why the final ranking chose the returned candidates."""
    parts = []

    if selected_categories:
        anchor_evidence = {cat: round(category_anchor_score(query, cat), 2) for cat in selected_categories}
        parts.append(f"Stage-1 routed to {selected_categories} using domain anchors {anchor_evidence}.")
    else:
        parts.append("Stage-1 used all categories because no strong domain anchor was detected.")

    if not final_results:
        return " ".join(parts)

    top_candidate_row = final_results[0]
    top_candidate = candidate_lookup.get(top_candidate_row.get("candidate_id"))
    top_terms = set()
    top_sections = []
    if top_candidate:
        top_sections, _, top_terms = build_candidate_explanation(top_candidate, query)

    if len(final_results) > 1:
        runner_row = final_results[1]
        runner_candidate = candidate_lookup.get(runner_row.get("candidate_id"))
        runner_terms = set()
        runner_sections = []
        if runner_candidate:
            runner_sections, _, runner_terms = build_candidate_explanation(runner_candidate, query)

        top_section_text = ", ".join(top_sections[:2]) if top_sections else "no exact section matches"
        runner_section_text = ", ".join(runner_sections[:2]) if runner_sections else "fewer exact section matches"
        top_term_count = len(top_terms)
        runner_term_count = len(runner_terms)

        if top_candidate and runner_candidate:
            parts.append(
                f"Top result {top_candidate.name} won because it matched {top_section_text} with {top_term_count} exact query term(s), while {runner_candidate.name} only matched {runner_section_text} with {runner_term_count} term(s)."
            )

    if anchor_candidate and anchor_overlap >= 0.45:
        parts.append(
            f"An exact-overlap anchor was also applied for candidate {anchor_candidate.id} (overlap={anchor_overlap:.2f})."
        )

    if ranking_method == "heuristic":
        parts.append("LLM reranking timed out or was unavailable, so the final order fell back to deterministic tree overlap scoring.")
    else:
        parts.append("LLM reranking ordered the shortlist after the deterministic stage-1 filter.")

    return " ".join(parts)


def heuristic_results(ranked_candidates: list, limit: int) -> list:
    """Fallback results when Groq is unavailable."""
    if not ranked_candidates:
        return []

    top_score = ranked_candidates[0][0]
    low_score = ranked_candidates[min(len(ranked_candidates) - 1, limit * 3 - 1)][0]
    span = max(1e-6, top_score - low_score)

    results = []
    for score, candidate in ranked_candidates[:limit]:
        normalized = (score - low_score) / span
        match_score = int(55 + normalized * 43)
        results.append({
            "candidate_id": candidate.id,
            "name": candidate.name,
            "category": candidate.category,
            "match_score": int(max(40, min(98, match_score))),
            "matched_sections": [],
            "explanation": "Heuristic match from stored PageIndex tree and resume metadata",
            "file_path": candidate.file_path,
        })
    return results


def llm_rank_candidates(query: str, shortlist: list) -> dict | None:
    """Use Groq to rerank the shortlisted candidates."""
    if not groq_client:
        return None

    candidate_blocks = [build_candidate_context(candidate, score) for score, candidate in shortlist]
    prompt = f"""You are an expert recruiter ranking resumes.

Query:
{query}

Instructions:
- Rank candidates by semantic fit to the query.
- Prefer evidence from skills, projects, and experience.
- Do not invent facts that are not in the candidate tree.
- Return the top 5 candidates only.
- If the query is broad, prefer the closest professional match.

Candidate trees:
{chr(10).join(candidate_blocks)}

Return only this JSON format:
{{
  "candidates": [
    {{
      "candidate_id": 1,
      "name": "Candidate Name",
      "category": "Category",
      "match_score": 92,
      "matched_sections": ["Skills", "Experience"],
      "explanation": "Why this candidate matches"
    }}
  ],
  "search_reasoning": "Short explanation of how you ranked the results"
}}"""

    last_error = None
    for model in GROQ_MODELS:
        try:
            future = llm_executor.submit(
                groq_client.chat.completions.create,
                model=model,
                messages=[
                    {"role": "system", "content": "You are a precise recruiter and you return only valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=420,
                response_format={"type": "json_object"},
            )
            response = future.result(timeout=RERANK_TIMEOUT_SEC)
            payload = json.loads(response.choices[0].message.content)
            payload.setdefault("search_reasoning", f"Reranked with {model}")
            return payload
        except FutureTimeoutError:
            last_error = f"timeout@{model}"
        except Exception as exc:
            last_error = exc

    if last_error:
        print(f"⚠️ LLM ranking unavailable: {str(last_error)[:120]}")
    return None


def extract_text_from_image_bytes(image_bytes: bytes) -> str:
    """Extract text from an image using local Tesseract OCR."""
    if not image_bytes:
        return ""

    try:
        from PIL import Image

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_image:
            temp_image.write(image_bytes)
            temp_image_path = temp_image.name

        try:
            image = Image.open(temp_image_path)
            # Basic preprocessing helps Tesseract on dark screenshots.
            if image.mode not in ("RGB", "L"):
                image = image.convert("RGB")
            image.save(temp_image_path)

            result = subprocess.run(
                ["/opt/homebrew/bin/tesseract", temp_image_path, "stdout", "--psm", "6"],
                capture_output=True,
                text=True,
                check=False,
            )
            return (result.stdout or "").strip()
        finally:
            try:
                os.unlink(temp_image_path)
            except Exception:
                pass
    except Exception as exc:
        print(f"⚠️ OCR extraction failed: {exc}")
        return ""


def clean_jd_text(raw_text: str) -> dict:
    """Turn OCR text into a clean JD using a text LLM."""
    text = (raw_text or "").strip()
    if not text:
        return {"jd_text": "", "reasoning": "OCR produced no text", "status": "empty"}

    if not groq_client:
        return {
            "jd_text": text,
            "reasoning": "Groq not configured; returning OCR text as-is",
            "status": "ok",
            "model_used": "ocr-only",
        }

    prompt = f"""You are cleaning OCR output from a hiring/posting screenshot.

OCR text:
{text}

Task:
- Convert the OCR text into a clean job description.
- Preserve role title, required skills, responsibilities, years of experience, and domain.
- Remove duplicated fragments, OCR noise, and trailing punctuation artifacts.
- Return concise recruiter-friendly plain text.

Return only valid JSON in this format:
{{
  "jd_text": "clean extracted job description text",
  "reasoning": "brief note on what was extracted"
}}
"""

    last_error = None
    for model in GROQ_MODELS:
        try:
            response = groq_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Return only valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=700,
                response_format={"type": "json_object"},
            )
            payload = json.loads(response.choices[0].message.content)
            jd_text = (payload.get("jd_text") or "").strip()
            return {
                "jd_text": jd_text or text,
                "reasoning": payload.get("reasoning", ""),
                "status": "ok" if (jd_text or text) else "empty",
                "model_used": model,
            }
        except Exception as exc:
            last_error = exc

    return {
        "jd_text": text,
        "reasoning": f"Groq cleanup failed; using OCR text. Last error: {str(last_error)[:180] if last_error else 'unknown'}",
        "status": "ok",
        "model_used": "ocr-only-fallback",
    }


def extract_jd_from_image(image_bytes: bytes, mime_type: str = "image/png") -> dict:
    """Extract a clean job description from a hiring/job-post screenshot using local OCR + text cleanup."""
    if not image_bytes:
        return {
            "jd_text": "",
            "reasoning": "No image content provided",
            "status": "error",
        }

    raw_text = extract_text_from_image_bytes(image_bytes)
    return clean_jd_text(raw_text)


def search_candidates(query: str, limit: int, db_session: Session) -> dict:
    """Search candidates using PageIndex-backed tree data with LLM reranking."""
    try:
        all_candidates = db_session.query(Candidate).all()
        if not all_candidates:
            return {"candidates": [], "search_reasoning": "No candidates"}

        cache_key = get_cache_key(query, len(all_candidates))
        if cache_key in search_cache:
            cached_result, cached_time = search_cache[cache_key]
            if time.time() - cached_time < CACHE_TTL:
                print("🚀 CACHE HIT: Instant results!")
                return cached_result

        print(f"\n🔍 SEARCHING: {query}")
        print(f"📊 Total candidates: {len(all_candidates)}")

        # Stage 1: meta-tree routing to reduce search scope before detailed ranking.
        meta_tree = build_meta_tree(all_candidates)
        route_result = llm_route_meta_tree(query, meta_tree) if ENABLE_LLM_ROUTING else None

        selected_categories = []
        deterministic_categories = []
        if route_result and isinstance(route_result.get("selected_categories"), list):
            selected_categories = [str(c).strip() for c in route_result.get("selected_categories", []) if str(c).strip()]

        deterministic_categories = deterministic_category_routing(query, meta_tree, top_k=5)
        if not selected_categories:
            selected_categories = deterministic_categories
        else:
            selected_categories = merge_unique(selected_categories, deterministic_categories)[:3]

        preferred_categories = list(infer_preferred_categories(query))
        excluded_categories = infer_excluded_categories(query)
        if preferred_categories:
            selected_categories = merge_unique(preferred_categories, selected_categories)

        # Re-rank categories by explicit domain anchors in query text.
        if selected_categories:
            selected_categories = sorted(
                selected_categories,
                key=lambda cat: (-category_anchor_score(query, cat), cat.lower())
            )

        # If we have anchored categories, keep strong anchor categories only.
        if selected_categories:
            anchor_scores = {cat: category_anchor_score(query, cat) for cat in selected_categories}
            max_anchor = max(anchor_scores.values()) if anchor_scores else 0.0
            if max_anchor > 0.0:
                threshold = max(1.0, max_anchor * 0.08)
                selected_categories = [
                    cat for cat in selected_categories
                    if anchor_scores.get(cat, 0.0) >= threshold
                ]

        # Guardrail: if LLM-selected categories have no anchor evidence,
        # prefer deterministic domain-matched categories.
        if selected_categories:
            best_anchor = max((category_anchor_score(query, cat) for cat in selected_categories), default=0.0)
            if best_anchor <= 0.0 and deterministic_categories:
                selected_categories = deterministic_categories[:3]

        # Remove clearly excluded categories unless the query explicitly anchors to them.
        if selected_categories and excluded_categories:
            selected_categories = [
                cat for cat in selected_categories
                if cat not in excluded_categories or category_anchor_score(query, cat) > 0.0
            ]

        selected_categories = selected_categories[:3]

        category_set = set(selected_categories)
        if category_set:
            stage1_pool = [c for c in all_candidates if (c.category or "").strip() in category_set]
            if not stage1_pool:
                stage1_pool = all_candidates
        else:
            stage1_pool = all_candidates

        # Safety net: include globally strong candidates so routing misses do not hide good matches.
        global_ranked_candidates = sorted(
            ((candidate_relevance_score(query, candidate), candidate) for candidate in all_candidates),
            key=lambda item: (-item[0], item[1].id)
        )
        global_backfill = [candidate for _, candidate in global_ranked_candidates[:15]]
        stage1_by_id = {candidate.id: candidate for candidate in stage1_pool}
        for candidate in global_backfill:
            stage1_by_id[candidate.id] = candidate
        stage1_pool = list(stage1_by_id.values())

        print(f"🌲 Stage-1 categories: {selected_categories if selected_categories else 'ALL'}")
        print(f"📦 Stage-1 pool size: {len(stage1_pool)}")

        # Stage 2: score and shortlist inside selected branches.
        ranked_candidates = sorted(
            ((candidate_relevance_score(query, candidate), candidate) for candidate in stage1_pool),
            key=lambda item: (-item[0], item[1].id)
        )

        overlap_ranked = sorted(
            ((overlap_ratio(query, candidate), candidate) for candidate in stage1_pool),
            key=lambda item: (-item[0], item[1].id)
        )
        anchor_candidate = overlap_ranked[0][1] if overlap_ranked else None
        anchor_overlap = overlap_ranked[0][0] if overlap_ranked else 0.0

        # If the query looks like pasted resume text, category routing is too brittle.
        # In that case, search globally and let the overlap-based shortlist decide.
        if query_looks_like_resume_excerpt(query) and anchor_overlap >= 0.18:
            stage1_pool = [candidate for _, candidate in global_ranked_candidates[:40]]
            stage1_by_id = {candidate.id: candidate for candidate in stage1_pool}
            stage1_pool = list(stage1_by_id.values())
            selected_categories = []

        shortlist_count = min(len(ranked_candidates), max(SHORTLIST_SIZE, limit * 3))
        shortlist = ranked_candidates[:shortlist_count]
        print(f"🤖 Shortlist size: {len(shortlist)}")

        candidate_lookup = {candidate.id: candidate for _, candidate in shortlist}
        if anchor_candidate:
            candidate_lookup[anchor_candidate.id] = anchor_candidate

        start_time = time.time()
        ranked_response = None
        elapsed_pre_rank_ms = (time.time() - start_time) * 1000
        if elapsed_pre_rank_ms < MAX_TOTAL_LATENCY_MS - 1200:
            ranked_response = llm_rank_candidates(query, shortlist)

        if ranked_response and ranked_response.get("candidates"):
            by_id = {candidate.id: candidate for _, candidate in shortlist}
            final_results = []
            seen_ids = set()

            for item in ranked_response.get("candidates", []):
                candidate_id = item.get("candidate_id")
                if candidate_id in seen_ids or candidate_id not in by_id:
                    continue
                seen_ids.add(candidate_id)
                source_candidate = by_id[candidate_id]
                # Use LLM explanation if present, else fallback
                llm_explanation = item.get("explanation")
                if llm_explanation and isinstance(llm_explanation, str) and len(llm_explanation.strip()) > 0:
                    explanation = llm_explanation.strip()
                else:
                    evidence = extract_section_evidence(source_candidate, query)
                    _, explanation, _ = build_candidate_explanation(source_candidate, query, evidence)
                # Matched sections: use LLM if present, else fallback
                llm_sections = item.get("matched_sections")
                if llm_sections and isinstance(llm_sections, list) and llm_sections:
                    matched_sections = llm_sections
                else:
                    evidence = extract_section_evidence(source_candidate, query)
                    matched_sections, _, _ = build_candidate_explanation(source_candidate, query, evidence)
                final_results.append({
                    "candidate_id": source_candidate.id,
                    "name": item.get("name", source_candidate.name),
                    "category": item.get("category", source_candidate.category),
                    "match_score": item.get("match_score", 0),
                    "matched_sections": matched_sections,
                    "explanation": explanation,
                    "file_path": source_candidate.file_path,
                })
                if len(final_results) >= limit:
                    break

            # If user pasted near-verbatim resume text, force include strongest overlap hit.
            if anchor_candidate and anchor_overlap >= 0.45:
                already = {row.get("candidate_id") for row in final_results}
                if anchor_candidate.id not in already:
                    evidence = extract_section_evidence(anchor_candidate, query)
                    matched_sections, explanation, _ = build_candidate_explanation(anchor_candidate, query, evidence)
                    final_results.insert(0, {
                        "candidate_id": anchor_candidate.id,
                        "name": anchor_candidate.name,
                        "category": anchor_candidate.category,
                        "match_score": 99,
                        "matched_sections": matched_sections,
                        "explanation": explanation,
                        "file_path": anchor_candidate.file_path,
                    })
                    final_results = final_results[:limit]
            ranking_method = "llm"
            search_reasoning = build_search_reasoning(
                query=query,
                selected_categories=selected_categories,
                final_results=final_results,
                candidate_lookup=candidate_lookup,
                ranking_method="llm",
                anchor_candidate=anchor_candidate,
                anchor_overlap=anchor_overlap,
            )
        else:
            final_results = heuristic_results(shortlist, limit)
            for row in final_results:
                candidate = candidate_lookup.get(row.get("candidate_id"))
                if candidate:
                    matched_sections, explanation, _ = build_candidate_explanation(candidate, query)
                    row["matched_sections"] = matched_sections
                    row["explanation"] = explanation

            search_reasoning = build_search_reasoning(
                query=query,
                selected_categories=selected_categories,
                final_results=final_results,
                candidate_lookup=candidate_lookup,
                ranking_method="heuristic",
                anchor_candidate=anchor_candidate,
                anchor_overlap=anchor_overlap,
            )
            ranking_method = "heuristic"

        total_time = (time.time() - start_time) * 1000
        result_dict = {
            "candidates": final_results,
            "search_reasoning": search_reasoning,
            "latency_ms": total_time,
            "ranking_method": ranking_method,
            "shortlist_size": len(shortlist),
        }

        search_cache[cache_key] = (result_dict, time.time())
        print(f"\n⏱️  TOTAL: {total_time:.0f}ms | 📊 Results: {len(final_results)} | {ranking_method.upper()} | 💾 Cached\n")
        return result_dict

    except Exception as e:
        print(f"❌ Error: {e}")
        return {"candidates": [], "search_reasoning": f"Error: {str(e)}"}


def analyze_single_resume(pdf_path: str, question: str) -> dict:
    """Analyze a single resume using its PageIndex tree."""
    try:
        if not groq_client:
            return {
                "answer": "Groq not configured",
                "relevant_sections": [],
                "recommendation": "Error",
                "reasoning": "API not configured"
            }

        print("\n📋 Analyzing resume...")
        _, tree_data = build_pageindex_tree_from_pdf(pdf_path, Path(pdf_path).stem)
        compressed_tree = compress_tree(tree_data)
        tree_str = json.dumps(compressed_tree, indent=2)

        prompt = SINGLE_RESUME_PROMPT.format(tree=tree_str, question=question)

        print("   💭 Analyzing...")
        last_error = None
        for model in GROQ_MODELS:
            try:
                response = groq_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "Return only valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=1000,
                    response_format={"type": "json_object"},
                )
                result = json.loads(response.choices[0].message.content)
                print("   ✅ Complete")
                return result
            except Exception as exc:
                last_error = exc

        raise RuntimeError(str(last_error))

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return {
            "answer": f"Error: {str(e)}",
            "relevant_sections": [],
            "recommendation": "Error",
            "reasoning": str(e)
        }