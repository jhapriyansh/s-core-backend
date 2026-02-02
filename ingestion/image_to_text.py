from groq import Groq
from config import get_groq_key
import pytesseract
from PIL import Image

def image_to_text(path):
    text = pytesseract.image_to_string(Image.open(path))
    if len(text.strip()) > 30:
        return text
    
    client = Groq(api_key=get_groq_key())
    prompt = f"Describe this diagram in academic text."
    
    res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    return res.choices[0].message.content
