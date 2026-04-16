#!/usr/bin/env python3
"""
Test Search Engine with Real APIs
Tests Groq reasoning over resume trees for accuracy & speed
"""

import sys
import os
from pathlib import Path
import time
import json

# Add backend to path
current_dir = Path(__file__).parent
backend_dir = current_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from backend.database import SessionLocal
from backend.models import Candidate
from backend.search import search_candidates

def test_search_engine():
    """Test search engine with real Groq API"""
    
    print("\n" + "="*70)
    print("🧪 TESTING GROQ SEARCH ENGINE - ACCURACY & SPEED")
    print("="*70)
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Check candidate count
        count = db.query(Candidate).count()
        print(f"\n📊 Candidates in database: {count}")
        
        if count == 0:
            print("❌ No candidates in database!")
            return False
        
        # Show sample candidates
        print(f"\n📋 Sample candidates in DB:")
        samples = db.query(Candidate).limit(3).all()
        for candidate in samples:
            print(f"   - ID {candidate.id}: {candidate.name[:40]} ({candidate.category})")
        
        # TEST QUERIES
        test_queries = [
            "Find a Python developer with machine learning experience",
            "Find an HR manager with recruitment and training background",
            "Find a finance professional with banking sector experience"
        ]
        
        results_summary = []
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{'='*70}")
            print(f"🔍 QUERY {i}: {query}")
            print(f"{'='*70}")
            
            start_time = time.time()
            result = search_candidates(query, limit=5, db_session=db)
            latency_ms = (time.time() - start_time) * 1000
            
            candidates = result.get("candidates", [])
            reasoning = result.get("search_reasoning", "")
            
            print(f"\n⏱️  Latency: {latency_ms:.1f}ms {'✅' if latency_ms < 500 else '⚠️'}")
            print(f"📊 Results: {len(candidates)} candidates found")
            
            if candidates:
                print(f"\n🏆 TOP RESULTS:")
                for j, cand in enumerate(candidates[:3], 1):
                    print(f"\n   {j}. {cand.get('name', 'N/A')} (ID: {cand.get('candidate_id')})")
                    print(f"      Category: {cand.get('category', 'N/A')}")
                    print(f"      Match Score: {cand.get('match_score', 'N/A')}%")
                    print(f"      Explanation: {cand.get('explanation', 'N/A')[:150]}...")
            else:
                print("   ⚠️  No results returned")
            
            if reasoning:
                print(f"\n💭 Search Reasoning: {reasoning[:200]}...")
            
            results_summary.append({
                "query": query,
                "results": len(candidates),
                "latency_ms": round(latency_ms, 2),
                "first_match_score": candidates[0].get("match_score", 0) if candidates else 0
            })
            
            time.sleep(1)  # Rate limiting
        
        # SUMMARY
        print(f"\n" + "="*70)
        print("📊 SEARCH ENGINE TEST SUMMARY")
        print("="*70)
        
        total_latency = sum(r["latency_ms"] for r in results_summary)
        avg_latency = total_latency / len(results_summary)
        
        print(f"\n✅ Queries tested: {len(results_summary)}")
        print(f"⏱️  Average latency: {avg_latency:.1f}ms")
        print(f"🎯 <500ms target: {'✅ PASS' if avg_latency < 500 else '⚠️ NEEDS OPTIMIZATION'}")
        
        print(f"\nDetailed Results:")
        for r in results_summary:
            print(f"  • {r['query'][:40]}...")
            print(f"    - Found: {r['results']} candidates")
            print(f"    - Latency: {r['latency_ms']}ms")
            print(f"    - Top Score: {r['first_match_score']}%")
        
        print("\n" + "="*70)
        print("✅ SEARCH ENGINE TEST COMPLETE")
        print("="*70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_search_engine()
    sys.exit(0 if success else 1)
