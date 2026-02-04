"""
Embedding Module for S-Core
Converts text to semantic vectors using sentence transformers.
"""

from typing import List, Union
from sentence_transformers import SentenceTransformer

from config import EMBEDDING_MODEL

# ─────────────────────────────────────────────────────────────
# Model Loading (Singleton)
# ─────────────────────────────────────────────────────────────

_model = None

def get_model() -> SentenceTransformer:
    """Get embedding model (lazy loading singleton)"""
    global _model
    if _model is None:
        print(f"Loading embedding model: {EMBEDDING_MODEL}")
        _model = SentenceTransformer(EMBEDDING_MODEL)
        print("✓ Embedding model loaded")
    return _model

# ─────────────────────────────────────────────────────────────
# Embedding Functions
# ─────────────────────────────────────────────────────────────

def embed(text: str) -> List[float]:
    """
    Convert a single text to embedding vector.
    
    Args:
        text: Input text
        
    Returns:
        Embedding as list of floats
    """
    model = get_model()
    return model.encode(text).tolist()

def embed_batch(texts: List[str], batch_size: int = 32) -> List[List[float]]:
    """
    Convert multiple texts to embeddings (more efficient).
    
    Args:
        texts: List of input texts
        batch_size: Batch size for encoding
        
    Returns:
        List of embeddings
    """
    model = get_model()
    embeddings = model.encode(texts, batch_size=batch_size, show_progress_bar=True)
    return [e.tolist() for e in embeddings]

def embed_query(query: str) -> List[float]:
    """
    Embed a query (same as embed, but semantically distinct).
    In some models, query embedding differs from document embedding.
    """
    return embed(query)

# ─────────────────────────────────────────────────────────────
# Similarity Functions
# ─────────────────────────────────────────────────────────────

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors"""
    from sentence_transformers import util
    import torch
    
    t1 = torch.tensor(vec1)
    t2 = torch.tensor(vec2)
    
    return util.cos_sim(t1, t2)[0][0].item()

def semantic_similarity(text1: str, text2: str) -> float:
    """Calculate semantic similarity between two texts"""
    vec1 = embed(text1)
    vec2 = embed(text2)
    return cosine_similarity(vec1, vec2)
