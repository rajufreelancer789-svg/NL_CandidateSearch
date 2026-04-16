# Resume ingestion pipeline
# Extract PDF → Build tree → Compress → Store in MySQL

import fitz  # PyMuPDF
import json
import time
from pathlib import Path
import os
import sys
from dotenv import load_dotenv
from sqlalchemy.orm import Session

# Handle import paths for both direct execution and module import
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
    from pageindex import PageIndexClient
except ImportError:
    try:
        from pageindex import Client as PageIndexClient
    except ImportError:
        print("⚠️ PageIndex not installed. Install with: pip install pageindex")
        PageIndexClient = None

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY")
if PageIndexClient and PAGEINDEX_API_KEY:
    pageindex_client = PageIndexClient(api_key=PAGEINDEX_API_KEY)
else:
    pageindex_client = None


def build_pageindex_tree_from_pdf(pdf_path: str, candidate_name: str, max_attempts: int = 20, sleep_seconds: int = 3):
    """Build a PageIndex tree directly from a PDF file."""
    if not pageindex_client:
        raise RuntimeError("PageIndex client is not configured")

    print(f"  🌳 Building PageIndex tree for {candidate_name}...")
    response = pageindex_client.submit_document(pdf_path)
    doc_id = response.get("doc_id") or response.get("id")
    if not doc_id:
        raise RuntimeError("PageIndex did not return a document ID")

    print(f"    Document ID: {doc_id}")

    attempt = 0
    while attempt < max_attempts:
        status_response = pageindex_client.get_document(doc_id)
        status = status_response.get("status")

        if status == "completed":
            print("    ✅ Tree built successfully")
            tree_response = pageindex_client.get_tree(doc_id, node_summary=True)
            # Keep full raw tree response for traceability.
            return doc_id, tree_response

        if status == "failed":
            raise RuntimeError(f"PageIndex processing failed for {pdf_path}")

        print(f"    ⏳ Status: {status} (attempt {attempt + 1}/{max_attempts})")
        time.sleep(sleep_seconds)
        attempt += 1

    raise TimeoutError(f"PageIndex tree build timed out for {pdf_path}")

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from PDF using PyMuPDF
    
    Args:
        pdf_path: Path to PDF file
    
    Returns:
        Extracted text string
    """
    try:
        doc = fitz.open(pdf_path)
        pages = []
        for page in doc:
            pages.append(page.get_text("text"))
        doc.close()

        # Preserve line structure for reliable name extraction.
        raw_text = "\n".join(pages)
        normalized_lines = []
        for line in raw_text.splitlines():
            normalized_lines.append(" ".join(line.split()))
        text = "\n".join(normalized_lines).strip()
        return text
    except Exception as e:
        print(f"❌ Error extracting text from {pdf_path}: {e}")
        raise

def extract_candidate_name(text: str) -> str:
    """
    Extract candidate name from resume text
    Usually first non-empty line
    
    Args:
        text: Resume text
    
    Returns:
        Candidate name
    """
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if not line or len(line) <= 2 or len(line) > 120:
            continue
        if line.lower() in {"summary", "experience", "skills", "education", "projects", "profile", "objective"}:
            continue
        # Skip obvious section-like lines.
        if len(line.split()) > 10:
            continue
        return line[:100]
    return "Unknown"


def build_local_tree_from_text(text: str, candidate_name: str) -> list:
    """Build a lightweight local tree when PageIndex is unavailable or rate-limited."""
    normalized = text or ""
    lines = [ln.strip() for ln in normalized.splitlines() if ln.strip()]

    section_titles = [
        "summary", "professional summary", "profile", "skills", "technical skills",
        "experience", "work experience", "employment", "projects", "education",
        "certifications", "accomplishments", "achievements"
    ]

    tree = []
    tree.append(
        {
            "node_id": "0000",
            "title": candidate_name or "Candidate",
            "summary": f"# {candidate_name or 'Candidate'}",
            "text": f"# {candidate_name or 'Candidate'}",
        }
    )

    current_title = "Summary"
    buckets = {current_title: []}

    def as_section_title(line: str) -> str | None:
        low = line.lower().strip(" :.-")
        if low in section_titles:
            return line.strip(" :.-").title()
        return None

    for line in lines:
        detected = as_section_title(line)
        if detected:
            current_title = detected
            buckets.setdefault(current_title, [])
            continue
        buckets.setdefault(current_title, []).append(line)

    node_idx = 1
    for title, content_lines in buckets.items():
        if not content_lines:
            continue
        joined = " ".join(content_lines)
        tree.append(
            {
                "node_id": f"{node_idx:04d}",
                "title": title[:100],
                "summary": joined[:400],
                "text": joined,
            }
        )
        node_idx += 1

    return tree


def infer_category_from_text(text: str) -> str:
    """Infer a resume category from extracted text when the PDF path doesn't reveal it."""
    normalized = text.lower()

    category_rules = [
        ("Information Technology", [
            "python", "java", "c#", "dotnet", ".net", "devops", "docker", "kubernetes", "aws",
            "azure", "react", "angular", "node", "django", "spring", "software", "developer",
            "programmer", "qa", "tester", "automation", "full stack", "backend", "frontend",
            "machine learning", "data science", "sql", "api", "web technologies", "html", "css"
        ]),
        ("Hr", ["human resources", "recruitment", "talent acquisition", "benefits", "payroll", "employee relations", "hr"]),
        ("Banking", ["investment banking", "banking", "m&a", "m and a", "equity", "analyst", "financial modeling", "valuation", "finance research"]),
        ("Finance", ["finance", "financial analysis", "budgeting", "forecast", "accounts", "audit", "tax", "treasury"]),
        ("Healthcare", ["healthcare", "hospital", "clinical", "medical", "nurse", "patient", "pharmacy"]),
        ("Agriculture", ["agriculture", "farm", "farming", "ffa", "crop", "soil", "harvest"]),
        ("Engineering", ["engineering", "engineer", "mechanical", "electrical", "civil", "production", "manufacturing"]),
        ("Sales", ["sales", "business development", "account manager", "client relationship", "revenue", "quota"]),
        ("Consultant", ["consultant", "consulting", "advisory", "strategy"]),
        ("Education", ["teacher", "teaching", "instructor", "classroom", "curriculum", "education", "school", "faculty"]),
    ]

    scored = []
    for category, keywords in category_rules:
        score = 0
        for keyword in keywords:
            if keyword in normalized:
                score += 1
        if score > 0:
            scored.append((score, category))

    if scored:
        scored.sort(key=lambda item: (-item[0], item[1]))
        return scored[0][1]

    return "Uncategorized"

def extract_category_from_path(pdf_path: str) -> str:
    """
    Extract category from PDF path
    Expected format: .../CATEGORY/file.pdf
    
    Args:
        pdf_path: Path to PDF file
    
    Returns:
        Category name
    """
    try:
        path_obj = Path(pdf_path)
        parent_name = path_obj.parent.name
        file_stem = path_obj.stem

        known_categories = {
            "ACCOUNTANT", "ADVOCATE", "AGRICULTURE", "APPAREL", "ARTS", "AUTOMOBILE", "AVIATION",
            "BANKING", "BPO", "BUSINESS-DEVELOPMENT", "CHEF", "CONSTRUCTION", "CONSULTANT", "DESIGNER",
            "DIGITAL-MEDIA", "ENGINEERING", "FINANCE", "FITNESS", "HEALTHCARE", "HR",
            "INFORMATION-TECHNOLOGY", "PUBLIC-RELATIONS", "SALES", "TEACHER"
        }

        # 1) Kaggle-style parent category folder
        if parent_name.upper() in known_categories:
            return parent_name.replace("-", " ").title()

        # 2) Prefixed filename pattern e.g. BANKING_123456.pdf
        if "_" in file_stem:
            prefix = file_stem.split("_", 1)[0].upper()
            if prefix in known_categories:
                return prefix.replace("-", " ").title()

        # 3) Avoid accidentally using generic workspace folder names like NLP.
        return "Uncategorized"
    except:
        return "Uncategorized"

def build_tree(text: str, candidate_name: str) -> list:
    """
    Build document tree using PageIndex
    Polls until completion and returns tree structure
    
    Args:
        text: Resume text
        candidate_name: Name of candidate
    
    Returns:
        List of tree nodes
    """
    try:
        if not pageindex_client:
            print(f"  ⚠️  PageIndex not configured. Returning empty tree.")
            return []
            
        print(f"  🌳 Building tree for {candidate_name}...")
        
        # Submit document to PageIndex
        response = pageindex_client.documents.create(
            name=candidate_name,
            content=text[:10000]  # Limit to first 10k chars for cost
        )
        
        doc_id = response.get("id")
        print(f"    Document ID: {doc_id}")
        
        # Poll for completion
        max_attempts = 20
        attempt = 0
        while attempt < max_attempts:
            status_response = pageindex_client.documents.get(doc_id)
            status = status_response.get("status")
            
            if status == "completed":
                print(f"    ✅ Tree built successfully")
                # Return tree as list
                tree = status_response.get("tree", [])
                return tree if isinstance(tree, list) else [tree]
            
            print(f"    ⏳ Status: {status} (attempt {attempt + 1}/{max_attempts})")
            time.sleep(3)
            attempt += 1
        
        print(f"    ⚠️  Tree building timeout")
        return []
    except Exception as e:
        print(f"  ❌ Error building tree: {e}")
        return []

def compress_tree(full_tree: list) -> list:
    """
    Compress tree to only keep essential info for search
    Keeps: node_id, title, summary (150 chars max)
    
    Args:
        full_tree: Full PageIndex tree
    
    Returns:
        Compressed tree list
    """
    compressed = []
    
    def walk_tree(node):
        """Recursively walk and compress tree nodes"""
        if isinstance(node, dict):
            # Handle PageIndex raw wrapper format: {doc_id, status, result:[...]}
            if "result" in node and isinstance(node.get("result"), list):
                walk_tree(node.get("result"))
                return

            compressed_node = {
                "node_id": str(node.get("node_id", "")),
                "title": str(node.get("title", ""))[:100],
                "summary": str(node.get("summary", node.get("text", "")))[:150]
            }
            # Add only real tree nodes (skip metadata-only dicts)
            if compressed_node["node_id"] or compressed_node["title"] or compressed_node["summary"]:
                compressed.append(compressed_node)
            
            # Walk children
            children = node.get("children", node.get("nodes", node.get("tree", [])))
            if isinstance(children, list):
                for child in children:
                    walk_tree(child)
        elif isinstance(node, list):
            for item in node:
                walk_tree(item)
    
    walk_tree(full_tree)
    return compressed

def ingest_resume(pdf_path: str, db_session: Session) -> int:
    """
    Main ingestion function
    Extract → Build tree → Compress → Store in DB
    
    Args:
        pdf_path: Path to resume PDF
        db_session: SQLAlchemy session
    
    Returns:
        Candidate ID
    """
    try:
        print(f"\n📄 Ingesting: {Path(pdf_path).name}")
        
        # Extract text
        text = extract_text_from_pdf(pdf_path)
        if len(text) < 500:
            raise Exception("Not enough text extracted (< 500 chars)")
        
        # Extract metadata
        name = extract_candidate_name(text)
        category = extract_category_from_path(pdf_path)
        if category == "Uncategorized":
            category = infer_category_from_text(text)
        
        print(f"  👤 Name: {name}")
        print(f"  🏷️  Category: {category}")
        
        # Build tree using PageIndex directly from the PDF.
        # If PageIndex is rate-limited/unavailable, fall back to a local tree
        # so the resume still becomes searchable immediately.
        doc_id = ""
        tree = []
        if pageindex_client:
            try:
                doc_id, tree = build_pageindex_tree_from_pdf(pdf_path, name)
            except Exception as pageindex_exc:
                print(f"  ⚠️  PageIndex unavailable for this upload ({pageindex_exc}). Using local fallback tree.")
                tree = build_local_tree_from_text(text, name)
                doc_id = "local-fallback"
        else:
            print("  ⚠️  PageIndex unavailable; using local fallback tree")
            tree = build_local_tree_from_text(text, name)
            doc_id = "local-fallback"
        
        # Compress tree
        compressed_tree = compress_tree(tree)
        
        # Save to database
        candidate = Candidate(
            name=name,
            category=category,
            file_path=pdf_path,
            doc_id=doc_id,
            tree_json=json.dumps(tree),
            tree_compressed=json.dumps(compressed_tree)
        )
        
        db_session.add(candidate)
        db_session.commit()
        db_session.refresh(candidate)
        
        print(f"  ✅ Saved to DB with ID: {candidate.id}")
        return candidate.id
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        db_session.rollback()
        raise
