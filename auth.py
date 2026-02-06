from datetime import datetime, timedelta
from typing import Optional

import jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRY_HOURS

# ─────────────────────────────────────────────────────────────
# Password Hashing (bcrypt direct — no passlib)
# ─────────────────────────────────────────────────────────────

def _prep(password: str) -> bytes:
    """Encode and truncate to 72 bytes (bcrypt hard limit)"""
    return password.encode("utf-8")[:72]

def hash_password(password: str) -> str:
    """Hash a plaintext password"""
    return bcrypt.hashpw(_prep(password), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a hash"""
    return bcrypt.checkpw(_prep(plain_password), hashed_password.encode("utf-8"))

# ─────────────────────────────────────────────────────────────
# JWT Token Management
# ─────────────────────────────────────────────────────────────

def create_access_token(user_id: str, username: str, email: str) -> str:
    """Create a JWT access token"""
    payload = {
        "sub": user_id,
        "username": username,
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# ─────────────────────────────────────────────────────────────
# FastAPI Dependency
# ─────────────────────────────────────────────────────────────

security = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    FastAPI dependency to extract the current user from the JWT token.
    Returns dict with user_id, username, email.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "user_id": payload["sub"],
        "username": payload["username"],
        "email": payload["email"],
    }
