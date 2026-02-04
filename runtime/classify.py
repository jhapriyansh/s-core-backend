"""
Query Classification Module for S-Core
Classifies user intent and extracts topic information.
"""

from typing import Tuple
from dataclasses import dataclass
import json

from groq import Groq
from config import get_groq_key, GROQ_MODEL

# ─────────────────────────────────────────────────────────────
# Data Classes
# ─────────────────────────────────────────────────────────────

@dataclass
class QueryClassification:
    """Classification result for a query"""
    intent: str  # explain, practice, revise, question
    topic: str   # Main topic extracted
    subtopics: list  # Related subtopics
    complexity: str  # simple, moderate, complex

# ─────────────────────────────────────────────────────────────
# Intent Classification
# ─────────────────────────────────────────────────────────────

def classify(query: str) -> str:
    """
    Simple intent classification.
    Returns: explain, practice, revise, or question
    """
    client = Groq(api_key=get_groq_key())
    
    prompt = f"""Classify the user's intent.

Query: {query}

Intents:
- explain: User wants explanation/theory
- practice: User wants practice questions
- revise: User wants quick review/summary
- question: User is asking a specific question

Return ONLY one word: explain, practice, revise, or question.
"""
    
    try:
        res = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=10
        )
        intent = res.choices[0].message.content.strip().lower()
        
        # Validate intent
        valid_intents = ["explain", "practice", "revise", "question"]
        return intent if intent in valid_intents else "explain"
        
    except Exception as e:
        print(f"Classification failed: {e}")
        return "explain"

def classify_detailed(query: str) -> QueryClassification:
    """
    Detailed classification with topic extraction.
    """
    client = Groq(api_key=get_groq_key())
    
    prompt = f"""Analyze this query and extract information.

Query: {query}

Return a JSON object with:
- "intent": one of [explain, practice, revise, question]
- "topic": main topic (1-3 words)
- "subtopics": array of related subtopics
- "complexity": one of [simple, moderate, complex]

Return ONLY the JSON object.
"""
    
    try:
        res = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=200
        )
        
        response = res.choices[0].message.content.strip()
        
        # Parse JSON
        if response.startswith("```"):
            response = response.split("```")[1]
            if response.startswith("json"):
                response = response[4:]
        
        data = json.loads(response)
        
        return QueryClassification(
            intent=data.get("intent", "explain"),
            topic=data.get("topic", ""),
            subtopics=data.get("subtopics", []),
            complexity=data.get("complexity", "moderate")
        )
        
    except Exception as e:
        print(f"Detailed classification failed: {e}")
        return QueryClassification(
            intent="explain",
            topic=query[:50],
            subtopics=[],
            complexity="moderate"
        )
