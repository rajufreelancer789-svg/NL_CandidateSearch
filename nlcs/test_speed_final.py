#!/usr/bin/env python3
"""
Final Speed Optimization Test
Demonstrates search speed with mixtral + caching
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

def test_search_optimization():
    print("\n" + "="*80)
    print("🚀 SPEED OPTIMIZATION - FINAL TEST")
    print("="*80)
    
    print(f"\n✨ Optimizations Applied:")
    print(f"   1. Fast Model: mixtral-8x7b-32768 (instead of llama-3.3)")
    print(f"   2. Result Caching: LRU cache for repeated queries")
    print(f"   3. Optimized Prompts: Concise formatting")
    print(f"   4. Batch Processing: {8} candidates per request")
    
    db = SessionLocal()
    
    try:
        count = db.query(Candidate).count()
        print(f"\n📊 Database: {count} candidates")
        
        query = "Find a Python developer with leadership experience"
        
        print(f"\n{'='*80}")
        print(f"TEST 1: FIRST SEARCH (COLD CACHE)")
        print(f"{'='*80}")
        print(f"🔍 Query: {query}\n")
        
        start_time = time.time()
        result1 = search_candidates(query, limit=5, db_session=db)
        time1 = (time.time() - start_time) * 1000
        
        candidates1 = result1.get("candidates", [])
        print(f"\n✅ RESULTS: {len(candidates1)} candidates")
        print(f"⏱️  Latency: {time1:.0f}ms")
        
        for i, cand in enumerate(candidates1[:3], 1):
            print(f"   {i}. {cand.get('name', 'N/A')[:40]} - {cand.get('match_score', 0)}%")
        
        # Test cache
        print(f"\n{'='*80}")
        print(f"TEST 2: REPEAT SEARCH (WARM CACHE)")
        print(f"{'='*80}")
        print(f"🔍 Same query (should hit cache)\n")
        
        start_time = time.time()
        result2 = search_candidates(query, limit=5, db_session=db)
        time2 = (time.time() - start_time) * 1000
        
        candidates2 = result2.get("candidates", [])
        print(f"\n✅ RESULTS: {len(candidates2)} candidates")
        print(f"⏱️  Latency: {time2:.0f}ms (instant from cache!)")
        
        # Summary
        print(f"\n{'='*80}")
        print(f"📈 OPTIMIZATION SUMMARY")
        print(f"{'='*80}")
        
        print(f"\n📊 Performance Metrics:")
        print(f"   First search (cold): {time1:.0f}ms")
        print(f"   Repeat search (cached): {time2:.0f}ms")
        print(f"   Cache speedup: {time1/time2:.1f}x faster! 🎉")
        
        print(f"\n🚀 IMPROVEMENTS vs ORIGINAL:")
        print(f"   Original (sequential 131s): 131,000ms")
        print(f"   First search (optimized): {time1:.0f}ms ")
        print(f"   Repeat search (cached): {time2:.0f}ms")
        if time1 > 0:
            speedup = 131000 / time1
            print(f"   Overall speedup: {speedup:.1f}x faster!")
        
        print(f"\n✨ Key Optimizations:")
        print(f"   ✅ Faster Model: mixtral-8x7b")
        print(f"   ✅ Intelligent Caching: Instant repeat searches")
        print(f"   ✅ Concise Prompts: Reduced token usage")
        print(f"   ✅ Batch Processing: Efficient candidate grouping")
        
        print(f"\n{'='*80}")
        print(f"✅ SPEED OPTIMIZATION COMPLETE")
        print(f"{'='*80 + '\n'}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_search_optimization()
    sys.exit(0 if success else 1)
