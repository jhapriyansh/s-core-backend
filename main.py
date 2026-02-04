"""
S-Core (Score) - Syllabus-Aware AI Study Companion
Main FastAPI Application

S-Core is:
- A knowledge alignment engine
- NOT a chatbot
- NOT a PDF Q&A tool  
- NOT a search engine

It enforces syllabus boundaries, diagnoses missing knowledge,
adapts learning depth, and generates theory + practice content.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
import uvicorn

# Database imports
from db.mongo import (
    init_db, create_user, get_user, get_user_by_username,
    create_deck, get_deck, get_user_decks, delete_deck, log_query
)
from db.chroma import get_collection_stats, delete_collection

# Ingestion imports
from ingestion.pipeline import ingest_files, PipelineResult
from ingestion.embed import embed, embed_query

# Runtime imports
from runtime.classify import classify, classify_detailed
from runtime.retrieve import retrieve, RetrievalResult, retrieve_for_topic
from runtime.respond import respond, generate_quick_answer, respond_with_history
from runtime.coverage import coverage_check_detailed, get_coverage_warning
from runtime.domain import domain_guard_detailed, generate_out_of_scope_response
from runtime.internet import internet_oracle_detailed, format_internet_response
from runtime.pace import validate_pace, get_pace_description
from runtime.practice import generate_practice_set, format_practice_set
from runtime.session import (
    session_store, Session, TeachingMode, UserAction,
    parse_user_action, get_action_prompt
)
from runtime.teach import (
    start_teaching_session, teach_current_topic,
    handle_teaching_input, resume_teaching,
    TeachingResponse
)

# ─────────────────────────────────────────────────────────────
# App Configuration
# ─────────────────────────────────────────────────────────────

app = FastAPI(
    title="S-Core API",
    description="Syllabus-Aware AI Study Companion",
    version="1.0.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────
# Pydantic Models
# ─────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str
    email: str

class UserResponse(BaseModel):
    user_id: str
    username: str
    email: str

class DeckCreate(BaseModel):
    name: str
    subject: str
    syllabus: str

class DeckResponse(BaseModel):
    deck_id: str
    name: str
    subject: str
    status: str
    chunk_count: int
    files_ingested: int

class QueryRequest(BaseModel):
    query: str
    pace: str = "medium"

class QueryResponse(BaseModel):
    intent: str
    in_scope: bool
    coverage: bool
    coverage_confidence: float
    answer: str
    warning: Optional[str] = None
    internet_enhanced: bool = False

class PracticeRequest(BaseModel):
    topic: str
    pace: str = "medium"

# ─────────────────────────────────────────────────────────────
# Teaching & Session Models
# ─────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    """Request for conversational chat with memory"""
    message: str
    pace: str = "medium"

class ChatResponse(BaseModel):
    """Response from chat with session context"""
    message: str
    topic: Optional[str] = None
    mode: str
    awaiting_input: bool
    prompt: Optional[str] = None
    progress: Optional[dict] = None
    session_id: str

class StartTeachingRequest(BaseModel):
    """Request to start auto-teaching mode"""
    starting_topic: Optional[str] = None
    pace: str = "medium"

class SessionResponse(BaseModel):
    """Session state information"""
    session_id: str
    user_id: str
    deck_id: str
    mode: str
    message_count: int
    teaching_state: Optional[dict] = None

# ─────────────────────────────────────────────────────────────
# Startup Events
# ─────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    """Initialize database on startup"""
    try:
        init_db()
        print("✓ S-Core API started")
    except Exception as e:
        print(f"⚠ Database init warning: {e}")

# ─────────────────────────────────────────────────────────────
# Health Check
# ─────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "name": "S-Core",
        "description": "Syllabus-Aware AI Study Companion",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

# ─────────────────────────────────────────────────────────────
# User Endpoints
# ─────────────────────────────────────────────────────────────

@app.post("/users", response_model=UserResponse)
async def create_new_user(user: UserCreate):
    """Create a new user"""
    try:
        # Check if user exists
        existing = get_user_by_username(user.username)
        if existing:
            raise HTTPException(400, "Username already exists")
        
        user_id = create_user(user.username, user.email)
        return UserResponse(
            user_id=user_id,
            username=user.username,
            email=user.email
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/users/{user_id}")
async def get_user_info(user_id: str):
    """Get user information"""
    user = get_user(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return user

# ─────────────────────────────────────────────────────────────
# Deck Management Endpoints
# ─────────────────────────────────────────────────────────────

@app.post("/users/{user_id}/decks", response_model=DeckResponse)
async def create_new_deck(user_id: str, deck: DeckCreate):
    """
    Create a new study deck.
    Each deck represents:
    - One subject
    - One syllabus
    - One isolated vector space
    """
    try:
        # Verify user exists
        user = get_user(user_id)
        if not user:
            raise HTTPException(404, "User not found")
        
        deck_id = create_deck(
            user_id=user_id,
            name=deck.name,
            subject=deck.subject,
            syllabus=deck.syllabus
        )
        
        return DeckResponse(
            deck_id=deck_id,
            name=deck.name,
            subject=deck.subject,
            status="created",
            chunk_count=0,
            files_ingested=0
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/users/{user_id}/decks")
async def list_user_decks(user_id: str):
    """List all decks for a user"""
    decks = get_user_decks(user_id)
    return {"decks": decks}

@app.get("/users/{user_id}/decks/{deck_id}")
async def get_deck_info(user_id: str, deck_id: str):
    """Get detailed deck information"""
    deck = get_deck(deck_id)
    if not deck:
        raise HTTPException(404, "Deck not found")
    if deck.get("user_id") != user_id:
        raise HTTPException(403, "Access denied")
    
    # Add Chroma stats
    stats = get_collection_stats(user_id, deck_id)
    deck["vector_stats"] = stats
    
    return deck

@app.delete("/users/{user_id}/decks/{deck_id}")
async def remove_deck(user_id: str, deck_id: str):
    """Delete a deck and its vector space"""
    deck = get_deck(deck_id)
    if not deck:
        raise HTTPException(404, "Deck not found")
    if deck.get("user_id") != user_id:
        raise HTTPException(403, "Access denied")
    
    # Delete from Chroma
    delete_collection(user_id, deck_id)
    
    # Delete from MongoDB
    delete_deck(deck_id, user_id)
    
    return {"status": "deleted", "deck_id": deck_id}

# ─────────────────────────────────────────────────────────────
# File Upload & Ingestion Endpoints
# ─────────────────────────────────────────────────────────────

@app.post("/users/{user_id}/decks/{deck_id}/upload")
async def upload_files(
    user_id: str,
    deck_id: str,
    files: List[UploadFile] = File(...)
):
    """
    Upload and ingest files into a deck.
    
    Supported formats:
    - PDF, DOC/DOCX, PPT/PPTX, TXT
    - Images (PNG, JPG, JPEG) - for scanned notes
    
    Files are processed through the unified ingestion pipeline:
    1. Extract text and images
    2. Convert images to text (OCR + LLM)
    3. Merge streams
    4. Filter by syllabus (hard boundary)
    5. Embed and store
    """
    # Verify deck exists and belongs to user
    deck = get_deck(deck_id)
    if not deck:
        raise HTTPException(404, "Deck not found")
    if deck.get("user_id") != user_id:
        raise HTTPException(403, "Access denied")
    
    syllabus = deck.get("syllabus", "")
    if not syllabus:
        raise HTTPException(400, "Deck has no syllabus defined")
    
    # Run ingestion pipeline
    result: PipelineResult = ingest_files(
        files=files,
        syllabus=syllabus,
        user_id=user_id,
        deck_id=deck_id
    )
    
    return {
        "status": "success",
        "files_processed": result.files_processed,
        "total_chunks": result.total_chunks,
        "total_filtered": result.total_filtered,
        "syllabus_topics": result.syllabus_topics,
        "details": [
            {
                "filename": r.filename,
                "success": r.success,
                "chunks": r.chunks_created,
                "filtered": r.chunks_filtered,
                "error": r.error
            }
            for r in result.results
        ]
    }

# ─────────────────────────────────────────────────────────────
# Query Endpoints
# ─────────────────────────────────────────────────────────────

@app.post("/users/{user_id}/decks/{deck_id}/ask", response_model=QueryResponse)
async def ask_question(
    user_id: str,
    deck_id: str,
    request: QueryRequest
):
    """
    Ask a question within a deck's knowledge space.
    
    Runtime flow:
    1. Classify query (intent + topic)
    2. Check domain (in syllabus scope?)
    3. Retrieve relevant documents
    4. Check coverage (sufficient material?)
    5. Generate response (pace-aware)
    6. Fallback to internet if needed
    """
    # Verify deck
    deck = get_deck(deck_id)
    if not deck:
        raise HTTPException(404, "Deck not found")
    if deck.get("user_id") != user_id:
        raise HTTPException(403, "Access denied")
    
    query = request.query
    pace = validate_pace(request.pace)
    syllabus = deck.get("syllabus", "")
    syllabus_topics = deck.get("syllabus_topics", [])
    
    # Step 1: Classify intent
    intent = classify(query)
    
    # Step 2: Domain check
    in_scope, domain_sim, domain_reason = domain_guard_detailed(
        query, syllabus, syllabus_topics
    )
    
    # Step 3: Retrieve documents
    retrieval_result: RetrievalResult = retrieve(
        user_id=user_id,
        deck_id=deck_id,
        query_text=query,
        pace=pace,
        expand=True
    )
    
    # Step 4: Coverage check
    coverage_ok, coverage_conf, coverage_reason = coverage_check_detailed(
        retrieval_result.documents,
        retrieval_result.scores,
        query
    )
    
    # Log query
    log_query(deck_id, query, intent, coverage_ok, pace)
    
    # Step 5: Generate response
    if in_scope and coverage_ok:
        # Normal flow - generate from local knowledge
        context = "\n\n".join(retrieval_result.documents)
        answer = respond(context, query, pace)
        warning = get_coverage_warning(coverage_conf)
        
        return QueryResponse(
            intent=intent,
            in_scope=True,
            coverage=True,
            coverage_confidence=coverage_conf,
            answer=answer,
            warning=warning if warning else None,
            internet_enhanced=False
        )
    
    # Step 6: Internet fallback
    if not in_scope:
        # Topic outside syllabus
        out_of_scope_msg = generate_out_of_scope_response(query, syllabus)
        internet_result = internet_oracle_detailed(query)
        
        answer = (
            f"⚠️ **Topic Outside Syllabus Scope**\n\n"
            f"{out_of_scope_msg}\n\n"
            f"{format_internet_response(internet_result.content, internet_result.sources)}"
        )
        
        return QueryResponse(
            intent=intent,
            in_scope=False,
            coverage=False,
            coverage_confidence=0.0,
            answer=answer,
            warning="This topic is not in your current syllabus.",
            internet_enhanced=True
        )
    
    # Insufficient coverage
    context = "\n\n".join(retrieval_result.documents) if retrieval_result.documents else ""
    local_answer = respond(context, query, pace) if context else ""
    internet_result = internet_oracle_detailed(query)
    
    answer = (
        f"⚠️ **Limited Coverage in Your Material**\n\n"
        f"{coverage_reason}\n\n"
    )
    
    if local_answer:
        answer += f"**From Your Material:**\n{local_answer}\n\n"
    
    answer += format_internet_response(internet_result.content, internet_result.sources)
    
    return QueryResponse(
        intent=intent,
        in_scope=True,
        coverage=False,
        coverage_confidence=coverage_conf,
        answer=answer,
        warning=coverage_reason,
        internet_enhanced=True
    )

# ─────────────────────────────────────────────────────────────
# Practice Generation Endpoints
# ─────────────────────────────────────────────────────────────

@app.post("/users/{user_id}/decks/{deck_id}/practice")
async def generate_practice(
    user_id: str,
    deck_id: str,
    request: PracticeRequest
):
    """
    Generate practice questions for a topic.
    
    Question types:
    1. Conceptual - definitions, explanations, comparisons
    2. Application - scenarios, tracing, classification
    3. Numerical - calculations, algorithms
    
    Each question includes answer and step-by-step solution.
    """
    # Verify deck
    deck = get_deck(deck_id)
    if not deck:
        raise HTTPException(404, "Deck not found")
    if deck.get("user_id") != user_id:
        raise HTTPException(403, "Access denied")
    
    topic = request.topic
    pace = validate_pace(request.pace)
    
    # Retrieve relevant context
    retrieval_result = retrieve(
        user_id=user_id,
        deck_id=deck_id,
        query_text=topic,
        pace=pace,
        expand=True
    )
    
    if not retrieval_result.documents:
        raise HTTPException(404, f"No material found for topic: {topic}")
    
    context = "\n\n".join(retrieval_result.documents)
    
    # Generate practice set
    practice_set = generate_practice_set(context, topic, pace)
    
    return {
        "topic": topic,
        "pace": pace,
        "pace_description": get_pace_description(pace),
        "theory_summary": practice_set.theory_summary,
        "questions": [
            {
                "type": q.question_type.value,
                "question": q.question,
                "answer": q.answer,
                "solution_steps": q.solution_steps,
                "difficulty": q.difficulty
            }
            for q in practice_set.questions
        ],
        "formatted": format_practice_set(practice_set)
    }

# ─────────────────────────────────────────────────────────────
# Topic Coverage Endpoints
# ─────────────────────────────────────────────────────────────

@app.get("/users/{user_id}/decks/{deck_id}/coverage")
async def get_topic_coverage(user_id: str, deck_id: str):
    """
    Get syllabus topic coverage analysis.
    Shows which topics have material and which don't.
    """
    deck = get_deck(deck_id)
    if not deck:
        raise HTTPException(404, "Deck not found")
    if deck.get("user_id") != user_id:
        raise HTTPException(403, "Access denied")
    
    syllabus_topics = deck.get("syllabus_topics", [])
    
    # Check coverage for each topic
    coverage = []
    for topic in syllabus_topics:
        result = retrieve(
            user_id=user_id,
            deck_id=deck_id,
            query_text=topic,
            pace="medium",
            expand=False
        )
        
        coverage.append({
            "topic": topic,
            "documents_found": result.total_found,
            "covered": result.total_found >= 2
        })
    
    covered_count = sum(1 for c in coverage if c["covered"])
    
    return {
        "total_topics": len(syllabus_topics),
        "covered_topics": covered_count,
        "coverage_ratio": covered_count / len(syllabus_topics) if syllabus_topics else 0,
        "topics": coverage
    }

# ─────────────────────────────────────────────────────────────
# Teaching & Session Endpoints
# ─────────────────────────────────────────────────────────────

@app.get("/users/{user_id}/decks/{deck_id}/session")
async def get_session(user_id: str, deck_id: str):
    """Get or create a session for this deck"""
    # Validate deck exists
    deck = get_deck(deck_id)
    if not deck:
        raise HTTPException(404, "Deck not found")
    if deck.get("user_id") != user_id:
        raise HTTPException(403, "Access denied")
    
    session = session_store.get_or_create_session(user_id, deck_id)
    
    return {
        "session_id": session.session_id,
        "user_id": session.user_id,
        "deck_id": session.deck_id,
        "mode": session.mode.value,
        "message_count": len(session.messages),
        "teaching_state": session.teaching_state.to_dict(),
        "recent_messages": [m.to_dict() for m in session.get_recent_messages(5)]
    }


@app.delete("/users/{user_id}/decks/{deck_id}/session")
async def clear_session(user_id: str, deck_id: str):
    """Clear the session for this deck (reset conversation)"""
    session_store.clear_deck_session(user_id, deck_id)
    return {"status": "cleared", "message": "Session and conversation history cleared"}


@app.post("/users/{user_id}/decks/{deck_id}/teach/start")
async def start_teaching(
    user_id: str,
    deck_id: str,
    request: StartTeachingRequest
):
    """
    Start auto-teaching mode.
    The system will teach topics in syllabus order.
    """
    # Validate deck
    deck = get_deck(deck_id)
    if not deck:
        raise HTTPException(404, "Deck not found")
    if deck.get("user_id") != user_id:
        raise HTTPException(403, "Access denied")
    
    syllabus_topics = deck.get("syllabus_topics", [])
    if not syllabus_topics:
        raise HTTPException(400, "Deck has no syllabus topics. Upload materials first.")
    
    # Get or create session
    session = session_store.get_or_create_session(user_id, deck_id)
    
    # Start teaching
    response = start_teaching_session(
        session=session,
        syllabus_topics=syllabus_topics,
        starting_topic=request.starting_topic,
        pace=request.pace
    )
    
    return {
        "session_id": session.session_id,
        "message": response.message,
        "topic": response.topic,
        "action": response.action_taken,
        "mode": response.mode,
        "progress": response.progress,
        "awaiting_input": response.awaiting_input,
        "prompt": response.prompt
    }


@app.post("/users/{user_id}/decks/{deck_id}/chat", response_model=ChatResponse)
async def chat(
    user_id: str,
    deck_id: str,
    request: ChatRequest
):
    """
    Conversational chat endpoint with memory.
    
    Handles:
    - Teaching mode interactions (next, slower, more, practice, example)
    - Follow-up questions ("explain that again", "I don't understand")
    - Free-form questions about the material
    
    The session remembers previous messages for context.
    """
    # Validate deck
    deck = get_deck(deck_id)
    if not deck:
        raise HTTPException(404, "Deck not found")
    if deck.get("user_id") != user_id:
        raise HTTPException(403, "Access denied")
    
    # Get or create session
    session = session_store.get_or_create_session(user_id, deck_id)
    
    user_input = request.message.strip()
    pace = request.pace
    
    # Check if in teaching mode
    if session.mode in [TeachingMode.TEACHING, TeachingMode.AWAITING_INPUT]:
        # Handle as teaching input
        response = handle_teaching_input(session, user_input)
        
        return ChatResponse(
            message=response.message,
            topic=response.topic,
            mode=response.mode,
            awaiting_input=response.awaiting_input,
            prompt=response.prompt,
            progress=response.progress,
            session_id=session.session_id
        )
    
    # Check for commands to start/resume teaching
    input_lower = user_input.lower()
    if any(cmd in input_lower for cmd in ["start teaching", "teach me", "begin lesson"]):
        syllabus_topics = deck.get("syllabus_topics", [])
        if syllabus_topics:
            response = start_teaching_session(
                session=session,
                syllabus_topics=syllabus_topics,
                pace=pace
            )
            return ChatResponse(
                message=response.message,
                topic=response.topic,
                mode=response.mode,
                awaiting_input=response.awaiting_input,
                prompt=response.prompt,
                progress=response.progress,
                session_id=session.session_id
            )
    
    if any(cmd in input_lower for cmd in ["continue teaching", "resume"]):
        if session.teaching_state.syllabus_topics:
            response = resume_teaching(session)
            return ChatResponse(
                message=response.message,
                topic=response.topic,
                mode=response.mode,
                awaiting_input=response.awaiting_input,
                prompt=response.prompt,
                progress=response.progress,
                session_id=session.session_id
            )
    
    # Free-form Q&A mode with conversation history
    session.add_message(role="user", content=user_input)
    
    # Get conversation history for context
    history = [{"role": m.role, "content": m.content} for m in session.get_recent_messages(6)]
    
    # Retrieve relevant content
    syllabus = deck.get("syllabus", "")
    retrieval = retrieve(user_id, deck_id, user_input, pace)
    context = "\n\n".join(retrieval.documents) if retrieval.documents else ""
    
    # Check domain and coverage
    in_scope, similarity, explanation = domain_guard_detailed(user_input, syllabus)
    
    if not in_scope:
        # Out of scope
        answer = generate_out_of_scope_response(user_input, syllabus)
        session.add_message(role="assistant", content=answer)
        
        return ChatResponse(
            message=answer,
            topic=None,
            mode=session.mode.value,
            awaiting_input=False,
            prompt=None,
            progress=None,
            session_id=session.session_id
        )
    
    # Generate response with history
    answer = respond_with_history(
        context=context,
        query=user_input,
        conversation_history=history[:-1],  # Exclude current message
        pace=pace
    )
    
    session.add_message(role="assistant", content=answer)
    
    return ChatResponse(
        message=answer,
        topic=domain_result.matched_topic,
        mode=session.mode.value,
        awaiting_input=False,
        prompt=None,
        progress=None,
        session_id=session.session_id
    )


@app.get("/users/{user_id}/decks/{deck_id}/teach/progress")
async def get_teaching_progress(user_id: str, deck_id: str):
    """Get current teaching progress for this deck"""
    session = session_store.get_session_by_deck(user_id, deck_id)
    
    if not session:
        return {
            "active": False,
            "message": "No active teaching session"
        }
    
    state = session.teaching_state
    return {
        "active": state.is_active,
        "current_topic": state.current_topic,
        "current_topic_index": state.current_topic_index,
        "total_topics": len(state.syllabus_topics),
        "progress_percent": state.progress_percent,
        "topics_completed": state.topics_completed,
        "topics_needing_review": state.topics_needing_review,
        "mode": session.mode.value,
        "session_id": session.session_id
    }


@app.get("/users/{user_id}/decks/{deck_id}/history")
async def get_conversation_history(
    user_id: str,
    deck_id: str,
    limit: int = 20
):
    """Get conversation history for this deck"""
    session = session_store.get_session_by_deck(user_id, deck_id)
    
    if not session:
        return {"messages": [], "count": 0}
    
    messages = session.messages[-limit:] if session.messages else []
    
    return {
        "messages": [m.to_dict() for m in messages],
        "count": len(messages),
        "total": len(session.messages),
        "session_id": session.session_id
    }


# ─────────────────────────────────────────────────────────────
# Legacy Endpoints (for backward compatibility)
# ─────────────────────────────────────────────────────────────

# Store for legacy single-deck mode
_legacy_state = {
    "user_id": "default_user",
    "deck_id": None,
    "syllabus": None
}

@app.post("/upload")
async def legacy_upload(
    file: UploadFile = File(...),
    syllabus: str = Form(...)
):
    """Legacy upload endpoint (single deck mode)"""
    global _legacy_state
    
    # Create or get default deck
    if _legacy_state["deck_id"] is None:
        _legacy_state["deck_id"] = create_deck(
            user_id=_legacy_state["user_id"],
            name="Default Deck",
            subject="General",
            syllabus=syllabus
        )
    
    _legacy_state["syllabus"] = syllabus
    
    result = ingest_files(
        files=[file],
        syllabus=syllabus,
        user_id=_legacy_state["user_id"],
        deck_id=_legacy_state["deck_id"]
    )
    
    return {
        "status": "ingested",
        "chunks": result.total_chunks,
        "filtered": result.total_filtered
    }

@app.post("/ask")
async def legacy_ask(query: str, pace: str = "medium"):
    """Legacy ask endpoint (single deck mode)"""
    global _legacy_state
    
    if _legacy_state["deck_id"] is None:
        return {"error": "No deck uploaded yet."}
    
    # Use the new endpoint logic
    from pydantic import BaseModel
    request = QueryRequest(query=query, pace=pace)
    
    response = await ask_question(
        user_id=_legacy_state["user_id"],
        deck_id=_legacy_state["deck_id"],
        request=request
    )
    
    return {
        "intent": response.intent,
        "coverage": response.coverage,
        "answer": response.answer
    }

# ─────────────────────────────────────────────────────────────
# Run Server
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
