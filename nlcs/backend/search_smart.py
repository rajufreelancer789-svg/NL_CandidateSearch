# Smart Rate-Limited Search Engine
# Handles Groq free tier rate limits with intelligent queuing

import json
import time
import sys
import os
import asyncio
from pathlib import Path
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor

current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

load_dotenv(parent_dir / ".env")

try:
    from models import Candidate
except ImportError:
    from backend.models import Candidate

try:
    from prompts import SEARCH_PROMPT, SINGLE_RESUME_PROMPT
except ImportError:
    from backend.prompts import SEARCH_PROMPT, SINGLE_RESUME_PROMPT

try:
    from ingest import extract_text_from_pdf, build_tree, compress_tree
except ImportError:
    from backend.ingest import extract_text_from_pdf, build_tree, compress_tree

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if GROQ_AVAILABLE and GROQ_API_KEY:
    groq_client = Groq(api_key=GROQ_API_KEY)
else:
    groq_client = None

# Configuration - optimized for free tier
BATCH_SIZE = 8
RESULTS_LIMIT = 5
MAX_RETRIES = 3
BASE_RETRY_DELAY = 2.0  # seconds
REQUEST_DELAY = 1.5  # seconds between requests

executor = ThreadPoolExecutor(max_workers=2)

def compress_trees_for_prompt(candidates: list) -> tuple:
    """Format candidates for prompt"""
    formatted = ""
    token_estimate = 0
    
    for i, candidate in enumerate(candidates, 1):
        try:
            tree = json.loads(candidate.tree_compressed) if candidate.tree_compressed else []
        except:
            tree = []
        
        candidate_block = f"\nCANDIDATE {i}: {candidate.name} (ID: {candidate.id})\n"
        candidate_block += f"Category: {candidate.category}\n"
        candidate_block += f"Tree: {json.dumps(tree)}\n"
        candidate_block += "---\n"
        
        formatted += candidate_block
        token_estimate += len(candidate_block) / 1.3
    
    return formatted, int(token_estimate)

def search_batch_with_retry(batch_num: int, query: str, candidates_batch: list, retry_count: int = 0) -> dict:
    """
    Search a batch with exponential backoff retry logic
    Handles rate limiting gracefully
    """
    if not groq_client:
        return {"batch_num": batch_num, "candidates": []}
    
    try:
        # Format trees
        all_trees, token_count = compress_trees_for_prompt(candidates_batch)
        
        # Build prompt
        prompt = f"""You are an expert senior recruiter with 20 years of experience.

Recruiter Query: {query}

You have {len(candidates_batch)} candidate resumes below.

ROUTING RULES:
- Skills → check Skills/Projects
- Experience → check Experience (years, company, tech)
- Domain → check Experience for domain mentions
- Leadership → check for "led", "managed"
- Education → check Education node

RESUME TREES:
{all_trees}

Return TOP 3 matches from this batch.
CRITICAL: Return ONLY valid JSON:
{{
  "candidates": [
    {{"candidate_id": 1, "name": "John", "category": "IT", "match_score": 85, "explanation": "reason"}}
  ]
}}"""
        
        # Call Groq with retry logic
        start_time = time.time()
        
        try:
            response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a recruiter. Return ONLY valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            latency_ms = (time.time() - start_time) * 1000
            response_text = response.choices[0].message.content
            result = json.loads(response_text)
            
            return {
                "batch_num": batch_num,
                "candidates": result.get("candidates", []),
                "latency_ms": latency_ms,
                "batch_size": len(candidates_batch),
                "retries": retry_count
            }
            
        except Exception as api_error:
            error_msg = str(api_error)
            
            # Check if it's a rate limit error
            if "429" in error_msg or "rate_limit" in error_msg.lower():
                if retry_count < MAX_RETRIES:
                    # Exponential backoff
                    wait_time = BASE_RETRY_DELAY * (2 ** retry_count)
                    print(f"    ⏳ Rate limited. Waiting {wait_time:.1f}s before retry {retry_count+1}/{MAX_RETRIES}...")
                    time.sleep(wait_time)
                    return search_batch_with_retry(batch_num, query, candidates_batch, retry_count + 1)
                else:
                    return {"batch_num": batch_num, "candidates": [], "retries": retry_count, "rate_limited": True}
            else:
                # Other error
                return {"batch_num": batch_num, "candidates": [], "error": error_msg[:100]}
                
    except Exception as e:
        return {"batch_num": batch_num, "candidates": [], "error": str(e)[:100]}

async def search_batch_async(batch_num: int, query: str, candidates_batch: list, delay_before: float) -> dict:
    """Async wrapper with pre-request delay"""
    # Rate limiting: space out requests
    await asyncio.sleep(delay_before)
    
    # Run in thread pool
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        executor,
        search_batch_with_retry,
        batch_num,
        query,
        candidates_batch
    )
    
    return result

async def search_all_batches_smart(query: str, all_candidates: list) -> list:
    """
    Search all batches with smart sequencing to avoid rate limits
    Uses async for I/O efficiency but staggers requests intelligently
    """
    # Create batches
    batches = []
    for i in range(0, len(all_candidates), BATCH_SIZE):
        batch = all_candidates[i:i + BATCH_SIZE]
        batches.append(batch)
    
    total_batches = len(batches)
    
    print(f"\n🚀 SMART RATE-LIMITED SEARCH")
    print(f"📊 Total batches: {total_batches}")
    print(f"⚙️  Rate limit strategy: Staggered with exponential backoff")
    print(f"⏱️  Request delay: {REQUEST_DELAY}s between batches\n")
    
    # Create tasks with spacing
    tasks = []
    for batch_num, batch in enumerate(batches, 1):
        # Stagger batch starts
        delay_before = REQUEST_DELAY * (batch_num - 1)
        
        task = search_batch_async(
            batch_num,
            query,
            batch,
            delay_before
        )
        tasks.append(task)
    
    # Execute sequentially to avoid hammer rate limiting
    results = await asyncio.gather(*tasks)
    
    return results

def search_candidates(query: str, limit: int, db_session: Session) -> dict:
    """Main search function with smart rate limiting"""
    try:
        if not groq_client:
            return {"candidates": [], "search_reasoning": "Groq not configured"}
        
        print(f"\n🔍 SEARCHING: {query}")
        
        # Fetch candidates
        all_candidates = db_session.query(Candidate).all()
        if not all_candidates:
            return {"candidates": [], "search_reasoning": "No candidates"}
        
        print(f"📊 Total candidates: {len(all_candidates)}")
        
        # Run smart async search
        start_time = time.time()
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        all_batch_results = loop.run_until_complete(
            search_all_batches_smart(query, all_candidates)
        )
        
        total_time = (time.time() - start_time) * 1000
        
        # Process results
        print(f"\n📊 COMBINING RESULTS")
        combined_candidates = []
        batch_details = []
        rate_limited_count = 0
        
        for result in all_batch_results:
            batch_num = result.get("batch_num")
            batch_size = result.get("batch_size", 0)
            latency = result.get("latency_ms", 0)
            retries = result.get("retries", 0)
            candidates = result.get("candidates", [])
            error = result.get("error")
            rate_limited = result.get("rate_limited", False)
            
            if rate_limited:
                print(f"[BATCH {batch_num}] ⚠️  Rate limited (exhausted retries)")
                rate_limited_count += 1
            elif error:
                print(f"[BATCH {batch_num}] ❌ Error: {error}")
            else:
                retry_str = f" (+{retries} retries)" if retries > 0 else ""
                print(f"[BATCH {batch_num}] ✅ {len(candidates)} matches ({latency:.0f}ms){retry_str}")
                batch_details.append({
                    "batch": batch_num,
                    "size": batch_size,
                    "matches": len(candidates),
                    "latency_ms": latency,
                    "retries": retries
                })
            
            combined_candidates.extend(candidates)
        
        # Rank and deduplicate
        combined_candidates.sort(key=lambda x: x.get("match_score", 0), reverse=True)
        
        seen_ids = set()
        unique_results = []
        for candidate in combined_candidates:
            cand_id = candidate.get("candidate_id")
            if cand_id not in seen_ids:
                seen_ids.add(cand_id)
                unique_results.append(candidate)
        
        final_results = unique_results[:limit]
        
        # Generate reasoning
        total_matches = len(unique_results)
        reasoning = f"✅ Searched {len(all_candidates)} candidates in {len(batch_details)} batches "
        if rate_limited_count > 0:
            reasoning += f"({rate_limited_count} rate-limited). "
        reasoning += f"Found {total_matches} matches, returning top {len(final_results)}. Latency: {total_time:.0f}ms"
        
        print(f"\n⏱️  TOTAL LATENCY: {total_time:.0f}ms")
        print(f"🏆 FINAL RESULTS: {len(final_results)} candidates")
        
        return {
            "candidates": final_results,
            "search_reasoning": reasoning,
            "latency_ms": total_time,
            "batch_details": batch_details
        }
        
    except Exception as e:
        print(f"❌ Search error: {e}")
        import traceback
        traceback.print_exc()
        return {"candidates": [], "search_reasoning": f"Error: {str(e)}"}

def analyze_single_resume(pdf_path: str, question: str) -> dict:
    """Analyze single resume"""
    try:
        if not groq_client:
            return {
                "answer": "Groq not configured",
                "relevant_sections": [],
                "recommendation": "Error",
                "reasoning": "API not configured"
            }
        
        print(f"\n📋 Analyzing resume...")
        
        text = extract_text_from_pdf(pdf_path)
        tree_data = build_tree(text, "Candidate")
        compressed_tree = compress_tree(tree_data)
        tree_str = json.dumps(compressed_tree, indent=2)
        
        prompt = SINGLE_RESUME_PROMPT.format(tree=tree_str, question=question)
        
        print(f"   💭 Analyzing with Groq...")
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a recruiter. Return valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1500,
            response_format={"type": "json_object"}
        )
        
        response_text = response.choices[0].message.content
        result = json.loads(response_text)
        
        print(f"   ✅ Analysis complete")
        return result
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return {
            "answer": f"Error: {str(e)}",
            "relevant_sections": [],
            "recommendation": "Error",
            "reasoning": str(e)
        }
