#!/usr/bin/env python3
"""
Test Optimized Search Engine with Batching
"""

import sys
from pathlib import Path
import time

current_dir = Path(__file__).parent
backend_dir = current_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from backend.database import SessionLocal
from backend.models import Candidate
from backend.search import search_candidates

def test_search_optimized():
    print("\n" + "="*70)
    print("🧪 TESTING OPTIMIZED BATCHED SEARCH ENGINE")
    print("="*70)
    
    db = SessionLocal()
    
    try:
        count = db.query(Candidate).count()
        print(f"\n📊 Total candidates: {count}\n")
        
        # Single test query
        query = "Find a Python developer with machine learning or data science experience"
        
        print(f"🔍 Query: {query}\n")
        
        start_time = time.time()
        result = search_candidates(query, limit=5, db_session=db)
        total_latency = (time.time() - start_time) * 1000
        
        candidates = result.get("candidates", [])
        reasoning = result.get("search_reasoning", "")
        
        # Results
        print(f"\n{'='*70}")
        print(f"✅ SEARCH COMPLETE")
        print(f"{'='*70}")
        print(f"\n⏱️  Total Latency: {total_latency:.1f}ms {'✅' if total_latency < 500 else '⚠️'}")
        print(f"📊 Results: {len(candidates)} candidates\n")
        
        if candidates:
            print(f"🏆 TOP RESULTS:\n")
            for i, cand in enumerate(candidates, 1):
                print(f"{i}. {cand.get('name', 'N/A')} (ID: {cand.get('candidate_id')})")
                print(f"   Category: {cand.get('category', 'N/A')}")
                print(f"   Match: {cand.get('match_score', 0)}%")
                print(f"   Reason: {cand.get('explanation', 'N/A')}\n")
        else:
            print("   ⚠️  No results found")
        
        print(f"💭 Search Reasoning: {reasoning}\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_search_optimized()
    sys.exit(0 if success else 1)
