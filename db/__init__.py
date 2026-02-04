"""
S-Core Database Package
Handles all data persistence.

Modules:
- chroma: Vector database operations (ChromaDB)
- mongo: Document database operations (MongoDB)
"""

from db.chroma import get_collection, add_documents, query_collection
from db.mongo import (
    create_user, get_user,
    create_deck, get_deck, get_user_decks,
    init_db
)

__all__ = [
    # Chroma
    "get_collection",
    "add_documents", 
    "query_collection",
    # Mongo
    "create_user",
    "get_user",
    "create_deck",
    "get_deck",
    "get_user_decks",
    "init_db"
]
