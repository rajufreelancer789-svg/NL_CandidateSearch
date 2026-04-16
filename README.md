# Resume Search System: Vectorless RAG vs Traditional Approaches

## Problem Statement (PS)

**Goal:**
Build a robust, explainable, and intent-driven resume search system that allows recruiters to upload resumes, index them, and immediately retrieve relevant candidates for natural language queries. The system must provide clear, intent-based explanations for why each candidate matches, and work reliably even if external APIs (like PageIndex) are unavailable.

---

## Traditional Solution (Keyword/Section Search)
- **Approach:**
  - Extract text from resumes (PDF/Docx).
  - Use keyword matching, section heuristics, or simple TF-IDF to find relevant candidates.
  - Explanations are based on keyword/section overlap (e.g., "Matched 'Python' in Skills").
- **Limitations:**
  - Shallow understanding of intent.
  - Poor at handling synonyms, context, or complex queries.
  - Explanations are not human-like or role-aware.

---

## Vector RAG Solution (Vector Database + RAG)
- **Approach:**
  - Extract text and chunk resumes into sections.
  - Embed sections using a vector model (e.g., OpenAI, HuggingFace).
  - Store embeddings in a vector database (e.g., Pinecone, FAISS).
  - For a query, embed and retrieve top-k similar chunks, then use a Retrieval-Augmented Generation (RAG) LLM to generate answers/explanations.
- **Pros:**
  - Handles synonyms, context, and semantic similarity.
  - Can generate more natural explanations.
- **Cons:**
  - Requires vector DB infrastructure and embedding model management.
  - Latency and cost for large-scale search.
  - Explanations may still be generic if not carefully prompted.

---

## Our Solution: Vectorless RAG (PageIndex + LLM Reasoning)
- **Approach:**
  - Extract resumes and build a hierarchical tree (PageIndex API or local fallback).
  - Store tree structure and compressed summaries in a relational DB.
  - For a query:
    - Use deterministic routing and LLM reranking to shortlist candidates.
    - LLM generates intent-based, role-aware explanations using tree context (no vector DB needed).
    - If PageIndex is unavailable, fallback to local tree ensures robustness.
- **Advantages:**
  - No vector DB or embeddings required.
  - Fast, explainable, and robust to API failures.
  - Explanations are intent-driven, citing actual skills/experience, not just keywords.
  - Immediate searchability after upload.

---

## How to Run the System

### 1. **Setup**
- Clone the repository and navigate to the project folder.
- Create and activate a Python virtual environment:
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```
- Install dependencies:
  ```bash
  pip install -r nlcs/backend/requirements.txt
  pip install reportlab pymupdf python-dotenv sqlalchemy
  ```
- Set up your `.env` file with the required API keys and DB credentials (see `.env.example`).

### 2. **Database**
- Ensure MySQL is running and accessible.
- Initialize the database tables:
  ```bash
  python nlcs/backend/database.py
  ```

### 3. **Resume Ingestion**
- To ingest a single resume PDF:
  ```bash
  python nlcs/backend/ingest.py /path/to/resume.pdf
  ```
- To bulk ingest synthetic resumes:
  ```bash
  python nlcs/resumes.py all
  # Then use a bulk ingestion script to index all generated PDFs
  ```

### 4. **Running the Search UI**
- Start the Streamlit app:
  ```bash
  streamlit run nlcs/app.py
  ```
- Upload resumes, run queries, and view intent-based explanations in the UI.

### 5. **Fallbacks and Robustness**
- If PageIndex API is unavailable, the system automatically falls back to a local tree builder.
- All resumes are immediately searchable after upload, regardless of API status.

---

## Project Structure
- `nlcs/app.py` — Streamlit UI and main orchestration
- `nlcs/backend/ingest.py` — Resume ingestion, tree building, fallback logic
- `nlcs/backend/search.py` — Candidate search, LLM reranking, explanation generation
- `nlcs/resumes.py` — Synthetic resume generator and PDF builder
- `nlcs/backend/database.py` — DB models and connection
- `uploads/` — Uploaded and generated resume PDFs

---

## Credits
- PageIndex API for tree extraction
- Groq/OpenAI LLMs for reranking and explanations
- ReportLab for PDF generation

---

## Contact
For questions or support, contact: [Your Name/Team]
