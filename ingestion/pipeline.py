import os
import shutil
from typing import List, Tuple, Optional
from dataclasses import dataclass

from ingestion.extract import extract_file, ExtractedContent, get_supported_extensions
from ingestion.image_to_text import process_images
from ingestion.chunk import smart_chunk, merge_small_chunks, Chunk
from ingestion.syllabus_map import map_to_syllabus, parse_syllabus, MappedChunk
from ingestion.embed import embed, embed_batch
from db.chroma import add_documents, get_collection_stats
from db.mongo import add_ingested_file, update_deck_syllabus_topics, get_deck

# ─────────────────────────────────────────────────────────────
# Data Classes
# ─────────────────────────────────────────────────────────────

@dataclass
class IngestionResult:
    """Result of ingesting a file"""
    filename: str
    success: bool
    chunks_created: int
    chunks_filtered: int
    error: Optional[str] = None

@dataclass
class PipelineResult:
    """Result of running the full pipeline"""
    deck_id: str
    files_processed: int
    total_chunks: int
    total_filtered: int
    syllabus_topics: List[str]
    results: List[IngestionResult]

# ─────────────────────────────────────────────────────────────
# Phase A: Raw Extraction
# ─────────────────────────────────────────────────────────────

def extract_content(file_path: str) -> ExtractedContent:
    """
    Extract all content from a file.
    Returns text chunks and images.
    """
    return extract_file(file_path)

# ─────────────────────────────────────────────────────────────
# Phase B: Image Processing
# ─────────────────────────────────────────────────────────────

def process_image_content(images: List[bytes], context: str = "") -> List[str]:
    """
    Convert all images to semantic text.
    No raw images are stored.
    """
    if not images:
        return []
    
    return process_images(images, context)

# ─────────────────────────────────────────────────────────────
# Phase C & D: Text Stream and Merge
# ─────────────────────────────────────────────────────────────

def merge_streams(
    text_chunks: List[str],
    image_texts: List[str],
    source_file: str
) -> List[Chunk]:
    """
    Merge normal text and image-derived text into unified chunks.
    """
    # Combine all text sources
    all_text = text_chunks + image_texts
    
    # Smart chunking
    chunks = smart_chunk(all_text, source_file)
    
    # Merge small chunks
    chunks = merge_small_chunks(chunks, min_size=100)
    
    return chunks

# ─────────────────────────────────────────────────────────────
# Phase E: Syllabus Mapping
# ─────────────────────────────────────────────────────────────

def filter_by_syllabus(
    chunks: List[Chunk],
    syllabus: str,
    source_file: str,
    syllabus_topics: List[str] = None
) -> Tuple[List[MappedChunk], int]:
    """
    Filter chunks by syllabus.
    Returns (mapped_chunks, filtered_count)
    """
    chunk_texts = [c.content for c in chunks]
    
    mapped = map_to_syllabus(
        chunk_texts, syllabus, source_file,
        syllabus_topics=syllabus_topics
    )
    filtered_count = len(chunks) - len(mapped)
    
    return mapped, filtered_count

# ─────────────────────────────────────────────────────────────
# Phase F: Embedding & Storage
# ─────────────────────────────────────────────────────────────

def embed_and_store(
    user_id: str,
    deck_id: str,
    mapped_chunks: List[MappedChunk]
) -> int:
    """
    Embed chunks and store in Chroma.
    Returns number of chunks stored.
    """
    if not mapped_chunks:
        return 0
    
    # Prepare documents and metadata
    documents = [c.content for c in mapped_chunks]
    metadatas = [
        {
            "source_file": c.source_file,
            "topics": ",".join(c.topics),
            "relevance": c.relevance_score
        }
        for c in mapped_chunks
    ]
    
    # Batch embed
    embeddings = embed_batch(documents)
    
    # Store in Chroma
    return add_documents(
        user_id=user_id,
        deck_id=deck_id,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )

# ─────────────────────────────────────────────────────────────
# Single File Ingestion
# ─────────────────────────────────────────────────────────────

def ingest_single_file(
    file_path: str,
    filename: str,
    syllabus: str,
    user_id: str,
    deck_id: str,
    syllabus_topics: List[str] = None
) -> IngestionResult:
    """
    Ingest a single file through the full pipeline.
    """
    try:
        # Phase A: Extract
        extracted = extract_content(file_path)
        
        # Phase B: Process images
        image_texts = process_image_content(extracted.images)
        
        # Phase C & D: Merge streams
        chunks = merge_streams(
            extracted.text_chunks,
            image_texts,
            filename
        )
        
        # Phase E: Syllabus filter (pass pre-parsed topics to avoid re-parsing)
        mapped_chunks, filtered_count = filter_by_syllabus(
            chunks, syllabus, filename,
            syllabus_topics=syllabus_topics
        )
        
        # Phase F: Embed and store
        stored_count = embed_and_store(user_id, deck_id, mapped_chunks)
        
        # Record in MongoDB
        add_ingested_file(deck_id, filename, stored_count)
        
        return IngestionResult(
            filename=filename,
            success=True,
            chunks_created=stored_count,
            chunks_filtered=filtered_count
        )
        
    except Exception as e:
        return IngestionResult(
            filename=filename,
            success=False,
            chunks_created=0,
            chunks_filtered=0,
            error=str(e)
        )

# ─────────────────────────────────────────────────────────────
# Main Pipeline Entry Point
# ─────────────────────────────────────────────────────────────

def ingest_files(
    files: List,  # List of UploadFile or file paths
    syllabus: str,
    user_id: str,
    deck_id: str
) -> PipelineResult:
    """
    Main ingestion pipeline.
    Processes all files for a deck.
    
    Args:
        files: List of uploaded files or file paths
        syllabus: Syllabus text for filtering
        user_id: Owner's user ID
        deck_id: Target deck ID
        
    Returns:
        PipelineResult with statistics
    """
    print(f"\n{'='*60}")
    print(f"🚀 Starting S-Core Ingestion Pipeline")
    print(f"   Deck: {deck_id}")
    print(f"   Files: {len(files)}")
    print(f"{'='*60}\n")
    
    # Parse syllabus topics
    syllabus_topics = parse_syllabus(syllabus)
    update_deck_syllabus_topics(deck_id, syllabus_topics)
    print(f"✓ Parsed {len(syllabus_topics)} syllabus topics")
    
    results = []
    total_chunks = 0
    total_filtered = 0
    
    for file in files:
        # Handle both UploadFile objects and file paths
        if hasattr(file, 'filename'):
            # It's an UploadFile
            filename = file.filename
            temp_path = f"/tmp/{filename}"
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            file_path = temp_path
            cleanup = True
        else:
            # It's a file path string
            file_path = file
            filename = os.path.basename(file)
            cleanup = False
        
        print(f"\n📄 Processing: {filename}")
        
        result = ingest_single_file(
            file_path=file_path,
            filename=filename,
            syllabus=syllabus,
            user_id=user_id,
            deck_id=deck_id,
            syllabus_topics=syllabus_topics
        )
        
        results.append(result)
        total_chunks += result.chunks_created
        total_filtered += result.chunks_filtered
        
        if result.success:
            print(f"   ✓ {result.chunks_created} chunks stored, {result.chunks_filtered} filtered")
        else:
            print(f"   ✗ Error: {result.error}")
        
        # Cleanup temp file
        if cleanup and os.path.exists(file_path):
            os.remove(file_path)
    
    # Final stats
    stats = get_collection_stats(user_id, deck_id)
    
    print(f"\n{'='*60}")
    print(f"✅ Ingestion Complete")
    print(f"   Total chunks in deck: {stats['total_documents']}")
    print(f"   Syllabus topics: {len(syllabus_topics)}")
    print(f"{'='*60}\n")
    
    return PipelineResult(
        deck_id=deck_id,
        files_processed=len(files),
        total_chunks=total_chunks,
        total_filtered=total_filtered,
        syllabus_topics=syllabus_topics,
        results=results
    )

# ─────────────────────────────────────────────────────────────
# Legacy Interface (backward compatibility)
# ─────────────────────────────────────────────────────────────

def ingest_files_legacy(files, syllabus):
    """Legacy interface for backward compatibility"""
    from db.chroma import get_chroma
    
    result = ingest_files(
        files=files,
        syllabus=syllabus,
        user_id="default_user",
        deck_id="default"
    )
    
    return get_chroma("default")
