from groq import Groq
from config import get_groq_key

def classify(query):
    client = Groq(api_key=get_groq_key())
    
    prompt = f"""
Classify intent: explain / practice / revise.
Query: {query}
Return only one word.
"""
    res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    return res.choices[0].message.content.strip()
