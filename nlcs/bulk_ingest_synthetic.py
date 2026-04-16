# Bulk ingest all synthetic (generated) resumes into the system
# Usage: python bulk_ingest_synthetic.py

import os
from pathlib import Path
from backend.database import SessionLocal
from backend.ingest import ingest_resume

# Directory containing generated PDFs (current directory)
PDF_DIR = Path(__file__).parent

def find_generated_pdfs():
    """Find all *_resume.pdf files in the current directory."""
    return sorted(PDF_DIR.glob("*_resume.pdf"))

def main():
    pdf_files = find_generated_pdfs()
    if not pdf_files:
        print("No generated resume PDFs found.")
        return
    print(f"Found {len(pdf_files)} generated resumes.")
    db = SessionLocal()
    success, fail = 0, 0
    for pdf_path in pdf_files:
        try:
            ingest_resume(str(pdf_path), db)
            success += 1
        except Exception as e:
            print(f"❌ Failed to ingest {pdf_path.name}: {e}")
            fail += 1
    db.close()
    print(f"\nIngestion complete: {success} succeeded, {fail} failed.")

if __name__ == "__main__":
    main()
