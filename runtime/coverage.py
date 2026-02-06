from typing import Tuple, List
from ingestion.embed import embed, cosine_similarity

# ─────────────────────────────────────────────────────────────
# Coverage Thresholds
# ─────────────────────────────────────────────────────────────

# Minimum semantic similarity for "sufficient" coverage
MIN_SIMILARITY_THRESHOLD = 0.5

# Minimum number of keyword hits
MIN_KEYWORD_HITS = 2

# Minimum documents for good coverage
MIN_DOCUMENTS = 2

# ─────────────────────────────────────────────────────────────
# Coverage Check Functions
# ─────────────────────────────────────────────────────────────

def coverage_check(docs: List[str], query: str) -> bool:
    """
    Check if retrieved documents sufficiently cover the query.
    
    Uses multiple heuristics:
    1. Keyword matching
    2. Semantic similarity
    3. Document count
    
    Returns:
        True if coverage is sufficient, False otherwise
    """
    if not docs:
        return False
    
    # Check 1: Minimum documents
    if len(docs) < MIN_DOCUMENTS:
        return False
    
    # Check 2: Keyword coverage
    joined = " ".join(docs).lower()
    keywords = [w.lower() for w in query.split() if len(w) > 3]
    keyword_hits = sum(1 for k in keywords if k in joined)
    
    if keyword_hits < MIN_KEYWORD_HITS:
        return False
    
    # Check 3: Semantic similarity
    query_vec = embed(query)
    context_vec = embed(" ".join(docs[:3]))  # Use top 3 docs
    similarity = cosine_similarity(query_vec, context_vec)
    
    return similarity >= MIN_SIMILARITY_THRESHOLD

def coverage_check_detailed(
    docs: List[str],
    scores: List[float],
    query: str
) -> Tuple[bool, float, str]:
    """
    Detailed coverage check with explanation.
    
    Returns:
        Tuple of (is_sufficient, confidence, reason)
    """
    if not docs:
        return False, 0.0, "No documents found for this topic."
    
    if len(docs) < MIN_DOCUMENTS:
        return False, 0.2, "Very limited material found for this topic."
    
    # Calculate coverage metrics
    joined = " ".join(docs).lower()
    keywords = [w.lower() for w in query.split() if len(w) > 3]
    keyword_hits = sum(1 for k in keywords if k in joined)
    keyword_ratio = keyword_hits / len(keywords) if keywords else 0
    
    # Average similarity score
    avg_score = sum(scores[:5]) / min(len(scores), 5)
    
    # Combine into confidence
    confidence = (keyword_ratio * 0.4) + (avg_score * 0.6)
    
    if confidence >= 0.5:
        return True, confidence, "Material sufficiently covers this topic."
    elif confidence >= 0.3:
        return True, confidence, "Partial coverage. Some aspects may be missing."
    else:
        return False, confidence, "Your uploaded material does not sufficiently cover this topic."

def get_coverage_warning(confidence: float) -> str:
    """
    Get appropriate warning message based on coverage confidence.
    """
    if confidence >= 0.7:
        return ""
    elif confidence >= 0.5:
        return "⚠️ Some aspects of this topic may not be fully covered in your material."
    elif confidence >= 0.3:
        return "⚠️ Your uploaded material has limited coverage of this topic."
    else:
        return "⚠️ This topic is not well covered in your uploaded material. Consider uploading more relevant content."
