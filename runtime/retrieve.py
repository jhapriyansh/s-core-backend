from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from runtime.expand import expand_topics
from db.chroma import query_collection
from ingestion.embed import embed, embed_query
from config import PACE_CONFIG

# ─────────────────────────────────────────────────────────────
# Data Classes
# ─────────────────────────────────────────────────────────────

@dataclass
class RetrievalResult:
    """Result of retrieval operation"""
    documents: List[str]
    scores: List[float]  # Similarity scores
    total_found: int
    topics_searched: List[str]

# ─────────────────────────────────────────────────────────────
# Retrieval Functions
# ─────────────────────────────────────────────────────────────

def get_retrieval_depth(pace: str) -> int:
    """Get number of documents to retrieve based on pace"""
    config = PACE_CONFIG.get(pace, PACE_CONFIG["medium"])
    return config.get("depth", 12)

def retrieve(
    user_id: str,
    deck_id: str,
    query_text: str,
    pace: str = "medium",
    expand: bool = True
) -> RetrievalResult:
    """
    Retrieve relevant documents with hierarchical topic expansion.
    
    Process:
    1. Embed query
    2. Query main collection
    3. Expand to subtopics
    4. Query for subtopics
    5. Deduplicate and rank
    """
    n_results = get_retrieval_depth(pace)
    query_vec = embed_query(query_text)
    
    # Main query
    results = query_collection(
        user_id=user_id,
        deck_id=deck_id,
        query_embedding=query_vec,
        n_results=n_results
    )
    
    documents = results["documents"]
    distances = results["distances"]
    topics_searched = [query_text]
    
    # Hierarchical expansion
    if expand:
        subtopics = expand_topics(query_text)
        topics_searched.extend(subtopics)
        
        # Query for each subtopic
        for subtopic in subtopics[:3]:  # Limit to top 3 subtopics
            subtopic_vec = embed_query(subtopic)
            sub_results = query_collection(
                user_id=user_id,
                deck_id=deck_id,
                query_embedding=subtopic_vec,
                n_results=3
            )
            
            # Add non-duplicate documents
            for doc, dist in zip(sub_results["documents"], sub_results["distances"]):
                if doc not in documents:
                    documents.append(doc)
                    distances.append(dist)
    
    # Convert distances to similarity scores (ChromaDB returns L2 distance)
    # Lower distance = higher similarity
    scores = [1 / (1 + d) for d in distances]
    
    return RetrievalResult(
        documents=documents,
        scores=scores,
        total_found=len(documents),
        topics_searched=topics_searched
    )

def retrieve_legacy(collection, query_vec, pace, query_text) -> List[str]:
    """
    Legacy interface for backward compatibility.
    Works with collection objects directly.
    """
    n_results = get_retrieval_depth(pace)
    results = collection.query(query_embeddings=[query_vec], n_results=n_results)
    docs = results["documents"][0] if results["documents"] else []
    
    # Expand topics
    subtopics = expand_topics(query_text)
    for subtopic in subtopics[:3]:
        sub_vec = embed(subtopic)
        sub_results = collection.query(query_embeddings=[sub_vec], n_results=3)
        if sub_results["documents"]:
            for doc in sub_results["documents"][0]:
                if doc not in docs:
                    docs.append(doc)
    
    return docs


def retrieve_for_topic(
    user_id: str,
    deck_id: str,
    topic: str,
    n_results: int = 8
) -> str:
    """
    Retrieve content specifically for a syllabus topic.
    Returns concatenated text suitable for teaching.
    
    Used by the auto-teaching module.
    """
    query_vec = embed_query(topic)
    
    # Query for main topic
    results = query_collection(
        user_id=user_id,
        deck_id=deck_id,
        query_embedding=query_vec,
        n_results=n_results
    )
    
    documents = results["documents"]
    
    # Expand to subtopics for better coverage
    subtopics = expand_topics(topic)
    for subtopic in subtopics[:2]:
        sub_vec = embed_query(subtopic)
        sub_results = query_collection(
            user_id=user_id,
            deck_id=deck_id,
            query_embedding=sub_vec,
            n_results=3
        )
        for doc in sub_results["documents"]:
            if doc not in documents:
                documents.append(doc)
    
    # Concatenate and return
    if not documents:
        return ""
    
    return "\n\n---\n\n".join(documents[:12])  # Limit to 12 chunks
