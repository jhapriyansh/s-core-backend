import os
from dotenv import load_dotenv

load_dotenv()

def get_groq_key():
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY not set")
    return key
