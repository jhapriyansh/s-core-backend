"""
Session Management for S-Core
Handles conversation memory and teaching state per deck session.

Features:
- Conversation history per user/deck session
- Teaching progress tracking
- Follow-up question support
- Session state persistence
"""

import time
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

# ─────────────────────────────────────────────────────────────
# Session State Enums
# ─────────────────────────────────────────────────────────────

class TeachingMode(Enum):
    """Current mode of interaction"""
    IDLE = "idle"                    # No active teaching session
    TEACHING = "teaching"            # Actively teaching a topic
    AWAITING_INPUT = "awaiting"      # Waiting for user response
    PRACTICE = "practice"            # In practice question mode
    FREE_CHAT = "free_chat"          # General Q&A mode


class UserAction(Enum):
    """Possible user actions during teaching"""
    NEXT_TOPIC = "next"              # Move to next topic
    EXPLAIN_MORE = "more"            # Deeper explanation
    EXPLAIN_SLOWER = "slower"        # Simpler explanation
    PRACTICE = "practice"            # Want practice questions
    EXAMPLE = "example"              # Want an example
    QUESTION = "question"            # Ask a specific question
    REPEAT = "repeat"                # Repeat current topic
    SKIP = "skip"                    # Skip to specific topic
    EXIT = "exit"                    # Exit teaching mode


# ─────────────────────────────────────────────────────────────
# Data Classes
# ─────────────────────────────────────────────────────────────

@dataclass
class Message:
    """A single message in conversation history"""
    role: str                        # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    topic: Optional[str] = None      # Which syllabus topic this relates to
    message_type: str = "chat"       # "chat", "lesson", "practice", "system"
    
    def to_dict(self) -> Dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "topic": self.topic,
            "type": self.message_type
        }


@dataclass
class TeachingState:
    """Tracks teaching progress through syllabus"""
    syllabus_topics: List[str] = field(default_factory=list)
    current_topic_index: int = 0
    topics_completed: List[str] = field(default_factory=list)
    topics_needing_review: List[str] = field(default_factory=list)
    current_depth: str = "medium"    # slow/medium/fast
    is_active: bool = False
    started_at: Optional[datetime] = None
    
    @property
    def current_topic(self) -> Optional[str]:
        if 0 <= self.current_topic_index < len(self.syllabus_topics):
            return self.syllabus_topics[self.current_topic_index]
        return None
    
    @property
    def progress_percent(self) -> float:
        if not self.syllabus_topics:
            return 0.0
        return (self.current_topic_index / len(self.syllabus_topics)) * 100
    
    @property
    def remaining_topics(self) -> List[str]:
        return self.syllabus_topics[self.current_topic_index + 1:]
    
    def to_dict(self) -> Dict:
        return {
            "syllabus_topics": self.syllabus_topics,
            "current_topic_index": self.current_topic_index,
            "current_topic": self.current_topic,
            "topics_completed": self.topics_completed,
            "topics_needing_review": self.topics_needing_review,
            "current_depth": self.current_depth,
            "is_active": self.is_active,
            "progress_percent": round(self.progress_percent, 1),
            "remaining_count": len(self.remaining_topics)
        }


@dataclass
class Session:
    """Complete session state for a user's deck"""
    session_id: str
    user_id: str
    deck_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    messages: List[Message] = field(default_factory=list)
    teaching_state: TeachingState = field(default_factory=TeachingState)
    mode: TeachingMode = TeachingMode.IDLE
    context_window: int = 10         # Number of recent messages to include
    
    def add_message(self, role: str, content: str, 
                    topic: Optional[str] = None,
                    message_type: str = "chat") -> Message:
        """Add a message to conversation history"""
        msg = Message(
            role=role,
            content=content,
            topic=topic or self.teaching_state.current_topic,
            message_type=message_type
        )
        self.messages.append(msg)
        self.last_activity = datetime.utcnow()
        return msg
    
    def get_recent_messages(self, count: Optional[int] = None) -> List[Message]:
        """Get recent messages for context"""
        n = count or self.context_window
        return self.messages[-n:] if self.messages else []
    
    def get_conversation_context(self) -> str:
        """Format recent messages as context string for LLM"""
        recent = self.get_recent_messages()
        if not recent:
            return ""
        
        context_parts = ["[Previous Conversation]"]
        for msg in recent:
            prefix = "User" if msg.role == "user" else "Assistant"
            context_parts.append(f"{prefix}: {msg.content[:500]}...")
        
        return "\n".join(context_parts)
    
    def to_dict(self) -> Dict:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "deck_id": self.deck_id,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "message_count": len(self.messages),
            "mode": self.mode.value,
            "teaching_state": self.teaching_state.to_dict(),
            "recent_messages": [m.to_dict() for m in self.get_recent_messages(5)]
        }


# ─────────────────────────────────────────────────────────────
# Session Store (In-Memory with TTL)
# ─────────────────────────────────────────────────────────────

class SessionStore:
    """
    In-memory session store with TTL.
    For production, replace with Redis.
    """
    
    def __init__(self, ttl_hours: int = 24):
        self._sessions: Dict[str, Session] = {}
        self._user_deck_index: Dict[str, str] = {}  # "user_id:deck_id" -> session_id
        self.ttl = timedelta(hours=ttl_hours)
    
    def _make_key(self, user_id: str, deck_id: str) -> str:
        return f"{user_id}:{deck_id}"
    
    def _cleanup_expired(self):
        """Remove expired sessions"""
        now = datetime.utcnow()
        expired = [
            sid for sid, session in self._sessions.items()
            if now - session.last_activity > self.ttl
        ]
        for sid in expired:
            self.delete_session(sid)
    
    def get_or_create_session(self, user_id: str, deck_id: str) -> Session:
        """Get existing session or create new one"""
        self._cleanup_expired()
        
        key = self._make_key(user_id, deck_id)
        
        if key in self._user_deck_index:
            session_id = self._user_deck_index[key]
            if session_id in self._sessions:
                session = self._sessions[session_id]
                session.last_activity = datetime.utcnow()
                return session
        
        # Create new session
        session = Session(
            session_id=str(uuid.uuid4()),
            user_id=user_id,
            deck_id=deck_id
        )
        self._sessions[session.session_id] = session
        self._user_deck_index[key] = session.session_id
        
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID"""
        return self._sessions.get(session_id)
    
    def get_session_by_deck(self, user_id: str, deck_id: str) -> Optional[Session]:
        """Get session by user and deck"""
        key = self._make_key(user_id, deck_id)
        session_id = self._user_deck_index.get(key)
        if session_id:
            return self._sessions.get(session_id)
        return None
    
    def delete_session(self, session_id: str):
        """Delete a session"""
        if session_id in self._sessions:
            session = self._sessions[session_id]
            key = self._make_key(session.user_id, session.deck_id)
            del self._sessions[session_id]
            if key in self._user_deck_index:
                del self._user_deck_index[key]
    
    def clear_deck_session(self, user_id: str, deck_id: str):
        """Clear session for a specific deck"""
        key = self._make_key(user_id, deck_id)
        if key in self._user_deck_index:
            session_id = self._user_deck_index[key]
            self.delete_session(session_id)
    
    def list_user_sessions(self, user_id: str) -> List[Session]:
        """List all sessions for a user"""
        return [
            s for s in self._sessions.values()
            if s.user_id == user_id
        ]


# ─────────────────────────────────────────────────────────────
# Global Session Store Instance
# ─────────────────────────────────────────────────────────────

session_store = SessionStore(ttl_hours=24)


# ─────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────

def parse_user_action(user_input: str) -> UserAction:
    """
    Parse user input to determine their intended action.
    Handles natural language variations.
    """
    text = user_input.lower().strip()
    
    # Next topic keywords
    if any(kw in text for kw in ["next", "continue", "move on", "next topic", "go ahead", "proceed"]):
        return UserAction.NEXT_TOPIC
    
    # Explain more/deeper
    if any(kw in text for kw in ["more detail", "explain more", "deeper", "elaborate", "tell me more", "in depth"]):
        return UserAction.EXPLAIN_MORE
    
    # Explain slower/simpler
    if any(kw in text for kw in ["slower", "simpler", "simplify", "easier", "basic", "don't understand", "didn't understand", "confused", "not clear"]):
        return UserAction.EXPLAIN_SLOWER
    
    # Practice questions
    if any(kw in text for kw in ["practice", "question", "quiz", "test me", "problems", "exercise"]):
        return UserAction.PRACTICE
    
    # Example
    if any(kw in text for kw in ["example", "show me", "demonstrate", "illustration"]):
        return UserAction.EXAMPLE
    
    # Repeat
    if any(kw in text for kw in ["repeat", "again", "one more time", "say that again"]):
        return UserAction.REPEAT
    
    # Exit teaching mode
    if any(kw in text for kw in ["exit", "stop", "quit", "end", "done", "finish teaching"]):
        return UserAction.EXIT
    
    # Skip to topic
    if "skip to" in text or "go to" in text or "jump to" in text:
        return UserAction.SKIP
    
    # Default: treat as a question
    return UserAction.QUESTION


def get_action_prompt() -> str:
    """Get the standard prompt for user actions"""
    return """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 What would you like to do?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• "next" → Move to next topic
• "more" → Explain in more depth  
• "slower" → Explain in simpler terms
• "practice" → Get practice questions
• "example" → Show me an example
• "repeat" → Explain this topic again
• Or ask any specific question about this topic
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
