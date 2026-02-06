from datetime import datetime
from typing import Optional, List
from pymongo import MongoClient
from bson import ObjectId
from config import get_mongo_uri, get_mongo_db

# ─────────────────────────────────────────────────────────────
# MongoDB Connection
# ─────────────────────────────────────────────────────────────

_client: Optional[MongoClient] = None
_db = None

def get_mongo():
    """Get MongoDB database connection (singleton)"""
    global _client, _db
    if _client is None:
        _client = MongoClient(get_mongo_uri())
        _db = _client[get_mongo_db()]
    return _db

def close_mongo():
    """Close MongoDB connection"""
    global _client
    if _client:
        _client.close()
        _client = None

# ─────────────────────────────────────────────────────────────
# User Operations
# ─────────────────────────────────────────────────────────────

def create_user(username: str, email: str, password_hash: str = "") -> str:
    """Create a new user and return user_id"""
    db = get_mongo()
    user = {
        "username": username,
        "email": email,
        "password_hash": password_hash,
        "created_at": datetime.utcnow(),
        "decks": []
    }
    result = db.users.insert_one(user)
    return str(result.inserted_id)

def get_user(user_id: str) -> Optional[dict]:
    """Get user by ID"""
    db = get_mongo()
    user = db.users.find_one({"_id": ObjectId(user_id)})
    if user:
        user["_id"] = str(user["_id"])
    return user

def get_user_by_username(username: str) -> Optional[dict]:
    """Get user by username"""
    db = get_mongo()
    user = db.users.find_one({"username": username})
    if user:
        user["_id"] = str(user["_id"])
    return user

def get_user_by_email(email: str) -> Optional[dict]:
    """Get user by email"""
    db = get_mongo()
    user = db.users.find_one({"email": email})
    if user:
        user["_id"] = str(user["_id"])
    return user

# ─────────────────────────────────────────────────────────────
# Deck Operations
# ─────────────────────────────────────────────────────────────

def create_deck(user_id: str, name: str, subject: str, syllabus: str) -> str:
    """
    Create a new study deck for a user.
    Each deck represents:
    - one subject
    - one syllabus
    - one isolated vector space
    """
    db = get_mongo()
    
    deck = {
        "user_id": user_id,
        "name": name,
        "subject": subject,
        "syllabus": syllabus,
        "syllabus_topics": [],  # Parsed topics from syllabus
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "files_ingested": [],
        "chunk_count": 0,
        "status": "created"
    }
    
    result = db.decks.insert_one(deck)
    deck_id = str(result.inserted_id)
    
    # Add deck to user's deck list
    db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$push": {"decks": deck_id}}
    )
    
    return deck_id

def get_deck(deck_id: str) -> Optional[dict]:
    """Get deck by ID"""
    db = get_mongo()
    deck = db.decks.find_one({"_id": ObjectId(deck_id)})
    if deck:
        deck["_id"] = str(deck["_id"])
    return deck

def get_user_decks(user_id: str) -> List[dict]:
    """Get all decks for a user"""
    db = get_mongo()
    decks = list(db.decks.find({"user_id": user_id}))
    for deck in decks:
        deck["_id"] = str(deck["_id"])
    return decks

def update_deck(deck_id: str, updates: dict) -> bool:
    """Update deck metadata"""
    db = get_mongo()
    updates["updated_at"] = datetime.utcnow()
    result = db.decks.update_one(
        {"_id": ObjectId(deck_id)},
        {"$set": updates}
    )
    return result.modified_count > 0

def update_deck_syllabus_topics(deck_id: str, topics: List[str]):
    """Update parsed syllabus topics"""
    return update_deck(deck_id, {"syllabus_topics": topics})

def add_ingested_file(deck_id: str, filename: str, chunk_count: int):
    """Record an ingested file"""
    db = get_mongo()
    file_record = {
        "filename": filename,
        "ingested_at": datetime.utcnow(),
        "chunks_created": chunk_count
    }
    db.decks.update_one(
        {"_id": ObjectId(deck_id)},
        {
            "$push": {"files_ingested": file_record},
            "$inc": {"chunk_count": chunk_count},
            "$set": {"updated_at": datetime.utcnow(), "status": "active"}
        }
    )

def delete_deck(deck_id: str, user_id: str) -> bool:
    """Delete a deck and remove from user's list"""
    db = get_mongo()
    
    # Remove from user's deck list
    db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$pull": {"decks": deck_id}}
    )
    
    # Delete deck
    result = db.decks.delete_one({"_id": ObjectId(deck_id)})
    return result.deleted_count > 0

# ─────────────────────────────────────────────────────────────
# Query History (optional, for analytics)
# ─────────────────────────────────────────────────────────────

def log_query(deck_id: str, query: str, intent: str, coverage: bool, pace: str):
    """Log a query for analytics (optional)"""
    db = get_mongo()
    log = {
        "deck_id": deck_id,
        "query": query,
        "intent": intent,
        "coverage": coverage,
        "pace": pace,
        "timestamp": datetime.utcnow()
    }
    db.query_logs.insert_one(log)

# ─────────────────────────────────────────────────────────────
# Database Initialization
# ─────────────────────────────────────────────────────────────

def init_db():
    """Initialize database indexes"""
    db = get_mongo()
    
    # Create indexes for faster queries
    db.users.create_index("username", unique=True)
    db.users.create_index("email", unique=True)
    db.decks.create_index("user_id")
    db.decks.create_index([("user_id", 1), ("name", 1)], unique=True)
    db.query_logs.create_index("deck_id")
    db.query_logs.create_index("timestamp")
    
    print("✓ MongoDB indexes created")
