#!/usr/bin/env python3
"""
Audit uploads/ coverage against the Candidate table.

Prints:
- total PDF files in uploads/
- total DB rows
- how many uploads are represented in DB by filename
- the missing filenames
"""

import sys
from pathlib import Path

current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from database import SessionLocal
from models import Candidate

UPLOADS_FOLDER = parent_dir / "uploads"


def main():
    pdfs = sorted(UPLOADS_FOLDER.glob("*.pdf"))
    db = SessionLocal()
    try:
        db_file_names = {
            Path(row.file_path or "").name
            for row in db.query(Candidate).all()
            if row.file_path
        }
        missing = [path.name for path in pdfs if path.name not in db_file_names]

        print(f"UPLOAD_PDFS {len(pdfs)}")
        print(f"DB_ROWS {db.query(Candidate).count()}")
        print(f"INDEXED_IN_DB {len(pdfs) - len(missing)}")
        print(f"MISSING_FROM_DB {len(missing)}")
        if missing:
            print("MISSING_FILES")
            for name in missing:
                print(name)
    finally:
        db.close()


if __name__ == "__main__":
    main()
