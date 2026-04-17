# Demo: Deterministic vs LLM Reranking

"""
This script demonstrates the difference between deterministic scoring and LLM reranking
for a sample candidate search query using your backend logic.

It prints:
- The query
- Deterministic scores for all candidates
- LLM reranked results
"""

from search import candidate_relevance_score, llm_rank_candidates
from models import Candidate
from database import SessionLocal

# Example query
QUERY = "python backend developer"
LIMIT = 5

def fetch_all_candidates(db):
    return db.query(Candidate).all()

def main():
    db = SessionLocal()
    candidates = fetch_all_candidates(db)
    print(f"Query: {QUERY}\n")
    print("Deterministic scores:")
    scored = [
        (candidate_relevance_score(QUERY, c), c)
        for c in candidates
    ]
    scored_sorted = sorted(scored, key=lambda x: (-x[0], x[1].id))
    for score, c in scored_sorted[:max(LIMIT*3, 12)]:
        print(f"  {c.id}: {c.name} | {c.category} | Score: {score}")

    shortlist = scored_sorted[:max(LIMIT*3, 12)]
    print("\nLLM reranked results:")
    llm_result = llm_rank_candidates(QUERY, shortlist)
    for idx, cand in enumerate(llm_result.get("candidates", []), 1):
        print(f"  Rank {idx}: {cand.get('name')} | {cand.get('category')} | LLM Score: {cand.get('score', 'N/A')}")

    db.close()

if __name__ == "__main__":
    main()
