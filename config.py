import os
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────────────────────
# API Keys
# ─────────────────────────────────────────────────────────────

def get_groq_key():
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY not set")
    return key

# ─────────────────────────────────────────────────────────────
# JWT / Auth Configuration
# ─────────────────────────────────────────────────────────────

JWT_SECRET = os.getenv("JWT_SECRET", "s-core-super-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "72"))

# ─────────────────────────────────────────────────────────────
# MongoDB Configuration
# ─────────────────────────────────────────────────────────────

def get_mongo_uri():
    return os.getenv("MONGO_URI", "mongodb://localhost:27017")

def get_mongo_db():
    return os.getenv("MONGO_DB", "score_db")

# ─────────────────────────────────────────────────────────────
# Chroma Configuration  
# ─────────────────────────────────────────────────────────────

def get_chroma_path():
    return os.getenv("CHROMA_PATH", "./chroma_data")

# ─────────────────────────────────────────────────────────────
# Model Configuration
# ─────────────────────────────────────────────────────────────

GROQ_MODEL = "llama-3.3-70b-versatile"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# ─────────────────────────────────────────────────────────────
# Pace Settings (Theory vs Practice ratios)
# ─────────────────────────────────────────────────────────────

PACE_CONFIG = {
    "slow": {"theory": 0.7, "practice": 0.3, "depth": 20, "description": "Deep learning mode"},
    "medium": {"theory": 0.5, "practice": 0.5, "depth": 12, "description": "Balanced mode"},
    "fast": {"theory": 0.3, "practice": 0.7, "depth": 6, "description": "Revision mode"}
}

# ─────────────────────────────────────────────────────────────
# Internet Enhancement Whitelist
# ─────────────────────────────────────────────────────────────

WHITELIST_DOMAINS = [
    "wikipedia.org",
    "geeksforgeeks.org",
    "tutorialspoint.com"
]

# ─────────────────────────────────────────────────────────────
# Chunking Configuration
# ─────────────────────────────────────────────────────────────

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
