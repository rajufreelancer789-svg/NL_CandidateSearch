# FastAPI Backend for Natural Language Candidate Search System
# Team: QuantumSprouts

import sys
import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session
import time

# Handle import paths
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from database import SessionLocal, engine, Base
from models import Candidate
from search import search_candidates, analyze_single_resume
from ingest import ingest_resume
import models as db_models

# Database initialization
Base.metadata.create_all(bind=engine)

# Request/Response Models
class SearchRequest(BaseModel):
    query: str
    limit: int = 5

class AnalyzeRequest(BaseModel):
    question: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Natural Language Candidate Search System starting...")
    yield
    # Shutdown
    print("👋 Shutting down...")

app = FastAPI(
    title="NLCS API",
    description="Natural Language Candidate Search",
    version="1.0.0",
    lifespan=lifespan
)

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount uploads folder
uploads_path = Path(__file__).parent.parent / "uploads"
uploads_path.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_path)), name="uploads")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============ ENDPOINTS ============

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    candidates_count = db.query(db_models.Candidate).count()
    return {
        "status": "ok",
        "candidates_in_db": candidates_count
    }

@app.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload and ingest a resume PDF"""
    try:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Save file
        file_path = uploads_path / file.filename
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Ingest resume
        candidate_id = ingest_resume(str(file_path), db)
        
        # Get candidate info
        candidate = db.query(db_models.Candidate).filter(
            db_models.Candidate.id == candidate_id
        ).first()
        
        return {
            "status": "success",
            "candidate_id": candidate.id,
            "name": candidate.name,
            "category": candidate.category,
            "message": "Resume ingested successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search")
async def search(request: SearchRequest, db: Session = Depends(get_db)):
    """Search candidates database"""
    try:
        start_time = time.time()
        results = search_candidates(request.query, request.limit, db)
        latency_ms = (time.time() - start_time) * 1000
        
        return {
            "results": results.get("candidates", []),
            "total_found": len(results.get("candidates", [])),
            "latency_ms": round(latency_ms, 2),
            "search_reasoning": results.get("search_reasoning", "")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    question: str = None,
    db: Session = Depends(get_db)
):
    """Analyze a single resume"""
    try:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Save temporarily
        temp_path = uploads_path / f"temp_{file.filename}"
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Analyze
        result = analyze_single_resume(str(temp_path), question)
        
        # Clean up
        if temp_path.exists():
            temp_path.unlink()
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/candidates")
async def get_all_candidates(db: Session = Depends(get_db)):
    """Get all candidates in database"""
    try:
        candidates = db.query(db_models.Candidate).all()
        return {
            "candidates": [
                {
                    "id": c.id,
                    "name": c.name,
                    "email": c.email,
                    "category": c.category,
                    "uploaded_at": c.uploaded_at.isoformat() if c.uploaded_at else None
                }
                for c in candidates
            ],
            "total": len(candidates)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
