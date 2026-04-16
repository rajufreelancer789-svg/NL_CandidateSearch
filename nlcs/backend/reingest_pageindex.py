#!/usr/bin/env python3
"""
Re-ingest existing candidate records through PageIndex and refresh tree fields.

This script updates existing DB rows in-place:
- doc_id
- tree_json
- tree_compressed

Usage examples:
  python backend/reingest_pageindex.py --only-missing
  python backend/reingest_pageindex.py --all --delay 2
  python backend/reingest_pageindex.py --limit 10 --dry-run
"""

import argparse
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
from ingest import build_pageindex_tree_from_pdf, compress_tree


def has_meaningful_tree(candidate: Candidate) -> bool:
    """Return True if candidate has a non-empty compressed tree."""
    if not candidate.tree_compressed:
        return False
    try:
        tree = json.loads(candidate.tree_compressed)
        return isinstance(tree, list) and len(tree) > 0
    except Exception:
        return False


def select_candidates(db, mode_all: bool, only_missing: bool, limit: int | None):
    """Select candidate rows for re-ingestion."""
    rows = db.query(Candidate).order_by(Candidate.id.asc()).all()

    if mode_all:
        selected = rows
    elif only_missing:
        selected = [c for c in rows if not has_meaningful_tree(c)]
    else:
        # default behavior: only missing
        selected = [c for c in rows if not has_meaningful_tree(c)]

    if limit is not None:
        selected = selected[:limit]

    return rows, selected


def run_reingestion(mode_all: bool, only_missing: bool, limit: int | None, delay_seconds: float, dry_run: bool):
    db = SessionLocal()

    processed = 0
    succeeded = 0
    failed = 0

    try:
        all_rows, selected = select_candidates(db, mode_all, only_missing, limit)

        print("\n" + "=" * 78)
        print("PAGEINDEX RE-INGESTION")
        print("=" * 78)
        print(f"Total rows in DB: {len(all_rows)}")
        print(f"Rows selected for re-ingest: {len(selected)}")
        print(f"Mode: {'ALL' if mode_all else 'ONLY_MISSING'}")
        print(f"Dry run: {dry_run}")
        print("=" * 78 + "\n")

        if not selected:
            print("No rows selected. Nothing to do.")
            return

        for idx, candidate in enumerate(selected, start=1):
            processed += 1
            print(f"[{idx}/{len(selected)}] Candidate ID {candidate.id}: {candidate.name[:80]}")

            file_path = Path(candidate.file_path or "")
            if not file_path.exists():
                failed += 1
                print(f"  ❌ File not found: {candidate.file_path}")
                continue

            if dry_run:
                print("  ℹ️ Dry run enabled: skipping PageIndex call")
                continue

            try:
                doc_id, tree = build_pageindex_tree_from_pdf(str(file_path), candidate.name or file_path.stem)
                compressed = compress_tree(tree)

                candidate.doc_id = doc_id
                candidate.tree_json = json.dumps(tree)
                candidate.tree_compressed = json.dumps(compressed)

                db.add(candidate)
                db.commit()

                succeeded += 1
                print(f"  ✅ Updated doc_id={doc_id}, nodes={len(compressed)}")

            except Exception as exc:
                db.rollback()
                failed += 1
                print(f"  ❌ Failed: {str(exc)[:180]}")

            if delay_seconds > 0 and idx < len(selected):
                time.sleep(delay_seconds)

        print("\n" + "=" * 78)
        print("RE-INGESTION REPORT")
        print("=" * 78)
        print(f"Processed: {processed}")
        print(f"Succeeded: {succeeded}")
        print(f"Failed: {failed}")
        print(f"Remaining with empty trees: {count_missing_trees(db)}")
        print("=" * 78)

    finally:
        db.close()


def count_missing_trees(db) -> int:
    """Count candidate rows missing meaningful tree data."""
    rows = db.query(Candidate).all()
    return sum(1 for row in rows if not has_meaningful_tree(row))


def parse_args():
    parser = argparse.ArgumentParser(description="Re-ingest existing candidates through PageIndex")
    parser.add_argument("--all", action="store_true", help="Re-ingest all rows")
    parser.add_argument("--only-missing", action="store_true", help="Re-ingest only rows with empty/invalid tree")
    parser.add_argument("--limit", type=int, default=None, help="Max rows to process")
    parser.add_argument("--delay", type=float, default=2.0, help="Delay in seconds between PageIndex calls")
    parser.add_argument("--dry-run", action="store_true", help="Show selection without calling PageIndex")
    return parser.parse_args()


def main():
    args = parse_args()

    mode_all = args.all
    only_missing = args.only_missing

    # Default safely to only missing if neither flag is provided
    if not mode_all and not only_missing:
        only_missing = True

    run_reingestion(
        mode_all=mode_all,
        only_missing=only_missing,
        limit=args.limit,
        delay_seconds=args.delay,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
