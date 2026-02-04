"""
S-Core Ingestion Package
Handles all document processing and ingestion into the knowledge base.

Modules:
- extract: File extraction for all formats
- chunk: Semantic text chunking
- image_to_text: Image to text conversion
- syllabus_map: Syllabus-based filtering
- embed: Text embedding
- pipeline: Main ingestion pipeline
"""

from ingestion.pipeline import ingest_files
from ingestion.extract import extract_file, get_supported_extensions
from ingestion.embed import embed, embed_batch
from ingestion.chunk import smart_chunk
from ingestion.syllabus_map import map_to_syllabus
from ingestion.image_to_text import image_to_text

__all__ = [
    "ingest_files",
    "extract_file",
    "get_supported_extensions",
    "embed",
    "embed_batch",
    "smart_chunk",
    "map_to_syllabus",
    "image_to_text"
]
