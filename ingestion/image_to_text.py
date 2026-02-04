"""
Image to Text Processing Module for S-Core
Converts all images to semantic text:
- Diagrams → descriptions
- Graphs → data interpretations  
- Flowcharts → process descriptions
- Handwritten notes → transcriptions
- Scanned pages → OCR text

No raw images are stored - only semantic text.
"""

import io
import base64
from typing import List, Optional

import pytesseract
from PIL import Image
from groq import Groq

from config import get_groq_key, GROQ_MODEL

# ─────────────────────────────────────────────────────────────
# OCR Processing
# ─────────────────────────────────────────────────────────────

def ocr_image(image_data: bytes) -> str:
    """
    Extract text from image using OCR.
    Returns extracted text or empty string.
    """
    try:
        image = Image.open(io.BytesIO(image_data))
        text = pytesseract.image_to_string(image)
        return text.strip()
    except Exception as e:
        print(f"OCR failed: {e}")
        return ""

def is_text_sufficient(text: str, min_chars: int = 50) -> bool:
    """Check if OCR extracted enough meaningful text"""
    if not text:
        return False
    # Remove whitespace and check length
    clean = ''.join(text.split())
    return len(clean) >= min_chars

# ─────────────────────────────────────────────────────────────
# LLM Image Description
# ─────────────────────────────────────────────────────────────

def describe_image_with_llm(image_data: bytes, context: str = "") -> str:
    """
    Use LLM to generate semantic description of an image.
    For diagrams, graphs, flowcharts that OCR cannot handle.
    
    Note: Groq currently doesn't support vision models directly,
    so we use OCR output + context to generate descriptions.
    If you have access to a vision model, update this function.
    """
    client = Groq(api_key=get_groq_key())
    
    # Try OCR first to get any text hints
    ocr_text = ocr_image(image_data)
    
    prompt = f"""You are analyzing an academic image/diagram.

OCR detected text (may be partial or garbled):
{ocr_text if ocr_text else "No text detected"}

Additional context:
{context if context else "No additional context"}

Based on this information, provide a detailed academic description of what this image likely contains.
Focus on:
1. Type of diagram/image (flowchart, graph, table, formula, etc.)
2. Key concepts or data shown
3. Relationships between elements
4. Any numerical values or labels

If the OCR text is unclear, make reasonable inferences based on common academic diagrams.
Write in clear, academic prose that could replace the image in study notes.
"""

    try:
        res = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500
        )
        return res.choices[0].message.content.strip()
    except Exception as e:
        print(f"LLM description failed: {e}")
        return ocr_text if ocr_text else ""

# ─────────────────────────────────────────────────────────────
# Main Processing Pipeline
# ─────────────────────────────────────────────────────────────

def image_to_text(image_data: bytes, context: str = "") -> str:
    """
    Convert image to semantic text.
    
    Pipeline:
    1. Try OCR extraction
    2. If OCR has sufficient text → return it
    3. If OCR is insufficient → use LLM to describe
    
    Args:
        image_data: Raw image bytes
        context: Optional context about what the image might contain
        
    Returns:
        Semantic text representation of the image
    """
    # Step 1: OCR
    ocr_text = ocr_image(image_data)
    
    # Step 2: Check if OCR is sufficient
    if is_text_sufficient(ocr_text):
        return f"[Image Text]\n{ocr_text}"
    
    # Step 3: LLM description for diagrams/graphs
    description = describe_image_with_llm(image_data, context)
    
    if description:
        return f"[Image Description]\n{description}"
    
    # Fallback: return any OCR text we got
    if ocr_text:
        return f"[Partial Image Text]\n{ocr_text}"
    
    return ""

def process_images(images: List[bytes], context: str = "") -> List[str]:
    """
    Process multiple images and return semantic text for each.
    Filters out empty results.
    """
    results = []
    for i, img_data in enumerate(images):
        text = image_to_text(img_data, context)
        if text:
            results.append(text)
    return results

# ─────────────────────────────────────────────────────────────
# Image File Handler (for standalone image files)
# ─────────────────────────────────────────────────────────────

def process_image_file(path: str, context: str = "") -> str:
    """Process an image file and return semantic text"""
    with open(path, 'rb') as f:
        image_data = f.read()
    return image_to_text(image_data, context)
