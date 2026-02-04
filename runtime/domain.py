"""
Domain Guard Module for S-Core
Detects when queries fall outside syllabus scope.

Handles topic drift gracefully.
"""

from typing import Tuple, List

from ingestion.embed import embed, cosine_similarity
from groq import Groq
from config import get_groq_key, GROQ_MODEL

# ─────────────────────────────────────────────────────────────
# Thresholds
# ─────────────────────────────────────────────────────────────

# Minimum similarity to syllabus for query to be "in scope"
DOMAIN_THRESHOLD = 0.30  # Lowered from 0.35 for better recall

# Minimum similarity to any individual topic
TOPIC_THRESHOLD = 0.40

# ─────────────────────────────────────────────────────────────
# Domain Check Functions
# ─────────────────────────────────────────────────────────────

def domain_guard(query: str, syllabus: str, syllabus_topics: List[str] = None) -> bool:
    """
    Check if query is within syllabus scope.
    
    Args:
        query: User's query
        syllabus: Syllabus text
        syllabus_topics: List of individual syllabus topics
        
    Returns:
        True if query is in scope, False otherwise
    """
    query_vec = embed(query)
    syllabus_vec = embed(syllabus)
    
    similarity = cosine_similarity(query_vec, syllabus_vec)
    
    # Check against individual topics for better accuracy
    if syllabus_topics:
        for topic in syllabus_topics:
            topic_vec = embed(topic)
            topic_sim = cosine_similarity(query_vec, topic_vec)
            if topic_sim >= TOPIC_THRESHOLD:
                return True  # Matches a specific topic
    
    return similarity >= DOMAIN_THRESHOLD

def domain_guard_detailed(
    query: str,
    syllabus: str,
    syllabus_topics: List[str] = None
) -> Tuple[bool, float, str]:
    """
    Detailed domain check with explanation.
    
    Returns:
        Tuple of (is_in_scope, similarity, explanation)
    """
    query_vec = embed(query)
    syllabus_vec = embed(syllabus)
    
    syllabus_similarity = cosine_similarity(query_vec, syllabus_vec)
    
    # Check against individual topics for better accuracy
    best_topic_match = None
    best_topic_score = 0.0
    
    if syllabus_topics:
        for topic in syllabus_topics:
            topic_vec = embed(topic)
            topic_sim = cosine_similarity(query_vec, topic_vec)
            if topic_sim > best_topic_score:
                best_topic_score = topic_sim
                best_topic_match = topic
    
    # Use the higher of syllabus similarity or best topic match
    effective_similarity = max(syllabus_similarity, best_topic_score)
    
    # Determine if in scope using either threshold
    is_in_scope = (syllabus_similarity >= DOMAIN_THRESHOLD or 
                   best_topic_score >= TOPIC_THRESHOLD)
    
    if is_in_scope:
        explanation = f"Query is within syllabus scope."
        if best_topic_match:
            explanation += f" Most relevant topic: {best_topic_match}"
        return True, effective_similarity, explanation
    else:
        return False, effective_similarity, "This topic is not in the scope of your current syllabus."

def generate_out_of_scope_response(query: str, syllabus: str) -> str:
    """
    Generate a helpful response for out-of-scope queries.
    Short, helpful, but stops early.
    """
    client = Groq(api_key=get_groq_key())
    
    prompt = f"""The user asked about a topic outside their study syllabus.

User's syllabus covers:
{syllabus[:500]}...

User asked:
{query}

Provide a BRIEF (2-3 sentences) helpful response that:
1. Acknowledges this is outside their syllabus
2. Gives a one-sentence definition/overview
3. Suggests focusing on their syllabus topics

Keep it SHORT and HELPFUL.
"""
    
    try:
        res = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=200
        )
        return res.choices[0].message.content
        
    except Exception as e:
        return f"This topic is not in your current syllabus scope."
