from typing import List, Optional
from dataclasses import dataclass
from enum import Enum
import json

from groq import Groq
from config import get_groq_key, GROQ_MODEL, PACE_CONFIG

# ─────────────────────────────────────────────────────────────
# Data Classes
# ─────────────────────────────────────────────────────────────

class QuestionType(Enum):
    CONCEPTUAL = "conceptual"
    APPLICATION = "application"
    NUMERICAL = "numerical"

@dataclass
class PracticeQuestion:
    """A generated practice question with solution"""
    question_type: QuestionType
    question: str
    answer: str
    solution_steps: List[str]
    difficulty: str  # easy, medium, hard
    topic: str

@dataclass
class PracticeSet:
    """A set of practice questions for a topic"""
    topic: str
    questions: List[PracticeQuestion]
    theory_summary: str

# ─────────────────────────────────────────────────────────────
# Question Generation
# ─────────────────────────────────────────────────────────────

def generate_conceptual_questions(
    context: str,
    topic: str,
    count: int = 2
) -> List[PracticeQuestion]:
    """Generate conceptual/theory questions"""
    client = Groq(api_key=get_groq_key())
    
    prompt = f"""Generate {count} conceptual questions about this topic.

Topic: {topic}
Context: {context}

Types of conceptual questions:
- Definitions: "What is X?"
- Explanations: "Explain how X works"
- Comparisons: "Compare X and Y"
- Advantages/Disadvantages: "What are the benefits of X?"

For EACH question, return a JSON object with:
- "question": the question text
- "answer": concise final answer
- "solution_steps": array of explanation steps
- "difficulty": "easy", "medium", or "hard"

Return as a JSON array of objects.
Return ONLY the JSON array.
"""

    try:
        res = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000
        )
        
        response = res.choices[0].message.content.strip()
        
        # Parse JSON
        if response.startswith("```"):
            response = response.split("```")[1]
            if response.startswith("json"):
                response = response[4:]
        
        questions_data = json.loads(response)
        
        return [
            PracticeQuestion(
                question_type=QuestionType.CONCEPTUAL,
                question=q["question"],
                answer=q["answer"],
                solution_steps=q.get("solution_steps", []),
                difficulty=q.get("difficulty", "medium"),
                topic=topic
            )
            for q in questions_data
        ]
        
    except Exception as e:
        print(f"Conceptual question generation failed: {e}")
        return []

def generate_application_questions(
    context: str,
    topic: str,
    count: int = 2
) -> List[PracticeQuestion]:
    """Generate application-based questions"""
    client = Groq(api_key=get_groq_key())
    
    prompt = f"""Generate {count} application-based questions about this topic.

Topic: {topic}
Context: {context}

Types of application questions:
- Scenario analysis: "Given this situation, what would happen?"
- Tracing: "Trace through this algorithm/process"
- Classification: "Which category does this belong to?"
- Problem-solving: "How would you solve this problem using X?"

For EACH question, return a JSON object with:
- "question": the question text (include scenario details)
- "answer": concise final answer
- "solution_steps": array of step-by-step solution
- "difficulty": "easy", "medium", or "hard"

Return as a JSON array of objects.
Return ONLY the JSON array.
"""

    try:
        res = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000
        )
        
        response = res.choices[0].message.content.strip()
        
        if response.startswith("```"):
            response = response.split("```")[1]
            if response.startswith("json"):
                response = response[4:]
        
        questions_data = json.loads(response)
        
        return [
            PracticeQuestion(
                question_type=QuestionType.APPLICATION,
                question=q["question"],
                answer=q["answer"],
                solution_steps=q.get("solution_steps", []),
                difficulty=q.get("difficulty", "medium"),
                topic=topic
            )
            for q in questions_data
        ]
        
    except Exception as e:
        print(f"Application question generation failed: {e}")
        return []

def generate_numerical_questions(
    context: str,
    topic: str,
    count: int = 2
) -> List[PracticeQuestion]:
    """Generate numerical/quantitative questions"""
    client = Groq(api_key=get_groq_key())
    
    prompt = f"""Generate {count} numerical/quantitative questions about this topic.

Topic: {topic}
Context: {context}

Types of numerical questions:
- CPU scheduling calculations (turnaround time, waiting time)
- Memory management (page faults, fragmentation)
- Networking (subnetting, bandwidth)
- Database (normalization, query optimization)
- Algorithm complexity (time/space analysis)
- Any calculation relevant to the topic

For EACH question, return a JSON object with:
- "question": the question with specific numbers/data
- "answer": the calculated final answer with units
- "solution_steps": array of detailed calculation steps
- "difficulty": "easy", "medium", or "hard"

If numerical questions don't apply to this topic, generate calculation-adjacent questions.

Return as a JSON array of objects.
Return ONLY the JSON array.
"""

    try:
        res = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000
        )
        
        response = res.choices[0].message.content.strip()
        
        if response.startswith("```"):
            response = response.split("```")[1]
            if response.startswith("json"):
                response = response[4:]
        
        questions_data = json.loads(response)
        
        return [
            PracticeQuestion(
                question_type=QuestionType.NUMERICAL,
                question=q["question"],
                answer=q["answer"],
                solution_steps=q.get("solution_steps", []),
                difficulty=q.get("difficulty", "medium"),
                topic=topic
            )
            for q in questions_data
        ]
        
    except Exception as e:
        print(f"Numerical question generation failed: {e}")
        return []

# ─────────────────────────────────────────────────────────────
# Pace-Aware Generation
# ─────────────────────────────────────────────────────────────

def generate_practice_set(
    context: str,
    topic: str,
    pace: str = "medium"
) -> PracticeSet:
    """
    Generate a complete practice set based on pace setting.
    
    Pace affects theory vs practice ratio:
    - slow: 70% theory, 30% practice (fewer questions, more explanation)
    - medium: 50% theory, 50% practice (balanced)
    - fast: 30% theory, 70% practice (more questions, less explanation)
    """
    config = PACE_CONFIG.get(pace, PACE_CONFIG["medium"])
    practice_ratio = config["practice"]
    
    # Calculate question counts based on practice ratio
    if pace == "slow":
        conceptual_count = 1
        application_count = 1
        numerical_count = 1
    elif pace == "fast":
        conceptual_count = 2
        application_count = 3
        numerical_count = 2
    else:  # medium
        conceptual_count = 2
        application_count = 2
        numerical_count = 1
    
    # Generate questions
    questions = []
    questions.extend(generate_conceptual_questions(context, topic, conceptual_count))
    questions.extend(generate_application_questions(context, topic, application_count))
    questions.extend(generate_numerical_questions(context, topic, numerical_count))
    
    # Generate theory summary based on pace
    theory_summary = generate_theory_summary(context, topic, pace)
    
    return PracticeSet(
        topic=topic,
        questions=questions,
        theory_summary=theory_summary
    )

def generate_theory_summary(
    context: str,
    topic: str,
    pace: str = "medium"
) -> str:
    """Generate theory summary based on pace"""
    client = Groq(api_key=get_groq_key())
    
    depth_instructions = {
        "slow": "Provide a comprehensive, detailed explanation with examples. Cover all nuances.",
        "medium": "Provide a balanced explanation with key points and one example.",
        "fast": "Provide a brief summary with only essential points for quick revision."
    }
    
    prompt = f"""Explain this topic based on the provided context.

Topic: {topic}
Context: {context}

Instructions: {depth_instructions.get(pace, depth_instructions["medium"])}

IMPORTANT:
- Use ONLY information from the context
- Do NOT add external knowledge
- If something is not in the context, say "Not covered in your material"
"""

    try:
        res = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1500 if pace == "slow" else 800 if pace == "medium" else 400
        )
        return res.choices[0].message.content.strip()
    except Exception as e:
        print(f"Theory summary generation failed: {e}")
        return ""

# ─────────────────────────────────────────────────────────────
# Formatting
# ─────────────────────────────────────────────────────────────

def format_practice_set(practice_set: PracticeSet) -> str:
    """Format a practice set for display"""
    output = []
    
    # Theory section
    output.append("=" * 60)
    output.append(f"📚 TOPIC: {practice_set.topic}")
    output.append("=" * 60)
    output.append("")
    output.append("📖 THEORY")
    output.append("-" * 40)
    output.append(practice_set.theory_summary)
    output.append("")
    
    # Questions section
    output.append("📝 PRACTICE QUESTIONS")
    output.append("-" * 40)
    
    for i, q in enumerate(practice_set.questions, 1):
        type_emoji = {
            QuestionType.CONCEPTUAL: "💭",
            QuestionType.APPLICATION: "🔧",
            QuestionType.NUMERICAL: "🔢"
        }
        
        output.append(f"\n{type_emoji.get(q.question_type, '❓')} Question {i} ({q.question_type.value.upper()}) [{q.difficulty}]")
        output.append(f"Q: {q.question}")
        output.append("")
        output.append(f"✅ Answer: {q.answer}")
        output.append("")
        output.append("📋 Solution Steps:")
        for j, step in enumerate(q.solution_steps, 1):
            output.append(f"   {j}. {step}")
        output.append("")
    
    return "\n".join(output)

def format_question(question: PracticeQuestion) -> str:
    """Format a single question for display"""
    lines = [
        f"**Question** ({question.question_type.value}, {question.difficulty})",
        question.question,
        "",
        f"**Answer:** {question.answer}",
        "",
        "**Solution:**"
    ]
    for i, step in enumerate(question.solution_steps, 1):
        lines.append(f"{i}. {step}")
    
    return "\n".join(lines)
