"""
Auto-Teaching Module for S-Core
Teaches syllabus topics in order with interactive flow.

Features:
- Follows syllabus order automatically
- Teaches topic by topic with appropriate depth
- Prompts user after each topic
- Handles: next, explain more, slower, practice, example
- Tracks progress through syllabus
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from groq import Groq

from config import get_groq_key, GROQ_MODEL
from runtime.session import (
    Session, TeachingState, TeachingMode, UserAction,
    session_store, parse_user_action, get_action_prompt
)
from runtime.retrieve import retrieve_for_topic
from runtime.practice import generate_practice_set, format_practice_set

# ─────────────────────────────────────────────────────────────
# Teaching Response Generator
# ─────────────────────────────────────────────────────────────

def generate_lesson(
    topic: str,
    context: str,
    depth: str = "medium",
    previous_explanation: Optional[str] = None,
    request_type: str = "initial"
) -> str:
    """
    Generate a lesson for a topic.
    
    Args:
        topic: The syllabus topic to teach
        context: Retrieved content from the deck
        depth: slow/medium/fast - determines explanation depth
        previous_explanation: If re-explaining, the previous attempt
        request_type: initial, deeper, simpler, example
    """
    client = Groq(api_key=get_groq_key())
    
    depth_instructions = {
        "slow": """
- Use simple, everyday language
- Explain every concept from the ground up
- Use many analogies and real-world comparisons
- Break down into very small steps
- Assume no prior knowledge
- Include visual descriptions where helpful
- Provide multiple examples for each concept
""",
        "medium": """
- Balance theory and examples
- Assume basic foundational knowledge
- Explain key concepts thoroughly
- Include 1-2 examples per concept
- Connect to related topics when relevant
""",
        "fast": """
- Be concise and to the point
- Focus on key facts and formulas
- Assume good foundational knowledge
- Use technical terminology freely
- Emphasize what's important for exams
- Quick examples only
"""
    }
    
    request_instructions = {
        "initial": "This is the first explanation of this topic.",
        "deeper": f"""The student asked for MORE DEPTH. Their previous explanation was:
---
{previous_explanation[:1000] if previous_explanation else 'N/A'}
---
Now go DEEPER. Add more details, edge cases, advanced concepts, and nuances.""",
        "simpler": f"""The student said they DON'T UNDERSTAND. Previous explanation:
---
{previous_explanation[:1000] if previous_explanation else 'N/A'}
---
Now explain it SIMPLER. Use easier words, more analogies, break it into smaller pieces.""",
        "example": f"""The student wants MORE EXAMPLES. Previous explanation:
---
{previous_explanation[:500] if previous_explanation else 'N/A'}
---
Provide 2-3 detailed, worked-out examples with step-by-step solutions."""
    }
    
    prompt = f"""You are a patient, expert tutor teaching a student.

TOPIC TO TEACH: {topic}

DEPTH LEVEL: {depth.upper()}
{depth_instructions.get(depth, depth_instructions['medium'])}

REQUEST TYPE: {request_type}
{request_instructions.get(request_type, request_instructions['initial'])}

STUDY MATERIAL (Use this as your source):
{context}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INSTRUCTIONS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Teach ONLY this topic: "{topic}"
2. Use ONLY information from the study material
3. Structure your lesson clearly with headers
4. Include relevant formulas if applicable
5. End with a brief summary of key points

FORMAT:
📖 LESSON: {topic}
================================

[Your explanation here]

📌 KEY TAKEAWAYS:
• Point 1
• Point 2
• Point 3

Generate the lesson now:"""

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=2000
    )
    
    return response.choices[0].message.content


def generate_topic_example(topic: str, context: str) -> str:
    """Generate worked examples for a topic"""
    client = Groq(api_key=get_groq_key())
    
    prompt = f"""You are a tutor providing worked examples for: {topic}

STUDY MATERIAL:
{context}

Provide 2-3 detailed examples that illustrate this topic.
For each example:
1. State the problem/scenario clearly
2. Show step-by-step solution
3. Explain the reasoning at each step
4. Highlight common mistakes to avoid

FORMAT:
📝 WORKED EXAMPLES: {topic}
================================

Example 1: [Title]
---
[Problem statement]
[Step-by-step solution]
[Key insight]

Example 2: [Title]
---
[Problem statement]
[Step-by-step solution]
[Key insight]

Generate examples now:"""

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1500
    )
    
    return response.choices[0].message.content


# ─────────────────────────────────────────────────────────────
# Teaching Flow Controller
# ─────────────────────────────────────────────────────────────

@dataclass
class TeachingResponse:
    """Response from the teaching system"""
    message: str
    topic: str
    action_taken: str
    mode: str
    progress: Dict[str, Any]
    awaiting_input: bool
    prompt: Optional[str] = None


def start_teaching_session(
    session: Session,
    syllabus_topics: List[str],
    starting_topic: Optional[str] = None,
    pace: str = "medium"
) -> TeachingResponse:
    """
    Start a new teaching session.
    Begins teaching from the first topic (or specified topic).
    """
    # Initialize teaching state
    session.teaching_state = TeachingState(
        syllabus_topics=syllabus_topics,
        current_topic_index=0,
        current_depth=pace,
        is_active=True
    )
    
    # If starting from a specific topic, find its index
    if starting_topic:
        try:
            idx = syllabus_topics.index(starting_topic)
            session.teaching_state.current_topic_index = idx
        except ValueError:
            pass  # Start from beginning if topic not found
    
    session.mode = TeachingMode.TEACHING
    
    # Add system message
    session.add_message(
        role="assistant",
        content=f"📚 Starting teaching session! We'll cover {len(syllabus_topics)} topics.",
        message_type="system"
    )
    
    # Teach the first topic
    return teach_current_topic(session)


def teach_current_topic(
    session: Session,
    request_type: str = "initial"
) -> TeachingResponse:
    """Teach the current topic in the syllabus"""
    state = session.teaching_state
    topic = state.current_topic
    
    if not topic:
        return TeachingResponse(
            message="🎉 Congratulations! You've completed all topics in the syllabus!",
            topic="",
            action_taken="completed",
            mode=TeachingMode.IDLE.value,
            progress=state.to_dict(),
            awaiting_input=False
        )
    
    # Retrieve relevant content for this topic
    context = retrieve_for_topic(session.user_id, session.deck_id, topic)
    
    if not context:
        context = f"Topic: {topic}\n(Limited material available for this topic)"
    
    # Get previous explanation if needed
    previous = None
    if request_type in ["deeper", "simpler"]:
        # Find last lesson message
        for msg in reversed(session.messages):
            if msg.message_type == "lesson" and msg.topic == topic:
                previous = msg.content
                break
    
    # Generate the lesson
    lesson = generate_lesson(
        topic=topic,
        context=context,
        depth=state.current_depth,
        previous_explanation=previous,
        request_type=request_type
    )
    
    # Add to conversation history
    session.add_message(
        role="assistant",
        content=lesson,
        topic=topic,
        message_type="lesson"
    )
    
    session.mode = TeachingMode.AWAITING_INPUT
    
    # Build progress info
    progress = state.to_dict()
    
    return TeachingResponse(
        message=lesson,
        topic=topic,
        action_taken=f"taught_{request_type}",
        mode=session.mode.value,
        progress=progress,
        awaiting_input=True,
        prompt=get_action_prompt()
    )


def handle_teaching_input(
    session: Session,
    user_input: str
) -> TeachingResponse:
    """
    Handle user input during teaching session.
    Routes to appropriate handler based on user action.
    """
    state = session.teaching_state
    topic = state.current_topic
    
    # Add user message to history
    session.add_message(
        role="user",
        content=user_input,
        topic=topic,
        message_type="chat"
    )
    
    # Parse user action
    action = parse_user_action(user_input)
    
    # Handle each action type
    if action == UserAction.NEXT_TOPIC:
        return move_to_next_topic(session)
    
    elif action == UserAction.EXPLAIN_MORE:
        return teach_current_topic(session, request_type="deeper")
    
    elif action == UserAction.EXPLAIN_SLOWER:
        state.topics_needing_review.append(topic)
        return teach_current_topic(session, request_type="simpler")
    
    elif action == UserAction.EXAMPLE:
        return provide_examples(session)
    
    elif action == UserAction.PRACTICE:
        return provide_practice(session)
    
    elif action == UserAction.REPEAT:
        return teach_current_topic(session, request_type="initial")
    
    elif action == UserAction.EXIT:
        return exit_teaching_mode(session)
    
    elif action == UserAction.SKIP:
        # Extract topic name from input
        return skip_to_topic(session, user_input)
    
    else:  # UserAction.QUESTION - handle as a question about current topic
        return answer_question_in_context(session, user_input)


def move_to_next_topic(session: Session) -> TeachingResponse:
    """Move to the next topic in syllabus"""
    state = session.teaching_state
    
    # Mark current topic as completed
    if state.current_topic:
        state.topics_completed.append(state.current_topic)
    
    # Move to next
    state.current_topic_index += 1
    
    if state.current_topic_index >= len(state.syllabus_topics):
        # All topics completed!
        session.mode = TeachingMode.IDLE
        state.is_active = False
        
        summary = f"""
🎉 CONGRATULATIONS! You've completed the entire syllabus!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Session Summary:
• Topics Covered: {len(state.topics_completed)}
• Topics Needing Review: {len(state.topics_needing_review)}

{"🔄 Topics to Review:" if state.topics_needing_review else ""}
{chr(10).join(f"  • {t}" for t in state.topics_needing_review) if state.topics_needing_review else ""}

What would you like to do next?
• "start teaching" - Go through syllabus again
• "practice" - Get practice questions
• Or ask any question about the topics
"""
        session.add_message(
            role="assistant",
            content=summary,
            message_type="system"
        )
        
        return TeachingResponse(
            message=summary,
            topic="",
            action_taken="completed_syllabus",
            mode=session.mode.value,
            progress=state.to_dict(),
            awaiting_input=False
        )
    
    # Teach the new topic
    transition_msg = f"\n✅ Great! Moving on to: **{state.current_topic}**\n"
    session.add_message(
        role="assistant",
        content=transition_msg,
        message_type="system"
    )
    
    return teach_current_topic(session)


def provide_examples(session: Session) -> TeachingResponse:
    """Provide worked examples for current topic"""
    state = session.teaching_state
    topic = state.current_topic
    
    # Retrieve context
    context = retrieve_for_topic(session.user_id, session.deck_id, topic)
    
    # Generate examples
    examples = generate_topic_example(topic, context)
    
    session.add_message(
        role="assistant",
        content=examples,
        topic=topic,
        message_type="lesson"
    )
    
    session.mode = TeachingMode.AWAITING_INPUT
    
    return TeachingResponse(
        message=examples,
        topic=topic,
        action_taken="provided_examples",
        mode=session.mode.value,
        progress=state.to_dict(),
        awaiting_input=True,
        prompt=get_action_prompt()
    )


def provide_practice(session: Session) -> TeachingResponse:
    """Provide practice questions for current topic"""
    state = session.teaching_state
    topic = state.current_topic
    
    # Retrieve context
    context = retrieve_for_topic(session.user_id, session.deck_id, topic)
    
    # Generate practice set
    practice = generate_practice_set(context, topic, state.current_depth)
    practice_text = format_practice_set(practice)
    
    session.add_message(
        role="assistant",
        content=practice_text,
        topic=topic,
        message_type="practice"
    )
    
    session.mode = TeachingMode.AWAITING_INPUT
    
    prompt = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Try to solve these! When ready:
• "next" → Continue to next topic
• "more practice" → Get more questions
• "explain" → Go back to explanation
• Or ask for help with a specific question
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    return TeachingResponse(
        message=practice_text,
        topic=topic,
        action_taken="provided_practice",
        mode=session.mode.value,
        progress=state.to_dict(),
        awaiting_input=True,
        prompt=prompt
    )


def answer_question_in_context(session: Session, question: str) -> TeachingResponse:
    """Answer a specific question within the teaching context"""
    state = session.teaching_state
    topic = state.current_topic
    
    # Get conversation context
    conv_context = session.get_conversation_context()
    
    # Retrieve relevant content
    retrieval_context = retrieve_for_topic(session.user_id, session.deck_id, topic)
    
    client = Groq(api_key=get_groq_key())
    
    prompt = f"""You are a tutor answering a student's question.

CURRENT TOPIC: {topic}

PREVIOUS CONVERSATION:
{conv_context}

STUDY MATERIAL:
{retrieval_context}

STUDENT'S QUESTION:
{question}

Answer the question:
1. Stay focused on the current topic: {topic}
2. Use only information from the study material
3. Reference the previous conversation if relevant
4. Be helpful and encouraging
5. If the question is off-topic, gently redirect to the current topic

Answer:"""

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1000
    )
    
    answer = response.choices[0].message.content
    
    session.add_message(
        role="assistant",
        content=answer,
        topic=topic,
        message_type="chat"
    )
    
    session.mode = TeachingMode.AWAITING_INPUT
    
    return TeachingResponse(
        message=answer,
        topic=topic,
        action_taken="answered_question",
        mode=session.mode.value,
        progress=state.to_dict(),
        awaiting_input=True,
        prompt=get_action_prompt()
    )


def skip_to_topic(session: Session, user_input: str) -> TeachingResponse:
    """Skip to a specific topic"""
    state = session.teaching_state
    
    # Try to find the topic in input
    input_lower = user_input.lower()
    
    for i, topic in enumerate(state.syllabus_topics):
        if topic.lower() in input_lower:
            state.current_topic_index = i
            msg = f"⏭️ Jumping to: **{topic}**\n"
            session.add_message(role="assistant", content=msg, message_type="system")
            return teach_current_topic(session)
    
    # Topic not found - list available topics
    topic_list = "\n".join(f"  {i+1}. {t}" for i, t in enumerate(state.syllabus_topics))
    msg = f"""I couldn't find that topic. Available topics:

{topic_list}

Say "skip to [topic name]" or "go to [topic name]" to jump to a specific topic.
"""
    session.add_message(role="assistant", content=msg, message_type="system")
    
    return TeachingResponse(
        message=msg,
        topic=state.current_topic or "",
        action_taken="topic_not_found",
        mode=session.mode.value,
        progress=state.to_dict(),
        awaiting_input=True,
        prompt=None
    )


def exit_teaching_mode(session: Session) -> TeachingResponse:
    """Exit the teaching mode"""
    state = session.teaching_state
    state.is_active = False
    session.mode = TeachingMode.FREE_CHAT
    
    msg = f"""
📚 Teaching session paused.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Progress: {state.current_topic_index}/{len(state.syllabus_topics)} topics
Current topic: {state.current_topic}
Topics completed: {len(state.topics_completed)}

You can:
• "continue teaching" - Resume from where you left off
• "start over" - Start from the beginning
• Ask any question about the material
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    session.add_message(role="assistant", content=msg, message_type="system")
    
    return TeachingResponse(
        message=msg,
        topic=state.current_topic or "",
        action_taken="exited_teaching",
        mode=session.mode.value,
        progress=state.to_dict(),
        awaiting_input=False
    )


def resume_teaching(session: Session) -> TeachingResponse:
    """Resume a paused teaching session"""
    state = session.teaching_state
    
    if not state.syllabus_topics:
        return TeachingResponse(
            message="No teaching session to resume. Use 'start teaching' to begin.",
            topic="",
            action_taken="no_session",
            mode=session.mode.value,
            progress=state.to_dict(),
            awaiting_input=False
        )
    
    state.is_active = True
    session.mode = TeachingMode.TEACHING
    
    msg = f"📚 Resuming teaching from: **{state.current_topic}**\n"
    session.add_message(role="assistant", content=msg, message_type="system")
    
    return teach_current_topic(session)
