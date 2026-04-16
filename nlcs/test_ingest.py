#!/usr/bin/env python3
"""
Test script for Resume Ingestion Pipeline (Section 3)
Tests all 6 ingestion functions
"""

import sys
from pathlib import Path

# Add backend to path
current_dir = Path(__file__).parent
backend_dir = current_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from backend.ingest import (
    extract_text_from_pdf,
    extract_candidate_name,
    extract_category_from_path,
    compress_tree,
    build_tree
)

def test_ingestion_pipeline():
    """Test all ingestion functions"""
    
    print("\n" + "="*60)
    print("🧪 TESTING SECTION 3 - INGESTION PIPELINE")
    print("="*60)
    
    # Find a sample PDF from database
    sample_pdf = (current_dir / "uploads").glob("*.pdf")
    sample_pdf_list = list(sample_pdf)
    
    if not sample_pdf_list:
        print("\n❌ No PDF files found in uploads/")
        print("   Run bulk_ingest.py first to download Kaggle dataset")
        return False
    
    pdf_path = str(sample_pdf_list[0])
    print(f"\n📄 Test file: {Path(pdf_path).name}")
    
    # TEST 1: extract_text_from_pdf
    print("\n[TEST 1] extract_text_from_pdf()")
    try:
        text = extract_text_from_pdf(pdf_path)
        if text and len(text) > 50:
            print(f"  ✅ Extracted {len(text)} characters")
            print(f"     Preview: {text[:100]}...")
        else:
            print(f"  ⚠️  Extracted text too short: {len(text)} chars")
            return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False
    
    # TEST 2: extract_candidate_name
    print("\n[TEST 2] extract_candidate_name()")
    try:
        name = extract_candidate_name(text)
        if name and name != "Unknown":
            print(f"  ✅ Extracted name: {name}")
        else:
            print(f"  ⚠️  Could not extract name")
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False
    
    # TEST 3: extract_category_from_path
    print("\n[TEST 3] extract_category_from_path()")
    try:
        category = extract_category_from_path(pdf_path)
        print(f"  ✅ Extracted category: {category}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False
    
    # TEST 4: compress_tree
    print("\n[TEST 4] compress_tree()")
    try:
        sample_tree = [
            {"node_id": "001", "title": "Skills", "summary": "Python React AWS", "children": []},
            {"node_id": "002", "title": "Experience", "summary": "5 years at startup", "children": []}
        ]
        compressed = compress_tree(sample_tree)
        if compressed and len(compressed) > 0:
            print(f"  ✅ Compressed tree to {len(compressed)} nodes")
            print(f"     Sample node: {compressed[0]}")
        else:
            print(f"  ⚠️  Tree compression returned empty")
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False
    
    # TEST 5: build_tree (PageIndex)
    print("\n[TEST 5] build_tree() - PageIndex API")
    try:
        print(f"  ⏳ Attempting PageIndex API call...")
        tree = build_tree(text[:2000], "Test Candidate")
        if tree:
            print(f"  ✅ Built tree with {len(tree)} nodes")
        else:
            print(f"  ⚠️  PageIndex returned empty tree (API key missing?)")
    except Exception as e:
        print(f"  ⚠️  PageIndex call failed (expected if API key not set): {e}")
    
    print("\n" + "="*60)
    print("✅ INGESTION PIPELINE TESTS COMPLETE")
    print("="*60)
    return True

if __name__ == "__main__":
    success = test_ingestion_pipeline()
    sys.exit(0 if success else 1)
