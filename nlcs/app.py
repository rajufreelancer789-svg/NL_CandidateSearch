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
    page_title="NLCS - Candidate Search",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional look
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary: #FF6B6B;
        --secondary: #4ECDC4;
        --dark: #2D3436;
        --light: #F8F9FA;
    }
    
    /* Header styling */
    .header-container {
        background: linear-gradient(135deg, #FF6B6B 0%, #4ECDC4 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .header-container h1 {
        margin: 0;
        font-size: 2.5rem;
    }
    
    .header-container p {
        margin: 0.5rem 0 0 0;
        font-size: 1rem;
        opacity: 0.95;
    }
    
    /* Card styling */
    .candidate-card {
        background: white;
        border-left: 4px solid #FF6B6B;
        padding: 1.5rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .score-badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.9rem;
    }
    
    .score-high {
        background: #E8F5E9;
        color: #2E7D32;
    }
    
    .score-medium {
        background: #FFF3E0;
        color: #E65100;
    }
    
    .score-low {
        background: #FFEBEE;
        color: #C62828;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
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
    """Resolve stored resume path to an existing local file."""
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


def render_pdf_preview(pdf_path: Path, height: int = 700):
    """Render a PDF inside Streamlit as an embedded popup-style preview."""
    try:
        pdf_bytes = pdf_path.read_bytes()
        encoded = base64.b64encode(pdf_bytes).decode("utf-8")
        iframe = f"""
            <iframe src="data:application/pdf;base64,{encoded}" width="100%" height="{height}" type="application/pdf"></iframe>
        """
        st.markdown(iframe, unsafe_allow_html=True)
    except Exception as exc:
        st.error(f"Unable to preview PDF: {exc}")

# Header
st.markdown("""
<div class="header-container">
    <h1>🔍 Natural Language Candidate Search</h1>
    <p>AI-Powered Resume Reasoning System • Team QuantumSprouts</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ System Settings")
    
    # Database stats
    db = SessionLocal()
    candidate_count = db.query(Candidate).count()
    db.close()
    
    st.metric("Candidates in DB", candidate_count)

    st.divider()
    st.subheader("📥 Add Resume To Search DB")
    db_upload = st.file_uploader(
        "Upload Resume For Indexing",
        type=["pdf"],
        key="db_resume_uploader",
        help="This uploads the PDF, runs PageIndex ingestion, and adds it to searchable candidates."
    )

    if db_upload is not None:
        if st.button("➕ Ingest Into Database", key="ingest_resume_btn", use_container_width=True):
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
                        f"Indexed successfully. Candidate ID: {candidate.id} | Name: {candidate.name} | Category: {candidate.category}"
                    )
                else:
                    st.success(f"Indexed successfully. Candidate ID: {candidate_id}")

                st.caption("The uploaded resume is now part of the searchable database and will appear in future query results if relevant.")
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
    
    # Mode selection
    mode = st.radio(
        "Select Mode",
        ["🔍 Database Search", "📄 Single Resume Analysis"],
        help="Choose between searching the database or analyzing a single resume"
    )
    
    st.divider()
    
    # About
    with st.expander("ℹ️ About This System"):
        st.markdown("""
        **Natural Language Candidate Search** uses:
        - 🧠 **Groq LLM** for intelligent reasoning
        - 🌳 **PageIndex** for resume tree analysis
        - 🗄️ **MySQL** database with 74+ candidates
        
        **No vector embeddings** — Pure reasoning-based search!
        
        **How it works:**
        1. Type your search query in plain English
        2. System reasons over 74 resume trees
        3. Returns top 5 candidates with explanations
        """)

# Main content
if mode == "🔍 Database Search":
    st.header("Database Search")
    st.write("Search across all 74 resumes using natural language queries.")

    input_mode = st.radio(
        "Input Type",
        ["📝 Enter JD Text", "🖼️ Upload Posting Screenshot"],
        horizontal=True,
        help="Use plain JD text or upload a job posting screenshot."
    )

    effective_query = ""

    if input_mode == "📝 Enter JD Text":
        col1, col2 = st.columns([4, 1])

        with col1:
            query = st.text_input(
                "What are you looking for?",
                placeholder="E.g., Python developer with ML experience, HR manager, Finance analyst...",
                key="search_input"
            )

        with col2:
            search_button = st.button("🔍 Search", key="search_btn", use_container_width=True)

        if search_button:
            effective_query = query.strip()

    else:
        screenshot_file = st.file_uploader(
            "Upload Job Posting Screenshot",
            type=["png", "jpg", "jpeg", "webp"],
            key="jd_screenshot",
            help="Upload a job posting image. The system extracts JD text and searches candidates."
        )

        if screenshot_file is not None:
            st.image(screenshot_file, caption="Uploaded Posting Screenshot", use_container_width=True)

            if st.button("🧠 Extract JD & Search", key="search_from_screenshot", use_container_width=True):
                with st.spinner("Extracting JD from screenshot..."):
                    extract_result = extract_jd_from_image(
                        screenshot_file.getvalue(),
                        screenshot_file.type or "image/png"
                    )
                    jd_text = (extract_result.get("jd_text") or "").strip()
                    st.session_state.extracted_jd = jd_text

                    if jd_text:
                        st.success("JD extracted successfully. Running candidate search...")
                        effective_query = jd_text
                    else:
                        st.error(extract_result.get("reasoning", "Could not extract JD from screenshot."))

        if st.session_state.extracted_jd:
            st.markdown("### Extracted JD")
            st.text_area("", st.session_state.extracted_jd, height=180, key="extracted_jd_view")

    if effective_query:
        with st.spinner(f"🔄 Searching across 74 candidates..."):
            db = SessionLocal()
            try:
                start_time = time.time()
                results = search_candidates(effective_query, limit=5, db_session=db)
                latency = (time.time() - start_time) * 1000
                
                st.session_state.search_results = results
                st.session_state.search_query = effective_query
                st.session_state.search_latency = latency
                
            except Exception as e:
                st.error(f"❌ Search failed: {str(e)}")
            finally:
                db.close()
    
    # Display results
    if st.session_state.search_results:
        candidates = st.session_state.search_results.get('candidates', [])
        reasoning = st.session_state.search_results.get('search_reasoning', '')
        
        # Results header
        st.divider()
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Results Found", len(candidates))
        with col2:
            st.metric("Latency", f"{st.session_state.search_latency:.0f}ms", 
                     delta="✅ Fast" if st.session_state.search_latency < 500 else "⚠️ Optimizing")
        with col3:
            st.metric("Query", f'"{st.session_state.search_query[:30]}..."')
        
        st.divider()
        
        # Candidate cards
        if candidates:
            for i, candidate in enumerate(candidates, 1):
                with st.container(border=True):
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.markdown(f"### #{i} {candidate.get('name', 'Unknown')}")
                        st.caption(f"ID: {candidate.get('candidate_id')} • {candidate.get('category', 'Unknown')}")
                    
                    with col2:
                        score = candidate.get('match_score', 0)
                        if score >= 80:
                            score_class = "score-high"
                        elif score >= 60:
                            score_class = "score-medium"
                        else:
                            score_class = "score-low"
                        
                        st.markdown(f'<span class="score-badge {score_class}">{score}%</span>', 
                                  unsafe_allow_html=True)
                    
                    with col3:
                        if st.button("📄 View Resume", key=f"resume_{i}"):
                            resolved = resolve_resume_path(candidate.get("file_path", ""))
                            if resolved:
                                st.session_state.resume_preview_path = str(resolved)
                                st.session_state.resume_preview_name = candidate.get('name', 'Unknown')
                            else:
                                st.warning("Resume file path not found for this candidate.")
                    
                    # Explanation
                    st.markdown(f"**Why this match:**")
                    st.info(candidate.get('explanation', 'No explanation available'))
                    matched_sections = candidate.get('matched_sections', [])
                    if matched_sections:
                        st.caption("Matched sections: " + " | ".join(matched_sections))
            
            # Search reasoning
            with st.expander("💭 How We Reasoned"):
                st.markdown(reasoning)

            if st.session_state.resume_preview_path:
                st.divider()
                header_col, close_col = st.columns([5, 1])
                with header_col:
                    st.markdown(f"### 📄 Resume Preview: {st.session_state.resume_preview_name}")
                with close_col:
                    if st.button("Close Preview", key="close_resume_preview"):
                        st.session_state.resume_preview_path = None
                        st.session_state.resume_preview_name = ""

                preview_path = Path(st.session_state.resume_preview_path)
                if preview_path.exists():
                    render_pdf_preview(preview_path)
                    with open(preview_path, "rb") as pdf_file:
                        st.download_button(
                            "⬇️ Download Resume",
                            data=pdf_file,
                            file_name=preview_path.name,
                            mime="application/pdf",
                            key="download_resume_preview"
                        )
                else:
                    st.warning("Preview file no longer exists on disk.")
        else:
            st.warning("No candidates matched your query. Try a different search!")

else:  # Single Resume Analysis
    st.header("📄 Single Resume Analysis")
    st.write("Upload a resume and ask specific questions about it.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        uploaded_file = st.file_uploader(
            "Upload Resume PDF",
            type="pdf",
            help="Select a PDF resume file"
        )
    
    with col2:
        question = st.text_input(
            "Your Question",
            placeholder="E.g., Is this person suitable for a senior developer role?",
            key="analysis_question"
        )
    
    if uploaded_file and question:
        if st.button("📊 Analyze", use_container_width=True):
            # Save uploaded file temporarily
            temp_path = Path(__file__).parent / "temp_upload.pdf"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            with st.spinner("📋 Analyzing resume..."):
                try:
                    result = analyze_single_resume(str(temp_path), question)
                    
                    # Display results
                    st.divider()
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        recommendation = result.get('recommendation', 'No recommendation')
                        if "Strong Yes" in recommendation:
                            st.success(f"✅ {recommendation}")
                        elif "Yes" in recommendation:
                            st.info(f"✓ {recommendation}")
                        elif "Maybe" in recommendation:
                            st.warning(f"⚠️ {recommendation}")
                        else:
                            st.error(f"❌ {recommendation}")
                    
                    with col2:
                        sections = result.get('relevant_sections', [])
                        st.metric("Relevant Sections", len(sections))
                    
                    # Answer
                    st.markdown("### 📝 Analysis")
                    st.markdown(result.get('answer', 'No answer available'))
                    
                    # Reasoning
                    with st.expander("💭 Detailed Reasoning"):
                        st.markdown(result.get('reasoning', 'No reasoning available'))
                    
                    # Relevant sections
                    if sections:
                        st.markdown("### 📂 Sections Reviewed")
                        st.write(", ".join(sections))
                    
                    # Clean up
                    temp_path.unlink()
                    
                except Exception as e:
                    st.error(f"❌ Analysis failed: {str(e)}")
                    if temp_path.exists():
                        temp_path.unlink()

# Footer
st.divider()
col1, col2, col3 = st.columns(3)

with col1:
    st.caption("🏢 Natural Language Candidate Search v1.0")
with col2:
    st.caption("Built by QuantumSprouts")
with col3:
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
