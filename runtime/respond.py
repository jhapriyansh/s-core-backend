from typing import Optional, List, Dict
from dataclasses import dataclass

from groq import Groq
from config import get_groq_key, GROQ_MODEL, PACE_CONFIG
from runtime.practice import generate_practice_set, format_practice_set

# ─────────────────────────────────────────────────────────────
# Data Classes
# ─────────────────────────────────────────────────────────────

@dataclass
class Response:
    """Complete response with theory and practice"""
    theory: str
    practice_questions: list
    answers: list
    coverage_warning: Optional[str] = None

# ─────────────────────────────────────────────────────────────
# Response Generation
# ─────────────────────────────────────────────────────────────

def get_pace_instructions(pace: str) -> dict:
    """Get pace-specific instructions for response generation"""
    instructions = {
        "slow": {
            "theory_depth": "comprehensive and detailed",
            "examples": "multiple examples for each concept",
            "practice_count": 3,
            "explanation_style": "step-by-step with intuition"
        },
        "medium": {
            "theory_depth": "balanced with key points",
            "examples": "one example per concept",
            "practice_count": 5,
            "explanation_style": "clear and concise"
        },
        "fast": {
            "theory_depth": "brief summary only",
            "examples": "minimal, only if essential",
            "practice_count": 7,
            "explanation_style": "bullet points"
        }
    }
    return instructions.get(pace, instructions["medium"])

def respond(context: str, query: str, pace: str = "medium") -> str:
    """
    Generate a response based on context and pace.
    
    The pace controls:
    - Explanation depth
    - Theory vs Practice ratio
    - Number of examples
    """
    client = Groq(api_key=get_groq_key())
    pace_config = get_pace_instructions(pace)
    
    prompt = f"""You are S-Core, a syllabus-bounded learning system.

RULES (MANDATORY - NEVER VIOLATE):
1. Use ONLY information present in the provided context
2. Do NOT introduce any concepts not found in the context
3. If something is not in the context, say: "Not covered in your uploaded material."
4. Do NOT mention unrelated topics
5. Do NOT hallucinate or make up information

CONTEXT (Your ONLY source of truth):
{context}

USER QUESTION:
{query}

PACE SETTING: {pace}
- Theory depth: {pace_config['theory_depth']}
- Examples: {pace_config['examples']}
- Explanation style: {pace_config['explanation_style']}

OUTPUT FORMAT:

📖 THEORY
{"="*40}
(Explain based on pace setting)

📝 PRACTICE QUESTIONS ({pace_config['practice_count']} questions)
{"="*40}
(Mix of conceptual, application, and numerical questions)

✅ ANSWERS & SOLUTIONS
{"="*40}
(Include step-by-step solutions)
"""
    
    try:
        res = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=3000
        )
        return res.choices[0].message.content
        
    except Exception as e:
        return f"Error generating response: {e}"

def respond_with_practice_set(
    context: str,
    query: str,
    topic: str,
    pace: str = "medium"
) -> str:
    """
    Generate response using the practice module for structured output.
    """
    practice_set = generate_practice_set(context, topic, pace)
    return format_practice_set(practice_set)

def generate_quick_answer(context: str, query: str) -> str:
    """
    Generate a quick, direct answer without practice questions.
    For simple factual queries.
    """
    client = Groq(api_key=get_groq_key())
    
    prompt = f"""Answer this question directly and concisely using ONLY the provided context.

Context:
{context}

Question:
{query}

Rules:
- Answer directly, no preamble
- Use only information from context
- If not in context, say "Not covered in your material"
- Keep it brief but complete
"""
    
    try:
        res = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500
        )
        return res.choices[0].message.content
        
    except Exception as e:
        return f"Error: {e}"


# ─────────────────────────────────────────────────────────────
# Conversation-Aware Response
# ─────────────────────────────────────────────────────────────

def respond_with_history(
    context: str,
    query: str,
    conversation_history: List[Dict[str, str]],
    pace: str = "medium"
) -> str:
    """
    Generate a response considering conversation history.
    Enables follow-up questions like "explain that slower" or "give me an example".
    
    Args:
        context: Retrieved documents
        query: Current user query
        conversation_history: List of {"role": "user/assistant", "content": "..."}
        pace: slow/medium/fast
    """
    client = Groq(api_key=get_groq_key())
    pace_config = get_pace_instructions(pace)
    
    # Format conversation history
    history_text = ""
    if conversation_history:
        history_text = "\n[PREVIOUS CONVERSATION]\n"
        for msg in conversation_history[-6:]:  # Last 6 messages
            role = "Student" if msg["role"] == "user" else "Tutor"
            content = msg["content"][:400]  # Truncate long messages
            history_text += f"{role}: {content}\n"
        history_text += "[END CONVERSATION]\n"
    
    # Check for follow-up patterns
    query_lower = query.lower()
    is_followup = any(phrase in query_lower for phrase in [
        "explain", "slower", "simpler", "don't understand",
        "didn't understand", "more detail", "example",
        "again", "what do you mean", "clarify", "confused",
        "not clear", "can you"
    ])
    
    followup_instruction = ""
    if is_followup and conversation_history:
        followup_instruction = """
IMPORTANT: This is a FOLLOW-UP question. The student is asking about something 
from the previous conversation. Look at what was discussed before and respond
appropriately. If they say "explain slower" or "don't understand", simplify 
your explanation significantly.
"""
    
    prompt = f"""You are S-Core, a patient and helpful tutoring system.

{followup_instruction}

RULES (MANDATORY):
1. Use ONLY information from the provided context
2. If something is not in context, say: "Not covered in your uploaded material."
3. Consider the conversation history when responding to follow-ups
4. If the student asks for simpler explanation, use easier language and analogies
5. If they ask for examples, provide concrete worked examples

{history_text}

CONTEXT (Your source material):
{context}

CURRENT QUESTION:
{query}

PACE SETTING: {pace}
- Theory depth: {pace_config['theory_depth']}
- Examples: {pace_config['examples']}
- Explanation style: {pace_config['explanation_style']}

Respond appropriately to the student's question:"""

    try:
        res = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2500
        )
        return res.choices[0].message.content
        
    except Exception as e:
        return f"Error generating response: {e}"
