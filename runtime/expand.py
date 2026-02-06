from typing import List

from groq import Groq
from config import get_groq_key, GROQ_MODEL

# ─────────────────────────────────────────────────────────────
# Topic Expansion
# ─────────────────────────────────────────────────────────────

def expand_topics(topic: str, max_subtopics: int = 5) -> List[str]:
    """
    Expand a topic into related subtopics.
    
    Used for hierarchical semantic retrieval - 
    when retrieving for "Deadlock", also retrieve for
    "Mutual Exclusion", "Critical Section", etc.
    
    Args:
        topic: Main topic to expand
        max_subtopics: Maximum number of subtopics to return
        
    Returns:
        List of subtopic strings
    """
    client = Groq(api_key=get_groq_key())
    
    prompt = f"""List the most important subtopics or related concepts for this topic.

Topic: {topic}

Rules:
1. Return only subtopic names, no explanations
2. Focus on fundamental/prerequisite concepts
3. Include closely related topics
4. Maximum {max_subtopics} subtopics
5. Return as comma-separated list

Example for "Deadlock":
Mutual Exclusion, Critical Section, Race Condition, Deadlock Prevention, Resource Allocation

Return ONLY the comma-separated list.
"""
    
    try:
        res = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=100
        )
        
        output = res.choices[0].message.content.strip()
        
        # Clean and parse
        subtopics = [t.strip() for t in output.split(",") if t.strip()]
        
        # Limit to max
        return subtopics[:max_subtopics]
        
    except Exception as e:
        print(f"Topic expansion failed: {e}")
        return []

def get_topic_hierarchy(topic: str, depth: int = 2) -> dict:
    """
    Build a topic hierarchy tree.
    
    Args:
        topic: Root topic
        depth: How deep to expand (default 2 levels)
        
    Returns:
        Dict with topic tree structure
    """
    hierarchy = {
        "topic": topic,
        "subtopics": []
    }
    
    if depth <= 0:
        return hierarchy
    
    subtopics = expand_topics(topic, max_subtopics=3)
    
    for sub in subtopics:
        if depth > 1:
            hierarchy["subtopics"].append(
                get_topic_hierarchy(sub, depth - 1)
            )
        else:
            hierarchy["subtopics"].append({"topic": sub, "subtopics": []})
    
    return hierarchy
