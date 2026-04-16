#!/usr/bin/env python3
"""
Export representative PageIndex resume trees from the database.

This is meant for evaluation and question-forming work:
- one or more resumes per category/domain
- full stored JSON tree included
- optional category filtering

Examples:
  python backend/export_resume_tree_samples.py
  python backend/export_resume_tree_samples.py --per-category 2 --output ../resume_tree_samples.json
  python backend/export_resume_tree_samples.py --categories IT Finance Banking
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from database import SessionLocal
from models import Candidate


def parse_args():
    parser = argparse.ArgumentParser(description="Export representative resume PageIndex trees")
    parser.add_argument(
        "--output",
        default=str(parent_dir / "resume_tree_samples.json"),
        help="Output JSON file path",
    )
    parser.add_argument(
        "--per-category",
        type=int,
        default=1,
        help="Number of resumes to export per category",
    )
    parser.add_argument(
        "--categories",
        nargs="*",
        default=None,
        help="Optional category names to include",
    )
    return parser.parse_args()


def parse_json_field(value):
    if value in (None, ""):
        return None
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            return value
    return value


def main():
    args = parse_args()
    db = SessionLocal()
    try:
        rows = (
            db.query(Candidate)
            .filter(Candidate.tree_json.isnot(None), Candidate.tree_json != "")
            .order_by(Candidate.category.asc(), Candidate.id.asc())
            .all()
        )

        grouped = defaultdict(list)
        for row in rows:
            category = (row.category or "Uncategorized").strip() or "Uncategorized"
            grouped[category].append(row)

        if args.categories:
            wanted = {item.strip() for item in args.categories if item.strip()}
            grouped = defaultdict(list, {k: v for k, v in grouped.items() if k in wanted})

        samples = []
        for category in sorted(grouped.keys(), key=str.lower):
            for row in grouped[category][: max(args.per_category, 1)]:
                samples.append(
                    {
                        "id": row.id,
                        "name": row.name,
                        "category": row.category,
                        "file_path": row.file_path,
                        "doc_id": row.doc_id,
                        "tree_json": parse_json_field(row.tree_json),
                        "tree_compressed": parse_json_field(row.tree_compressed),
                    }
                )

        output_path = Path(args.output).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "generated_from": "nlcs candidates table",
            "total_db_rows": len(rows),
            "categories": len(grouped),
            "per_category": args.per_category,
            "samples": samples,
        }

        output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))

        print(f"WROTE {output_path}")
        print(f"TOTAL_DB_ROWS {len(rows)}")
        print(f"CATEGORIES {len(grouped)}")
        print(f"SAMPLES {len(samples)}")
        for sample in samples:
            print(f"- {sample['category']}: {sample['name']} ({sample['file_path']})")
    finally:
        db.close()


if __name__ == "__main__":
    main()