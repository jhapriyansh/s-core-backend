"""
S-Core Runtime Package
Handles all query-time operations.

Modules:
- classify: Query intent classification
- retrieve: Hierarchical semantic retrieval
- respond: Response generation
- coverage: Coverage detection
- domain: Domain/scope checking
- internet: Internet enhancement
- expand: Topic expansion
- pace: Pace configuration
- practice: Practice question generation
- session: Conversation memory and session management
- teach: Auto-teaching flow controller
"""

from runtime.classify import classify, classify_detailed
from runtime.retrieve import retrieve, retrieve_for_topic
from runtime.respond import respond, respond_with_history
from runtime.coverage import coverage_check_detailed
from runtime.domain import domain_guard_detailed
from runtime.internet import internet_oracle_detailed
from runtime.expand import expand_topics
from runtime.pace import pace_config, validate_pace
from runtime.practice import generate_practice_set
from runtime.session import session_store, Session, TeachingMode
from runtime.teach import start_teaching_session, handle_teaching_input

__all__ = [
    "classify",
    "classify_detailed",
    "retrieve",
    "retrieve_for_topic",
    "respond",
    "respond_with_history",
    "coverage_check_detailed",
    "domain_guard_detailed",
    "internet_oracle_detailed",
    "expand_topics",
    "pace_config",
    "validate_pace",
    "generate_practice_set",
    "session_store",
    "Session",
    "TeachingMode",
    "start_teaching_session",
    "handle_teaching_input"
]
