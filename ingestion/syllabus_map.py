from typing import List, Tuple, Optional
from dataclasses import dataclass
import json

from groq import Groq
from config import get_groq_key, GROQ_MODEL

# ─────────────────────────────────────────────────────────────
# Data Classes
# ─────────────────────────────────────────────────────────────

@dataclass
class MappedChunk:
    """A chunk mapped to syllabus topics"""
    content: str
    topics: List[str]
    relevance_score: float  # 0-1
    source_file: str

# ─────────────────────────────────────────────────────────────
# Syllabus Parsing
# ─────────────────────────────────────────────────────────────

def parse_syllabus(syllabus: str) -> List[str]:
    """
    Parse syllabus text into individual topics.
    Returns a list of topic strings.
    """
    client = Groq(api_key=get_groq_key())
    
    prompt = f"""Parse this syllabus into individual topics/subtopics.

Syllabus:
{syllabus}

IMPORTANT RULES:
1. If the syllabus is vague or just a broad topic name (e.g. "Scheduling", "Memory Management"),
   expand it into the common academic sub-topics a university course would cover.
   For example "Scheduling" → ["CPU Scheduling Overview", "First Come First Served (FCFS)", "Shortest Job First (SJF)", "Priority Scheduling", "Round Robin (RR)", "Multilevel Queue Scheduling", "Multilevel Feedback Queue"]
2. If the syllabus already lists specific topics, parse them as-is with their subtopics.
3. Return at least 3 topics — never return a single-element list for a broad subject.

Return as a JSON array of topic strings.
Example: ["Topic 1", "Topic 1 - Subtopic A", "Topic 2", ...]

Return ONLY the JSON array, no other text.
"""

    try:
        res = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=2000
        )
        
        response = res.choices[0].message.content.strip()
        
        # Try to parse JSON
        # Handle cases where response might have markdown code blocks
        if response.startswith("```"):
            response = response.split("```")[1]
            if response.startswith("json"):
                response = response[4:]
        
        topics = json.loads(response)
        return topics if isinstance(topics, list) else []
        
    except Exception as e:
        print(f"Syllabus parsing failed: {e}")
        # Fallback: split by newlines
        return [line.strip() for line in syllabus.split('\n') if line.strip()]

# ─────────────────────────────────────────────────────────────
# Content to Syllabus Mapping
# ─────────────────────────────────────────────────────────────

def map_chunk_to_topics(chunk: str, syllabus_topics: List[str]) -> Tuple[List[str], float]:
    """
    Map a single chunk to relevant syllabus topics.
    
    Returns:
        Tuple of (matched_topics, relevance_score)
        If no topics match, returns ([], 0.0)
    """
    client = Groq(api_key=get_groq_key())
    
    topics_str = "\n".join(f"- {t}" for t in syllabus_topics)
    
    prompt = f"""Determine which syllabus topics this content relates to.

Syllabus Topics:
{topics_str}

Content:
{chunk}

Rules:
1. Only match topics that are DIRECTLY relevant
2. Content must substantially cover the topic
3. Incidental mentions don't count
4. Be strict - if unclear, don't match

Return a JSON object with:
- "topics": array of matched topic names (exact names from list)
- "relevance": number 0-1 indicating how relevant the content is
- "reason": brief explanation

If NO topics match, return: {{"topics": [], "relevance": 0, "reason": "Not related to syllabus"}}

Return ONLY the JSON object.
"""

    try:
        res = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=500
        )
        
        response = res.choices[0].message.content.strip()
        
        # Parse JSON
        if response.startswith("```"):
            response = response.split("```")[1]
            if response.startswith("json"):
                response = response[4:]
        
        result = json.loads(response)
        
        topics = result.get("topics", [])
        relevance = float(result.get("relevance", 0))
        
        return topics, relevance
        
    except Exception as e:
        print(f"Topic mapping failed: {e}")
        return [], 0.0

def map_to_syllabus(
    chunks: List[str],
    syllabus: str,
    source_file: str = "unknown",
    min_relevance: float = 0.3,
    syllabus_topics: Optional[List[str]] = None
) -> List[MappedChunk]:
    """
    Map all chunks to syllabus topics.
    Filters out chunks that don't match any topic.
    
    This is the core filter function that enforces:
    "syllabus = hard boundary"
    
    Args:
        chunks: List of text chunks
        syllabus: Raw syllabus text
        source_file: Source filename for metadata
        min_relevance: Minimum relevance score to keep chunk
        syllabus_topics: Pre-parsed topics (avoids redundant LLM call)
        
    Returns:
        List of MappedChunk objects that passed the filter
    """
    # Use pre-parsed topics if available, otherwise parse now
    if not syllabus_topics:
        syllabus_topics = parse_syllabus(syllabus)
    
    if not syllabus_topics:
        print("Warning: Could not parse syllabus topics")
        return []
    
    mapped_chunks = []
    filtered_count = 0
    
    for chunk in chunks:
        if not chunk or not chunk.strip():
            continue
            
        topics, relevance = map_chunk_to_topics(chunk, syllabus_topics)
        
        if topics and relevance >= min_relevance:
            mapped_chunks.append(MappedChunk(
                content=chunk,
                topics=topics,
                relevance_score=relevance,
                source_file=source_file
            ))
        else:
            filtered_count += 1
    
    print(f"✓ Syllabus mapping: {len(mapped_chunks)} kept, {filtered_count} filtered out")
    
    return mapped_chunks

# ─────────────────────────────────────────────────────────────
# Topic Coverage Analysis
# ─────────────────────────────────────────────────────────────

def analyze_topic_coverage(
    mapped_chunks: List[MappedChunk],
    syllabus_topics: List[str]
) -> dict:
    """
    Analyze how well the uploaded material covers the syllabus.
    
    Returns dict with:
        - covered_topics: topics with content
        - uncovered_topics: topics without content
        - coverage_ratio: 0-1
        - topic_chunk_counts: chunks per topic
    """
    topic_chunks = {topic: 0 for topic in syllabus_topics}
    
    for chunk in mapped_chunks:
        for topic in chunk.topics:
            if topic in topic_chunks:
                topic_chunks[topic] += 1
    
    covered = [t for t, count in topic_chunks.items() if count > 0]
    uncovered = [t for t, count in topic_chunks.items() if count == 0]
    
    return {
        "covered_topics": covered,
        "uncovered_topics": uncovered,
        "coverage_ratio": len(covered) / len(syllabus_topics) if syllabus_topics else 0,
        "topic_chunk_counts": topic_chunks
    }

# ─────────────────────────────────────────────────────────────
# Simple Interface (backward compatibility)
# ─────────────────────────────────────────────────────────────

def filter_by_syllabus(text: str, syllabus: str, syllabus_topics: Optional[List[str]] = None) -> Optional[str]:
    """
    Simple interface: check if text is relevant to syllabus.
    Returns the text if relevant, None if not.
    """
    mapped = map_to_syllabus([text], syllabus, syllabus_topics=syllabus_topics)
    return mapped[0].content if mapped else None
