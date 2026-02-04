"""
Internet Enhancement Module for S-Core
Temporary oracle for out-of-scope or insufficient coverage.

Key principle: Internet = temporary oracle, Chroma = ground truth
- Never stored
- Never embedded  
- Never mixed with Chroma
- Always labeled [Internet Enhanced]
"""

from typing import Optional, List
from dataclasses import dataclass

from duckduckgo_search import DDGS
from groq import Groq
from config import get_groq_key, GROQ_MODEL, WHITELIST_DOMAINS

# ─────────────────────────────────────────────────────────────
# Data Classes
# ─────────────────────────────────────────────────────────────

@dataclass
class InternetResult:
    """Result from internet enhancement"""
    content: str
    sources: List[str]
    is_reliable: bool

# ─────────────────────────────────────────────────────────────
# Search Functions
# ─────────────────────────────────────────────────────────────

def search_internet(query: str, max_results: int = 10) -> List[dict]:
    """
    Search internet using DuckDuckGo.
    Filters to whitelisted domains only.
    """
    results = []
    
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                # Filter to whitelisted domains
                for domain in WHITELIST_DOMAINS:
                    if domain in r.get("href", ""):
                        results.append({
                            "title": r.get("title", ""),
                            "body": r.get("body", ""),
                            "url": r.get("href", ""),
                            "domain": domain
                        })
                        break
    except Exception as e:
        print(f"Internet search failed: {e}")
    
    return results

def summarize_results(results: List[dict], query: str) -> str:
    """
    Summarize search results using LLM.
    """
    if not results:
        return "No reliable external information found."
    
    client = Groq(api_key=get_groq_key())
    
    context = "\n\n".join([
        f"Source: {r['domain']}\n{r['body']}"
        for r in results
    ])
    
    prompt = f"""Summarize this information clearly and concisely.

User's question: {query}

Search results:
{context}

Rules:
1. Only summarize what is present in the results
2. Do NOT add any external knowledge
3. Be concise and educational
4. Focus on answering the user's question
5. Keep it brief - this is supplementary information
"""
    
    try:
        res = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500
        )
        return res.choices[0].message.content
        
    except Exception as e:
        # Fallback to raw snippets
        return "\n".join([r["body"] for r in results[:3]])

# ─────────────────────────────────────────────────────────────
# Main Interface
# ─────────────────────────────────────────────────────────────

def internet_oracle(query: str) -> str:
    """
    Main interface for internet enhancement.
    
    Triggers:
    - Local similarity score is low
    - Prerequisite missing
    - Topic outside syllabus
    
    Returns summarized content with [Internet Enhanced] label.
    NEVER stores the result.
    """
    results = search_internet(query)
    
    if not results:
        return "No reliable external information found for this topic."
    
    summary = summarize_results(results, query)
    
    # Get source domains for citation
    sources = list(set([r["domain"] for r in results]))
    
    return summary

def internet_oracle_detailed(query: str) -> InternetResult:
    """
    Detailed internet enhancement with metadata.
    """
    results = search_internet(query)
    
    if not results:
        return InternetResult(
            content="No reliable external information found.",
            sources=[],
            is_reliable=False
        )
    
    summary = summarize_results(results, query)
    sources = list(set([r["domain"] for r in results]))
    
    return InternetResult(
        content=summary,
        sources=sources,
        is_reliable=len(results) >= 2
    )

def format_internet_response(content: str, sources: List[str] = None) -> str:
    """
    Format internet-enhanced response with proper labeling.
    """
    response = [
        "🌐 [Internet Enhanced]",
        "="*50,
        "This information is from external sources and is NOT stored.",
        "",
        content,
        ""
    ]
    
    if sources:
        response.append(f"📚 Sources: {', '.join(sources)}")
    
    response.append("="*50)
    
    return "\n".join(response)
