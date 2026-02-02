from groq import Groq
from config import get_groq_key

def expand_topics(query):
    client = Groq(api_key=get_groq_key())

    prompt = f"""
Given this topic, list important subtopics.

Topic:
{query}

Return as comma separated list.
Do NOT explain.
"""
    res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )

    out = res.choices[0].message.content.strip()
    return [t.strip() for t in out.split(",")]
