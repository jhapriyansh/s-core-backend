"""
Learning Pace Module for S-Core
Controls explanation depth and theory/practice ratio.

Pace does NOT affect:
- Ingestion
- Embeddings  
- Retrieval logic

Pace DOES affect:
- How Groq explains
- How many questions are generated
- How much detail is shown
"""

from typing import Dict, Any
from config import PACE_CONFIG

# ─────────────────────────────────────────────────────────────
# Pace Configuration
# ─────────────────────────────────────────────────────────────

# Pace settings table:
# Pace       | Theory | Practice | Description
# -----------|--------|----------|------------------
# Slow/Deep  |  70%   |   30%    | Deep learning mode
# Medium     |  50%   |   50%    | Balanced mode
# Fast       |  30%   |   70%    | Revision mode

def pace_config(pace: str) -> Dict[str, Any]:
    """
    Get configuration for a pace setting.
    
    Args:
        pace: 'slow', 'medium', or 'fast'
        
    Returns:
        Configuration dict with theory/practice ratios and settings
    """
    return PACE_CONFIG.get(pace, PACE_CONFIG["medium"])

def get_theory_ratio(pace: str) -> float:
    """Get theory ratio for pace (0.0 to 1.0)"""
    config = pace_config(pace)
    return config.get("theory", 0.5)

def get_practice_ratio(pace: str) -> float:
    """Get practice ratio for pace (0.0 to 1.0)"""
    config = pace_config(pace)
    return config.get("practice", 0.5)

def get_retrieval_depth(pace: str) -> int:
    """Get number of documents to retrieve for pace"""
    config = pace_config(pace)
    return config.get("depth", 12)

def get_pace_description(pace: str) -> str:
    """Get human-readable description of pace"""
    config = pace_config(pace)
    return config.get("description", "Balanced mode")

# ─────────────────────────────────────────────────────────────
# Pace-Aware Formatting
# ─────────────────────────────────────────────────────────────

def get_question_count(pace: str) -> Dict[str, int]:
    """
    Get number of each question type to generate for pace.
    """
    counts = {
        "slow": {"conceptual": 1, "application": 1, "numerical": 1},
        "medium": {"conceptual": 2, "application": 2, "numerical": 1},
        "fast": {"conceptual": 2, "application": 3, "numerical": 2}
    }
    return counts.get(pace, counts["medium"])

def get_max_tokens(pace: str) -> int:
    """
    Get max tokens for response generation based on pace.
    """
    tokens = {
        "slow": 3000,   # Detailed explanations
        "medium": 2000, # Balanced
        "fast": 1500    # Concise
    }
    return tokens.get(pace, 2000)

def validate_pace(pace: str) -> str:
    """
    Validate and normalize pace value.
    Returns 'medium' for invalid values.
    """
    valid_paces = ["slow", "medium", "fast"]
    pace = pace.lower().strip()
    return pace if pace in valid_paces else "medium"
