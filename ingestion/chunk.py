from typing import List
from dataclasses import dataclass
import re

from config import CHUNK_SIZE, CHUNK_OVERLAP

# ─────────────────────────────────────────────────────────────
# Data Classes
# ─────────────────────────────────────────────────────────────

@dataclass
class Chunk:
    """A semantic text chunk with metadata"""
    content: str
    source_file: str
    chunk_index: int
    char_start: int
    char_end: int

# ─────────────────────────────────────────────────────────────
# Chunking Strategies
# ─────────────────────────────────────────────────────────────

def find_sentence_boundary(text: str, target_pos: int, direction: str = "forward") -> int:
    """
    Find the nearest sentence boundary from target position.
    Looks for: . ! ? followed by space or newline
    """
    sentence_endings = re.compile(r'[.!?]\s')
    
    if direction == "forward":
        # Search forward for next sentence end
        match = sentence_endings.search(text, target_pos)
        if match:
            return match.end()
        return len(text)
    else:
        # Search backward for previous sentence end
        text_before = text[:target_pos]
        matches = list(sentence_endings.finditer(text_before))
        if matches:
            return matches[-1].end()
        return 0

def find_paragraph_boundary(text: str, target_pos: int, direction: str = "forward") -> int:
    """Find the nearest paragraph boundary (double newline)"""
    if direction == "forward":
        idx = text.find('\n\n', target_pos)
        return idx + 2 if idx != -1 else len(text)
    else:
        idx = text.rfind('\n\n', 0, target_pos)
        return idx + 2 if idx != -1 else 0

def semantic_chunk(
    text: str,
    source_file: str = "unknown",
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP
) -> List[Chunk]:
    """
    Split text into semantic chunks respecting sentence boundaries.
    
    Algorithm:
    1. Target chunk_size characters
    2. Find nearest sentence boundary
    3. Create chunk with overlap from previous
    4. Repeat until end
    """
    if not text or not text.strip():
        return []
    
    chunks = []
    text = text.strip()
    text_length = len(text)
    
    current_pos = 0
    chunk_index = 0
    
    while current_pos < text_length:
        # Calculate target end position
        target_end = current_pos + chunk_size
        
        if target_end >= text_length:
            # Last chunk - take everything
            chunk_text = text[current_pos:].strip()
            if chunk_text:
                chunks.append(Chunk(
                    content=chunk_text,
                    source_file=source_file,
                    chunk_index=chunk_index,
                    char_start=current_pos,
                    char_end=text_length
                ))
            break
        
        # Find sentence boundary near target
        sentence_end = find_sentence_boundary(text, target_end, "forward")
        
        # Don't let chunk get too large (1.5x target)
        if sentence_end - current_pos > chunk_size * 1.5:
            # Fall back to finding previous sentence end
            sentence_end = find_sentence_boundary(text, target_end, "backward")
            if sentence_end <= current_pos:
                # No sentence boundary found, just cut at target
                sentence_end = target_end
        
        chunk_text = text[current_pos:sentence_end].strip()
        
        if chunk_text:
            chunks.append(Chunk(
                content=chunk_text,
                source_file=source_file,
                chunk_index=chunk_index,
                char_start=current_pos,
                char_end=sentence_end
            ))
            chunk_index += 1
        
        # Move to next position with overlap
        current_pos = sentence_end - overlap
        if current_pos < 0:
            current_pos = 0
    
    return chunks

def chunk_by_paragraphs(
    text: str,
    source_file: str = "unknown",
    max_chunk_size: int = CHUNK_SIZE * 2
) -> List[Chunk]:
    """
    Split text by paragraphs, merging small ones.
    Good for structured documents with clear sections.
    """
    if not text or not text.strip():
        return []
    
    # Split on double newlines
    paragraphs = [p.strip() for p in re.split(r'\n\n+', text) if p.strip()]
    
    chunks = []
    current_chunk = []
    current_length = 0
    chunk_index = 0
    char_pos = 0
    
    for para in paragraphs:
        para_len = len(para)
        
        if current_length + para_len > max_chunk_size and current_chunk:
            # Save current chunk
            chunk_text = '\n\n'.join(current_chunk)
            chunks.append(Chunk(
                content=chunk_text,
                source_file=source_file,
                chunk_index=chunk_index,
                char_start=char_pos - current_length,
                char_end=char_pos
            ))
            chunk_index += 1
            current_chunk = []
            current_length = 0
        
        current_chunk.append(para)
        current_length += para_len + 2  # +2 for \n\n
        char_pos += para_len + 2
    
    # Don't forget last chunk
    if current_chunk:
        chunk_text = '\n\n'.join(current_chunk)
        chunks.append(Chunk(
            content=chunk_text,
            source_file=source_file,
            chunk_index=chunk_index,
            char_start=char_pos - current_length,
            char_end=char_pos
        ))
    
    return chunks

# ─────────────────────────────────────────────────────────────
# Smart Chunking (Combines Strategies)
# ─────────────────────────────────────────────────────────────

def smart_chunk(
    text_chunks: List[str],
    source_file: str = "unknown"
) -> List[Chunk]:
    """
    Intelligently chunk a list of text blocks.
    Uses paragraph chunking for structured text,
    semantic chunking for dense text.
    """
    all_chunks = []
    
    for text in text_chunks:
        if not text or not text.strip():
            continue
        
        # Check if text has paragraph structure
        has_paragraphs = '\n\n' in text and text.count('\n\n') > 2
        
        if has_paragraphs:
            chunks = chunk_by_paragraphs(text, source_file)
        else:
            chunks = semantic_chunk(text, source_file)
        
        # Renumber chunks globally
        for chunk in chunks:
            chunk.chunk_index = len(all_chunks)
            all_chunks.append(chunk)
    
    return all_chunks

def merge_small_chunks(
    chunks: List[Chunk],
    min_size: int = 100
) -> List[Chunk]:
    """Merge chunks that are too small"""
    if not chunks:
        return []
    
    merged = []
    buffer = None
    
    for chunk in chunks:
        if buffer is None:
            buffer = chunk
        elif len(buffer.content) < min_size:
            # Merge with next chunk
            buffer = Chunk(
                content=buffer.content + "\n\n" + chunk.content,
                source_file=buffer.source_file,
                chunk_index=buffer.chunk_index,
                char_start=buffer.char_start,
                char_end=chunk.char_end
            )
        else:
            merged.append(buffer)
            buffer = chunk
    
    if buffer:
        merged.append(buffer)
    
    return merged
