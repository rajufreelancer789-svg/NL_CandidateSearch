#!/usr/bin/env python3
"""
Natural Language Candidate Search System
Streamlit Frontend - Production Grade
Team: QuantumSprouts
"""

import streamlit as st
import sys
import os
import json
import time
import base64
import re
from pathlib import Path
from datetime import datetime

# Add backend to path
current_dir = Path(__file__).parent
backend_dir = current_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from backend.database import SessionLocal
from backend.models import Candidate
from backend.search import search_candidates, analyze_single_resume, extract_jd_from_image
from backend.ingest import ingest_resume

# Page config
st.set_page_config(
    page_title="NLCS — Candidate Intelligence",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Premium CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;1,9..40,300&family=DM+Serif+Display:ital@0;1&display=swap');

/* ── Reset & Base ── */
*, *::before, *::after { box-sizing: border-box; }

html, body, [class*="css"], .stApp {
    font-family: 'DM Sans', sans-serif !important;
    background: #0B0F1A !important;
    color: #E8E6F0 !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0F1425 !important;
    border-right: 1px solid rgba(255,255,255,0.06) !important;
}
[data-testid="stSidebar"] .stMarkdown h2,
[data-testid="stSidebar"] .stMarkdown h3 {
    color: #C8B9FF !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    letter-spacing: 0.04em !important;
    font-size: 0.78rem !important;
    text-transform: uppercase !important;
}
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] label {
    color: #9B94B3 !important;
    font-size: 0.88rem !important;
}
[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.07) !important;
}

/* ── Metric Cards ── */
[data-testid="stMetric"] {
    background: linear-gradient(145deg, #161B2E, #111629) !important;
    border: 1px solid rgba(200,185,255,0.12) !important;
    border-radius: 12px !important;
    padding: 1rem 1.2rem !important;
    position: relative;
    overflow: hidden;
}
[data-testid="stMetric"]::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #7C5CFC, #C8B9FF, #7C5CFC);
    opacity: 0.7;
}
[data-testid="stMetricLabel"] {
    color: #9B94B3 !important;
    font-size: 0.75rem !important;
    font-weight: 400 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
}
[data-testid="stMetricValue"] {
    color: #E8E6F0 !important;
    font-size: 1.6rem !important;
    font-weight: 500 !important;
    font-family: 'DM Serif Display', serif !important;
}
[data-testid="stMetricDelta"] {
    color: #7FFFB3 !important;
    font-size: 0.78rem !important;
}

/* ── Header Block ── */
.nlcs-header {
    background: linear-gradient(135deg, #161B2E 0%, #1A1040 50%, #0D1B38 100%);
    border: 1px solid rgba(124,92,252,0.25);
    border-radius: 16px;
    padding: 2.4rem 2.8rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}
.nlcs-header::before {
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 240px; height: 240px;
    background: radial-gradient(circle, rgba(124,92,252,0.15) 0%, transparent 70%);
    pointer-events: none;
}
.nlcs-header::after {
    content: '';
    position: absolute;
    bottom: -40px; left: 30%;
    width: 180px; height: 180px;
    background: radial-gradient(circle, rgba(75,175,255,0.08) 0%, transparent 70%);
    pointer-events: none;
}
.nlcs-header-label {
    font-size: 0.72rem;
    font-weight: 500;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #7C5CFC;
    margin-bottom: 0.5rem;
}
.nlcs-header h1 {
    font-family: 'DM Serif Display', serif !important;
    font-size: 2.4rem !important;
    font-weight: 400 !important;
    color: #F0EEF8 !important;
    margin: 0 0 0.5rem 0 !important;
    letter-spacing: -0.01em;
    line-height: 1.2;
}
.nlcs-header-sub {
    font-size: 0.92rem;
    color: #9B94B3;
    letter-spacing: 0.02em;
}
.nlcs-header-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(124,92,252,0.15);
    border: 1px solid rgba(124,92,252,0.3);
    color: #C8B9FF;
    font-size: 0.72rem;
    font-weight: 500;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 4px 12px;
    border-radius: 20px;
    margin-top: 1rem;
}

/* ── Candidate Cards ── */
.cand-card {
    background: linear-gradient(145deg, #141926, #111523);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s ease;
}
.cand-card:hover {
    border-color: rgba(124,92,252,0.3);
}
.cand-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 3px; height: 100%;
    background: linear-gradient(180deg, #7C5CFC, #4BAFFF);
    border-radius: 3px 0 0 3px;
}
.cand-rank {
    font-family: 'DM Serif Display', serif;
    font-size: 2.4rem;
    color: rgba(124,92,252,0.25);
    line-height: 1;
    position: absolute;
    right: 1.6rem;
    top: 1.2rem;
}
.cand-name {
    font-family: 'DM Serif Display', serif;
    font-size: 1.25rem;
    color: #F0EEF8;
    margin: 0 0 2px 0;
}
.cand-meta {
    font-size: 0.78rem;
    color: #6B637F;
    letter-spacing: 0.04em;
}
.cand-meta span {
    color: #9B94B3;
    margin-right: 12px;
}
.score-ring {
    width: 54px; height: 54px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-weight: 500;
    font-size: 0.95rem;
    flex-shrink: 0;
}
.score-ring-high {
    background: rgba(127,255,179,0.1);
    border: 2px solid rgba(127,255,179,0.5);
    color: #7FFFB3;
}
.score-ring-mid {
    background: rgba(255,185,80,0.1);
    border: 2px solid rgba(255,185,80,0.45);
    color: #FFB950;
}
.score-ring-low {
    background: rgba(255,100,100,0.1);
    border: 2px solid rgba(255,100,100,0.4);
    color: #FF7070;
}
.match-label {
    font-size: 0.7rem;
    font-weight: 500;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #7C5CFC;
    margin-bottom: 4px;
}
.match-text {
    font-size: 0.88rem;
    color: #ABA4C0;
    line-height: 1.55;
}
.section-pill {
    display: inline-block;
    background: rgba(124,92,252,0.12);
    border: 1px solid rgba(124,92,252,0.25);
    color: #C8B9FF;
    font-size: 0.7rem;
    font-weight: 500;
    letter-spacing: 0.05em;
    padding: 3px 10px;
    border-radius: 20px;
    margin: 3px 3px 0 0;
}

/* ── Section Headers ── */
.section-header {
    font-family: 'DM Serif Display', serif;
    font-size: 1.5rem;
    color: #F0EEF8;
    margin: 0 0 0.3rem 0;
    font-weight: 400;
}
.section-sub {
    font-size: 0.88rem;
    color: #6B637F;
    margin-bottom: 1.5rem;
}

/* ── Input Fields ── */
.stTextInput > div > div > input,
.stTextArea textarea {
    background: #131828 !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 10px !important;
    color: #E8E6F0 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.92rem !important;
    padding: 0.7rem 1rem !important;
    transition: border-color 0.2s ease !important;
}
.stTextInput > div > div > input:focus,
.stTextArea textarea:focus {
    border-color: rgba(124,92,252,0.55) !important;
    box-shadow: 0 0 0 3px rgba(124,92,252,0.1) !important;
}
.stTextInput > div > div > input::placeholder {
    color: #4A4360 !important;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #7C5CFC, #5B3FD4) !important;
    color: #F0EEF8 !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.04em !important;
    padding: 0.55rem 1.4rem !important;
    transition: opacity 0.15s ease, transform 0.1s ease !important;
}
.stButton > button:hover {
    opacity: 0.88 !important;
    transform: translateY(-1px) !important;
}
.stButton > button:active {
    transform: translateY(0) !important;
}

/* ── Radio Buttons ── */
.stRadio > div {
    gap: 0.5rem !important;
}
.stRadio label {
    background: #131828 !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 8px !important;
    padding: 0.5rem 1rem !important;
    color: #9B94B3 !important;
    font-size: 0.88rem !important;
    cursor: pointer !important;
    transition: all 0.15s ease !important;
}
.stRadio label:has(input:checked) {
    border-color: rgba(124,92,252,0.5) !important;
    background: rgba(124,92,252,0.1) !important;
    color: #C8B9FF !important;
}

/* ── File Uploader ── */
[data-testid="stFileUploader"] {
    background: #131828 !important;
    border: 1px dashed rgba(124,92,252,0.35) !important;
    border-radius: 12px !important;
    padding: 1rem !important;
}
[data-testid="stFileUploader"] label {
    color: #9B94B3 !important;
    font-size: 0.88rem !important;
}

/* ── Expander ── */
.streamlit-expanderHeader {
    background: #131828 !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 10px !important;
    color: #9B94B3 !important;
    font-size: 0.88rem !important;
}
.streamlit-expanderContent {
    background: #0F1322 !important;
    border: 1px solid rgba(255,255,255,0.05) !important;
    border-top: none !important;
    border-radius: 0 0 10px 10px !important;
    color: #ABA4C0 !important;
    font-size: 0.88rem !important;
    line-height: 1.65 !important;
}

/* ── Alerts / Info boxes ── */
.stAlert {
    border-radius: 10px !important;
    border-left-width: 3px !important;
    font-size: 0.88rem !important;
}
.stSuccess {
    background: rgba(127,255,179,0.07) !important;
    border-color: #7FFFB3 !important;
    color: #7FFFB3 !important;
}
.stWarning {
    background: rgba(255,185,80,0.07) !important;
    border-color: #FFB950 !important;
    color: #FFB950 !important;
}
.stError {
    background: rgba(255,100,100,0.07) !important;
    border-color: #FF7070 !important;
    color: #FF7070 !important;
}
.stInfo {
    background: rgba(75,175,255,0.07) !important;
    border-color: #4BAFFF !important;
    color: #9DD6FF !important;
}

/* ── Spinner ── */
.stSpinner > div {
    border-top-color: #7C5CFC !important;
}

/* ── Divider ── */
hr {
    border-color: rgba(255,255,255,0.06) !important;
}

/* ── Download Button ── */
.stDownloadButton > button {
    background: transparent !important;
    border: 1px solid rgba(124,92,252,0.4) !important;
    color: #C8B9FF !important;
    border-radius: 8px !important;
    font-size: 0.82rem !important;
    font-weight: 400 !important;
    letter-spacing: 0.03em !important;
}
.stDownloadButton > button:hover {
    background: rgba(124,92,252,0.12) !important;
    border-color: rgba(124,92,252,0.65) !important;
}

/* ── Caption ── */
.stCaption {
    color: #4A4360 !important;
    font-size: 0.76rem !important;
}

/* ── Select box / number input ── */
.stSelectbox select, .stNumberInput input {
    background: #131828 !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 8px !important;
    color: #E8E6F0 !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* ── Container borders ── */
[data-testid="stVerticalBlock"] > [data-testid="stVerticalBlockBorderWrapper"] > div {
    background: #141926 !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 14px !important;
}

/* ── Results count bar ── */
.results-bar {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 0.9rem 1.4rem;
    background: #0F1322;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px;
    margin-bottom: 1.2rem;
    font-size: 0.82rem;
    color: #6B637F;
}
.results-bar strong { color: #C8B9FF; font-weight: 500; }
.results-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: #7C5CFC;
    flex-shrink: 0;
}

/* ── Footer ── */
.nlcs-footer {
    display: flex;
    gap: 24px;
    align-items: center;
    font-size: 0.75rem;
    color: #3A344D;
    letter-spacing: 0.04em;
    padding-top: 0.5rem;
}
.nlcs-footer a { color: #5B4FA0; text-decoration: none; }
</style>
""", unsafe_allow_html=True)

# ── Session State ────────────────────────────────────────────────────────────
if 'search_results' not in st.session_state:
    st.session_state.search_results = None
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""
if 'search_latency' not in st.session_state:
    st.session_state.search_latency = 0
if 'resume_preview_path' not in st.session_state:
    st.session_state.resume_preview_path = None
if 'resume_preview_name' not in st.session_state:
    st.session_state.resume_preview_name = ""
if 'extracted_jd' not in st.session_state:
    st.session_state.extracted_jd = ""


def resolve_resume_path(raw_path: str) -> Path | None:
    if not raw_path:
        return None
    path = Path(raw_path)
    candidates = [
        path,
        current_dir / raw_path,
        (current_dir / "uploads" / path.name),
        (current_dir.parent / raw_path),
    ]
    for candidate in candidates:
        try:
            if candidate.exists() and candidate.is_file():
                return candidate.resolve()
        except Exception:
            continue
    return None


def render_pdf_preview(pdf_path: Path, height: int = 720):
    try:
        pdf_bytes = pdf_path.read_bytes()
        encoded = base64.b64encode(pdf_bytes).decode("utf-8")
        iframe = f"""
            <div style="border-radius:12px;overflow:hidden;border:1px solid rgba(124,92,252,0.2);">
                <iframe src="data:application/pdf;base64,{encoded}"
                    width="100%" height="{height}"
                    style="display:block;border:none;"
                    type="application/pdf">
                </iframe>
            </div>
        """
        st.markdown(iframe, unsafe_allow_html=True)
    except Exception as exc:
        st.error(f"Unable to preview PDF: {exc}")


# ── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="nlcs-header">
    <div class="nlcs-header-label">◈ AI-Powered Talent Intelligence</div>
    <h1>Natural Language<br>Candidate Search</h1>
    <div class="nlcs-header-sub">Reasoning over 74 resumes — no vectors, pure intelligence</div>
    <div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:1rem;">
        <span class="nlcs-header-pill">⚡ Groq LLM</span>
        <span class="nlcs-header-pill">🌳 PageIndex</span>
        <span class="nlcs-header-pill">🗄 MySQL</span>
        <span class="nlcs-header-pill">🏗 QuantumSprouts</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ SYSTEM")

    db = SessionLocal()
    candidate_count = db.query(Candidate).count()
    db.close()

    st.metric("Candidates Indexed", candidate_count)

    st.divider()
    st.markdown("### 📥 INGEST RESUME")
    db_upload = st.file_uploader(
        "Upload PDF to Database",
        type=["pdf"],
        key="db_resume_uploader",
        help="Runs PageIndex ingestion and adds to the searchable candidate pool."
    )

    if db_upload is not None:
        if st.button("➕ Add to Index", key="ingest_resume_btn", use_container_width=True):
            db = SessionLocal()
            saved_path = None
            try:
                uploads_dir = current_dir / "uploads"
                uploads_dir.mkdir(parents=True, exist_ok=True)

                original_name = Path(db_upload.name).stem
                safe_stem = re.sub(r"[^A-Za-z0-9_-]+", "_", original_name).strip("_") or "resume"
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                target_name = f"{safe_stem}_{timestamp}.pdf"
                saved_path = uploads_dir / target_name

                with open(saved_path, "wb") as f:
                    f.write(db_upload.getbuffer())

                candidate_id = ingest_resume(str(saved_path), db)
                candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()

                if candidate:
                    st.success(
                        f"Indexed · ID {candidate.id} · {candidate.name} · {candidate.category}"
                    )
                else:
                    st.success(f"Indexed · ID: {candidate_id}")

                st.caption("Resume is now part of the searchable pool.")
                st.rerun()
            except Exception as exc:
                st.error(f"Ingestion failed: {exc}")
                if saved_path and saved_path.exists():
                    try:
                        saved_path.unlink()
                    except Exception:
                        pass
            finally:
                db.close()

    st.divider()
    st.markdown("###  MODE")
    mode = st.radio(
        "",
        ["🔍 Database Search", " Single Resume Analysis"],
        help="Switch between database-wide search and individual resume analysis",
        label_visibility="collapsed"
    )

    st.divider()
    with st.expander("ℹ️ How it works"):
        st.markdown("""
**No vector embeddings.**

1. Type a plain-English query or upload a job posting screenshot
2. The system reasons over 74 resume trees via PageIndex
3. Returns the top 5 candidates with scored explanations

Built for precision, not keyword matching.
        """)


# ── Main ─────────────────────────────────────────────────────────────────────
if mode == " Database Search":

    st.markdown('<p class="section-header">Database Search</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-sub">Query across all 74 indexed candidates using natural language.</p>', unsafe_allow_html=True)

    input_mode = st.radio(
        "Input type",
        [" Enter JD Text", " Upload Posting Screenshot"],
        horizontal=True,
        help="Paste a job description or upload a screenshot of a job posting."
    )

    effective_query = ""

    if input_mode == " Enter JD Text":
        col1, col2 = st.columns([5, 1])
        with col1:
            query = st.text_input(
                "Search query",
                placeholder="e.g. Python developer with 4+ years ML experience, strong system design...",
                key="search_input",
                label_visibility="collapsed"
            )
        with col2:
            search_button = st.button("Search ›", key="search_btn", use_container_width=True)

        if search_button:
            effective_query = query.strip()

    else:
        screenshot_file = st.file_uploader(
            "Upload job posting screenshot",
            type=["png", "jpg", "jpeg", "webp"],
            key="jd_screenshot",
            help="The system extracts JD text from the image and runs candidate matching."
        )

        if screenshot_file is not None:
            st.image(screenshot_file, caption="Uploaded posting", use_container_width=True)

            if st.button(" Extract JD & Search", key="search_from_screenshot", use_container_width=True):
                with st.spinner("Extracting JD from screenshot..."):
                    extract_result = extract_jd_from_image(
                        screenshot_file.getvalue(),
                        screenshot_file.type or "image/png"
                    )
                    jd_text = (extract_result.get("jd_text") or "").strip()
                    st.session_state.extracted_jd = jd_text

                    if jd_text:
                        st.success("JD extracted — running candidate search...")
                        effective_query = jd_text
                    else:
                        st.error(extract_result.get("reasoning", "Could not extract JD from screenshot."))

        if st.session_state.extracted_jd:
            st.markdown("**Extracted JD**")
            st.text_area("", st.session_state.extracted_jd, height=160, key="extracted_jd_view")

    # ── Run search ──
    if effective_query:
        with st.spinner("Reasoning over candidates..."):
            db = SessionLocal()
            try:
                start_time = time.time()
                results = search_candidates(effective_query, limit=5, db_session=db)
                latency = (time.time() - start_time) * 1000
                st.session_state.search_results = results
                st.session_state.search_query = effective_query
                st.session_state.search_latency = latency
            except Exception as e:
                st.error(f"Search failed: {str(e)}")
            finally:
                db.close()

    # ── Results ──
    if st.session_state.search_results:
        candidates = st.session_state.search_results.get('candidates', [])
        reasoning = st.session_state.search_results.get('search_reasoning', '')

        st.divider()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Candidates Matched", len(candidates))
        with col2:
            latency_val = st.session_state.search_latency
            delta_str = "✓ Fast" if latency_val < 500 else "Optimizing"
            st.metric("Response Time", f"{latency_val:.0f} ms", delta=delta_str)
        with col3:
            q_preview = st.session_state.search_query[:28]
            st.metric("Query", f'"{q_preview}…"')

        st.divider()

        if candidates:
            # Results summary bar
            st.markdown(
                f'<div class="results-bar"><span class="results-dot"></span>'
                f'Showing <strong>{len(candidates)}</strong> best matches for your query</div>',
                unsafe_allow_html=True
            )

            for i, candidate in enumerate(candidates, 1):
                score = candidate.get('match_score', 0)
                if score >= 80:
                    ring_class = "score-ring-high"
                elif score >= 60:
                    ring_class = "score-ring-mid"
                else:
                    ring_class = "score-ring-low"

                matched_sections = candidate.get('matched_sections', [])
                pills_html = "".join(
                    f'<span class="section-pill">{s}</span>' for s in matched_sections
                )

                explanation = candidate.get('explanation', 'No explanation available.')

                st.markdown(f"""
<div class="cand-card">
    <span class="cand-rank">#{i:02d}</span>
    <div style="display:flex;align-items:flex-start;gap:14px;">
        <div class="score-ring {ring_class}">{score}%</div>
        <div style="flex:1;min-width:0;">
            <p class="cand-name">{candidate.get('name', 'Unknown')}</p>
            <div class="cand-meta">
                <span>ID {candidate.get('candidate_id')}</span>
                <span>{candidate.get('category', 'Unknown')}</span>
            </div>
        </div>
    </div>
    <div style="margin-top:1rem;">
        <div class="match-label">Match reasoning</div>
        <div class="match-text">{explanation}</div>
    </div>
    {f'<div style="margin-top:0.75rem;">{pills_html}</div>' if pills_html else ''}
</div>
""", unsafe_allow_html=True)

                # View Resume button (outside the HTML card so it stays functional)
                btn_col, _ = st.columns([1, 5])
                with btn_col:
                    if st.button("View Resume", key=f"resume_{i}"):
                        resolved = resolve_resume_path(candidate.get("file_path", ""))
                        if resolved:
                            st.session_state.resume_preview_path = str(resolved)
                            st.session_state.resume_preview_name = candidate.get('name', 'Unknown')
                        else:
                            st.warning("Resume file path not found for this candidate.")

            # ── Reasoning expander ──
            with st.expander(" Search reasoning"):
                st.markdown(
                    f'<div style="font-size:0.88rem;color:#ABA4C0;line-height:1.7;">{reasoning}</div>',
                    unsafe_allow_html=True
                )

            # ── PDF Preview ──
            if st.session_state.resume_preview_path:
                st.divider()
                h_col, c_col = st.columns([5, 1])
                with h_col:
                    st.markdown(
                        f'<p class="section-header" style="font-size:1.1rem;"> {st.session_state.resume_preview_name}</p>',
                        unsafe_allow_html=True
                    )
                with c_col:
                    if st.button("✕ Close", key="close_resume_preview"):
                        st.session_state.resume_preview_path = None
                        st.session_state.resume_preview_name = ""

                preview_path = Path(st.session_state.resume_preview_path)
                if preview_path.exists():
                    render_pdf_preview(preview_path)
                    with open(preview_path, "rb") as pdf_file:
                        st.download_button(
                            "⬇ Download PDF",
                            data=pdf_file,
                            file_name=preview_path.name,
                            mime="application/pdf",
                            key="download_resume_preview"
                        )
                else:
                    st.warning("Preview file no longer exists on disk.")
        else:
            st.warning("No candidates matched your query — try rephrasing or broadening the search.")


# ── Single Resume Analysis ─────────────────────────────────────────────────
else:
    st.markdown('<p class="section-header">Single Resume Analysis</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-sub">Upload any resume PDF and ask a specific question about it.</p>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        uploaded_file = st.file_uploader(
            "Resume PDF",
            type="pdf",
            help="Select a PDF resume to analyze"
        )
    with col2:
        question = st.text_input(
            "Your question",
            placeholder="e.g. Is this person ready for a Staff Engineer role?",
            key="analysis_question"
        )

    if uploaded_file and question:
        if st.button("Analyze Resume ›", use_container_width=True):
            temp_path = Path(__file__).parent / "temp_upload.pdf"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            with st.spinner("Analyzing resume..."):
                try:
                    result = analyze_single_resume(str(temp_path), question)

                    st.divider()
                    col1, col2 = st.columns(2)

                    with col1:
                        recommendation = result.get('recommendation', 'No recommendation')
                        if "Strong Yes" in recommendation:
                            st.success(f" {recommendation}")
                        elif "Yes" in recommendation:
                            st.info(f"✓ {recommendation}")
                        elif "Maybe" in recommendation:
                            st.warning(f" {recommendation}")
                        else:
                            st.error(f"✕ {recommendation}")

                    with col2:
                        sections = result.get('relevant_sections', [])
                        st.metric("Sections Reviewed", len(sections))

                    st.markdown("**Analysis**")
                    st.markdown(
                        f'<div style="font-size:0.92rem;color:#C4BDDA;line-height:1.7;background:#131828;border:1px solid rgba(255,255,255,0.07);border-radius:10px;padding:1.2rem 1.4rem;">'
                        f'{result.get("answer", "No answer available.")}</div>',
                        unsafe_allow_html=True
                    )

                    with st.expander(" Detailed reasoning"):
                        st.markdown(result.get('reasoning', 'No reasoning available'))

                    if sections:
                        st.markdown("**Sections reviewed**")
                        pills = "".join(
                            f'<span class="section-pill">{s}</span>' for s in sections
                        )
                        st.markdown(f'<div style="margin-top:4px;">{pills}</div>', unsafe_allow_html=True)

                    temp_path.unlink()

                except Exception as e:
                    st.error(f"Analysis failed: {str(e)}")
                    if temp_path.exists():
                        temp_path.unlink()


# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    f'<div class="nlcs-footer">'
    f'<span>◈ NLCS v1.0</span>'
    f'<span>·</span>'
    f'<span>QuantumSprouts</span>'
    f'<span>·</span>'
    f'<span>{datetime.now().strftime("%Y-%m-%d %H:%M")}</span>'
    f'</div>',
    unsafe_allow_html=True
)