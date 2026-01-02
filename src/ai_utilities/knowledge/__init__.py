"""
Knowledge Index and Vector Search for AI Utilities.

This module provides local-first knowledge indexing and semantic search capabilities
using SQLite for storage and embeddings for semantic similarity.

Features:
- File-based knowledge indexing with change detection
- Configurable chunking with overlap
- SQLite vector storage with extension support
- Semantic search with cosine similarity
- Integration with AI client for RAG capabilities
"""

from .models import Source, Chunk, SearchHit
from .chunking import TextChunker
from .sources import FileSourceLoader
from .indexer import KnowledgeIndexer
from .search import KnowledgeSearch
from .backend import SqliteVectorBackend
from .exceptions import (
    KnowledgeDisabledError,
    SqliteExtensionUnavailableError,
    KnowledgeIndexError,
    KnowledgeSearchError
)

__all__ = [
    # Models
    "Source",
    "Chunk", 
    "SearchHit",
    # Core components
    "TextChunker",
    "FileSourceLoader",
    "KnowledgeIndexer",
    "KnowledgeSearch",
    "SqliteVectorBackend",
    # Exceptions
    "KnowledgeDisabledError",
    "SqliteExtensionUnavailableError", 
    "KnowledgeIndexError",
    "KnowledgeSearchError",
]
