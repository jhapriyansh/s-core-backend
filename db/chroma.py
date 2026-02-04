"""
ChromaDB Vector Storage for S-Core
Manages isolated vector spaces per deck.

Key principle: One vector space per user per deck
- No cross-user leakage
- No cross-deck contamination
"""

import os
from typing import Optional, List, Dict, Any
import chromadb
from chromadb.config import Settings

from config import get_chroma_path

# ─────────────────────────────────────────────────────────────
# ChromaDB Client Management
# ─────────────────────────────────────────────────────────────

_client: Optional[chromadb.PersistentClient] = None

def get_chroma_client() -> chromadb.PersistentClient:
    """Get persistent ChromaDB client (singleton)"""
    global _client
    if _client is None:
        chroma_path = get_chroma_path()
        os.makedirs(chroma_path, exist_ok=True)
        _client = chromadb.PersistentClient(
            path=chroma_path,
            settings=Settings(anonymized_telemetry=False)
        )
    return _client

def get_ephemeral_client() -> chromadb.Client:
    """Get in-memory client for testing"""
    return chromadb.Client()

# ─────────────────────────────────────────────────────────────
# Deck Collection Management
# ─────────────────────────────────────────────────────────────

def get_deck_collection_name(user_id: str, deck_id: str) -> str:
    """
    Generate unique collection name for a deck.
    Ensures complete isolation between users and decks.
    """
    # ChromaDB collection names must be 3-63 chars, alphanumeric + underscores
    return f"deck_{user_id[:8]}_{deck_id[:8]}"

def get_collection(user_id: str, deck_id: str):
    """
    Get or create a ChromaDB collection for a deck.
    Each deck has its own isolated vector space.
    """
    client = get_chroma_client()
    collection_name = get_deck_collection_name(user_id, deck_id)
    
    return client.get_or_create_collection(
        name=collection_name,
        metadata={"user_id": user_id, "deck_id": deck_id}
    )

def delete_collection(user_id: str, deck_id: str) -> bool:
    """Delete a deck's collection (when deck is deleted)"""
    client = get_chroma_client()
    collection_name = get_deck_collection_name(user_id, deck_id)
    
    try:
        client.delete_collection(collection_name)
        return True
    except Exception:
        return False

# ─────────────────────────────────────────────────────────────
# Document Operations
# ─────────────────────────────────────────────────────────────

def add_documents(
    user_id: str,
    deck_id: str,
    documents: List[str],
    embeddings: List[List[float]],
    metadatas: Optional[List[Dict[str, Any]]] = None,
    ids: Optional[List[str]] = None
) -> int:
    """
    Add documents to a deck's collection.
    
    Args:
        user_id: Owner's user ID
        deck_id: Deck ID
        documents: List of text chunks
        embeddings: Corresponding embeddings
        metadatas: Optional metadata for each chunk
        ids: Optional custom IDs (auto-generated if not provided)
        
    Returns:
        Number of documents added
    """
    collection = get_collection(user_id, deck_id)
    
    # Generate IDs if not provided
    if ids is None:
        existing_count = collection.count()
        ids = [f"chunk_{existing_count + i}" for i in range(len(documents))]
    
    # Generate default metadata if not provided
    if metadatas is None:
        metadatas = [{"chunk_index": i} for i in range(len(documents))]
    
    collection.add(
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids
    )
    
    return len(documents)

def query_collection(
    user_id: str,
    deck_id: str,
    query_embedding: List[float],
    n_results: int = 10,
    where: Optional[Dict] = None,
    where_document: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Query a deck's collection for similar documents.
    
    Args:
        user_id: Owner's user ID
        deck_id: Deck ID  
        query_embedding: Query vector
        n_results: Number of results to return
        where: Optional metadata filter
        where_document: Optional document content filter
        
    Returns:
        Query results with documents, distances, and metadata
    """
    collection = get_collection(user_id, deck_id)
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=where,
        where_document=where_document,
        include=["documents", "metadatas", "distances"]
    )
    
    return {
        "documents": results["documents"][0] if results["documents"] else [],
        "metadatas": results["metadatas"][0] if results["metadatas"] else [],
        "distances": results["distances"][0] if results["distances"] else [],
        "count": len(results["documents"][0]) if results["documents"] else 0
    }

def get_collection_stats(user_id: str, deck_id: str) -> Dict[str, Any]:
    """Get statistics about a deck's collection"""
    collection = get_collection(user_id, deck_id)
    
    return {
        "total_documents": collection.count(),
        "collection_name": get_deck_collection_name(user_id, deck_id)
    }

# ─────────────────────────────────────────────────────────────
# Topic-Filtered Retrieval
# ─────────────────────────────────────────────────────────────

def query_by_topic(
    user_id: str,
    deck_id: str,
    query_embedding: List[float],
    topic: str,
    n_results: int = 10
) -> Dict[str, Any]:
    """
    Query with topic filter for more precise retrieval.
    Requires chunks to have 'topics' in metadata.
    """
    return query_collection(
        user_id=user_id,
        deck_id=deck_id,
        query_embedding=query_embedding,
        n_results=n_results,
        where={"topics": {"$contains": topic}}
    )

# ─────────────────────────────────────────────────────────────
# Backward Compatibility
# ─────────────────────────────────────────────────────────────

def get_chroma(deck_id: str):
    """
    Legacy function for backward compatibility.
    Uses a default user ID for simple use cases.
    """
    return get_collection("default_user", deck_id)
