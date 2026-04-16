# Project Review: Vectorless RAG Resume Search System

## 1. Project Overview

Our system is a next-generation, explainable resume search platform designed for recruiters and hiring teams. It enables robust, intent-driven candidate search and instant resume ingestion, with clear, LLM-powered explanations for every match. The system is resilient to external API failures and does not require a vector database, making it cost-effective and easy to maintain.

---

## 2. Problem Statement
- Recruiters need to search and rank candidates using natural language queries.
- Explanations for matches must be intent-based, not just keyword/section overlap.
- The system must be robust to API failures and support immediate search after upload.

---

## 3. Solution Architecture

### a. Ingestion Pipeline
- **PDF Upload:** Users upload resumes via the UI or bulk scripts.
- **Tree Extraction:**
  - Primary: PageIndex API builds a hierarchical tree of resume sections.
  - Fallback: Local tree builder if PageIndex is unavailable.
- **Compression:** Trees are compressed for fast search (title, summary, node_id).
- **Database Storage:**
  - Stores candidate metadata, full tree, and compressed tree in MySQL.

### b. Search & Reasoning
- **Query Input:** User enters a natural language search query.
- **Stage 1 Routing:**
  - Domain/category routing using anchors and LLM (if enabled).
- **Shortlisting:**
  - Deterministic scoring and overlap for initial shortlist.
- **LLM Reranking:**
  - Groq/OpenAI LLM reranks candidates and generates intent-based explanations.
- **Explanation:**
  - LLM explanations cite actual skills/experience, not just section names.
  - Fallback to deterministic explanation if LLM is unavailable.

### c. User Interface
- **Streamlit App:**
  - Upload resumes (single or bulk).
  - Search with natural language queries.
  - View candidate cards with explanations and evidence.
  - Immediate feedback on upload and search.

---

## 4. Module Breakdown

### 1. `nlcs/app.py` (UI & Orchestration)
- Streamlit-based UI for upload, search, and results display.
- Handles user session, sidebar, and candidate card rendering.

### 2. `nlcs/backend/ingest.py` (Ingestion)
- PDF text extraction (PyMuPDF).
- PageIndex tree building and fallback logic.
- Candidate name/category extraction.
- DB insert with full and compressed tree.

### 3. `nlcs/backend/search.py` (Search & Reasoning)
- Query parsing and anchor routing.
- Section evidence extraction.
- LLM reranking and explanation generation.
- Fallback to deterministic explanations.

### 4. `nlcs/backend/database.py` (Database)
- SQLAlchemy models and session management.
- MySQL connection pooling.

### 5. `nlcs/resumes.py` (Synthetic Resume Generator)
- Generates 100+ realistic candidate resumes as PDFs.
- Used for bulk ingestion and testing.

### 6. `nlcs/backend/bulk_ingest.py` / `bulk_ingest_synthetic.py` (Bulk Ingestion)
- Scripts to ingest large numbers of resumes from PDFs.
- Calls the ingestion pipeline for each file.

---

## 5. User Flow

1. **Resume Upload:**
   - User uploads a resume (PDF) via the UI or bulk script.
   - System extracts text, builds tree, and stores in DB.
   - Resume is immediately searchable.

2. **Candidate Search:**
   - User enters a natural language query (e.g., "GenAI developer with LLM experience").
   - System routes query, shortlists candidates, and reranks with LLM.
   - Top candidates are shown with intent-based explanations and evidence.

3. **Explanation:**
   - Each candidate card displays why the candidate matches, citing actual skills/experience.
   - If LLM is unavailable, a deterministic explanation is shown.

4. **Fallbacks:**
   - If PageIndex API fails, local tree builder is used.
   - If LLM fails, deterministic explanations are used.

---

## 6. Key Features
- **Vectorless RAG:** No vector DB required; uses tree structure and LLM for reasoning.
- **Robustness:** Works even if PageIndex or LLM is unavailable.
- **Explainability:** Intent-based, human-like explanations for every match.
- **Immediate Searchability:** Resumes are searchable right after upload.
- **Bulk Ingestion:** Supports large-scale resume ingestion for testing and demos.

---

## 7. How to Run

1. **Setup Python Environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r nlcs/backend/requirements.txt
   pip install reportlab pymupdf python-dotenv sqlalchemy
   ```
2. **Configure `.env`:** Add DB credentials and API keys.
3. **Initialize Database:**
   ```bash
   python nlcs/backend/database.py
   ```
4. **Ingest Resumes:**
   - Single: `python nlcs/backend/ingest.py /path/to/resume.pdf`
   - Bulk: `python nlcs/resumes.py all` + bulk ingestion script
5. **Run UI:**
   ```bash
   streamlit run nlcs/app.py
   ```

---

## 8. Technologies Used
- Python, Streamlit, SQLAlchemy, MySQL
- PyMuPDF, ReportLab, dotenv
- PageIndex API, Groq/OpenAI LLMs

---

## 9. Team & Contact
- [QuantumSprouts]
- [quantumsprouts@gmail.com]

---

## 10. Appendix: Example Query & Explanation
- **Query:** "GenAI developer with LLM experience"
- **Result:**
  - Top candidate: "Rahul Verma"
  - **Explanation:** "Rahul has 8 years of Python experience, led LLM-based projects, and contributed to open-source GenAI libraries."

---

This document covers the project end-to-end for review, demo, or onboarding purposes.
