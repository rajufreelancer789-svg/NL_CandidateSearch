#!/usr/bin/env python3
"""
Index every PDF present in the current uploads/ folder.

This is the main repair path when uploads exist but are not yet indexed in MySQL.

Usage:
  python backend/index_uploads.py
  python backend/index_uploads.py --limit 20
  python backend/index_uploads.py --skip-existing
"""

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from database import SessionLocal
from models import Candidate
from ingest import ingest_resume

UPLOADS_FOLDER = parent_dir / "uploads"


def file_hash(path: Path) -> str:
    """Return SHA1 hash for duplicate checks."""
    h = hashlib.sha1()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def parse_args():
    parser = argparse.ArgumentParser(description="Index PDFs from uploads/ into MySQL")
    parser.add_argument("--limit", type=int, default=None, help="Process at most N files")
    parser.add_argument("--skip-existing", action="store_true", help="Skip PDFs already present in DB by filename")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between ingestions in seconds")
    return parser.parse_args()


def main():
    args = parse_args()

    if not UPLOADS_FOLDER.exists():
        raise SystemExit(f"Uploads folder not found: {UPLOADS_FOLDER}")

    pdfs = sorted(UPLOADS_FOLDER.glob("*.pdf"))
    if args.limit is not None:
        pdfs = pdfs[: args.limit]

    db = SessionLocal()
    try:
        existing_names = {
            Path(row.file_path or "").name
            for row in db.query(Candidate).all()
            if row.file_path
        }
        existing_hashes = set()
        # Hashes are useful for exact duplicates, but we only build them if needed.

        print("\n" + "=" * 80)
        print("UPLOADS INDEXING")
        print("=" * 80)
        print(f"Uploads PDFs found: {len(pdfs)}")
        print(f"Existing DB file names: {len(existing_names)}")
        print(f"Skip existing: {args.skip_existing}")
        print("=" * 80 + "\n")

        processed = 0
        ingested = 0
        skipped = 0
        failed = 0

        for idx, pdf_path in enumerate(pdfs, start=1):
            if args.skip_existing and pdf_path.name in existing_names:
                skipped += 1
                print(f"[{idx}/{len(pdfs)}] SKIP existing: {pdf_path.name}")
                continue

            # Avoid exact duplicate files in uploads itself.
            try:
                fingerprint = file_hash(pdf_path)
            except Exception as exc:
                failed += 1
                print(f"[{idx}/{len(pdfs)}] ❌ hash error {pdf_path.name}: {exc}")
                continue

            if fingerprint in existing_hashes:
                skipped += 1
                print(f"[{idx}/{len(pdfs)}] SKIP duplicate content: {pdf_path.name}")
                continue
            existing_hashes.add(fingerprint)

            processed += 1
            try:
                print(f"[{idx}/{len(pdfs)}] INGEST: {pdf_path.name}")
                candidate_id = ingest_resume(str(pdf_path), db)
                ingested += 1
                print(f"  ✅ candidate_id={candidate_id}")
            except Exception as exc:
                failed += 1
                print(f"  ❌ failed: {str(exc)[:200]}")

            if args.delay > 0 and idx < len(pdfs):
                time.sleep(args.delay)

        print("\n" + "=" * 80)
        print("UPLOAD INDEX REPORT")
        print("=" * 80)
        print(f"Processed: {processed}")
        print(f"Ingested: {ingested}")
        print(f"Skipped: {skipped}")
        print(f"Failed: {failed}")
        print(f"DB total rows: {db.query(Candidate).count()}")
        print("=" * 80)

    finally:
        db.close()


if __name__ == "__main__":
    main()
