from groq import Groq
from config import get_groq_key

def map_to_syllabus(chunk, syllabus):
    client = Groq(api_key=get_groq_key())

    prompt = f"""
Syllabus topics:
{syllabus}

Text:
{chunk}

Return relevant topics as comma list.
If none, return NONE.
"""
    res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    out = res.choices[0].message.content.strip()
    if out == "NONE":
        return []
    return [t.strip() for t in out.split(",")]
