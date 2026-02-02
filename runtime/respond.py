from groq import Groq
from config import get_groq_key

def respond(context, query, pace):
    client = Groq(api_key=get_groq_key())

    prompt = f"""
You are S-Core, a syllabus-bounded learning system.

Rules (MANDATORY):
1. Use ONLY the information present in the provided context.
2. Do NOT introduce any concepts not found in the context.
3. If something is not in the context, say: "Not covered in your material."
4. Do NOT mention unrelated topics.
5. Give full theory for each concept, not just names.

Context:
{context}

User question:
{query}

Pace:
{pace}

Output format (STRICT):
THEORY:
(detailed explanation of each relevant concept)

PRACTICE QUESTIONS:
(at least 3)

ANSWERS:
(with explanations)

STEP-BY-STEP SOLUTIONS:
(detailed)
"""
    res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    return res.choices[0].message.content
