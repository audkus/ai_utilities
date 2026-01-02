"""
Knowledge search functionality.

This module provides semantic search capabilities over the indexed knowledge base,
using vector similarity to find relevant chunks.
"""

from __future__ import annotations

import logging
from typing import List, Optional, Dict, Any

from .backend import SqliteVectorBackend
from .exceptions import KnowledgeSearchError
from .models import Chunk, SearchHit

logger = logging.getLogger(__name__)


class KnowledgeSearch:
    """Semantic search over indexed knowledge."""
    
    def __init__(
        self,
        backend: SqliteVectorBackend,
        embedding_client,
        embedding_model: str = "text-embedding-3-small",
    ) -> None:
        """
        Initialize the knowledge search system.
        
        Args:
            backend: SQLite vector storage backend
            embedding_client: Client for generating embeddings
            embedding_model: Name of the embedding model to use
        """
        self.backend = backend
        self.embedding_client = embedding_client
        self.embedding_model = embedding_model
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.0,
        include_metadata: bool = True,
    ) -> List[SearchHit]:
        """
        Search for similar chunks based on a query.
        
        Args:
            query: Search query text
            top_k: Number of results to return
            similarity_threshold: Minimum similarity threshold (0.0-1.0)
            include_metadata: Whether to include chunk metadata in results
            
        Returns:
            List of search hits sorted by similarity
        """
        if not query.strip():
            return []
        
        try:
            # Generate query embedding
            query_embedding = self._generate_query_embedding(query)
            
            # Search for similar chunks
            similar_chunks = self.backend.search_similar(
                query_embedding,
                top_k=top_k * 2,  # Get more candidates to filter
                similarity_threshold=similarity_threshold,
            )
            
            # Convert to SearchHit objects
            hits = []
            for rank, (chunk_id, similarity_score) in enumerate(similar_chunks[:top_k], 1):
                chunk = self.backend.get_chunk(chunk_id)
                if chunk:
                    # Get source path
                    source_path = self._get_source_path(chunk.source_id)
                    
                    hit = SearchHit.from_chunk(
                        chunk=chunk,
                        similarity_score=similarity_score,
                        rank=rank,
                        source_path=source_path,
                    )
                    
                    # Optionally filter metadata
                    if not include_metadata:
                        hit.chunk.metadata = {}
                    
                    hits.append(hit)
            
            return hits
            
        except Exception as e:
            raise KnowledgeSearchError(f"Search failed: {e}")
    
    def search_with_context(
        self,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.0,
        context_chars: int = 200,
    ) -> List[SearchHit]:
        """
        Search with additional context around each hit.
        
        Args:
            query: Search query text
            top_k: Number of results to return
            similarity_threshold: Minimum similarity threshold
            context_chars: Number of characters to include as context
            
        Returns:
            List of search hits with expanded context
        """
        hits = self.search(query, top_k, similarity_threshold)
        
        # Add context to each hit
        for hit in hits:
            context = self._get_context(hit.chunk, context_chars)
            if context:
                # Create a new chunk with context
                context_chunk = Chunk(
                    chunk_id=hit.chunk.chunk_id + "_context",
                    source_id=hit.chunk.source_id,
                    text=context,
                    metadata=hit.chunk.metadata,
                    chunk_index=hit.chunk.chunk_index,
                    start_char=max(0, hit.chunk.start_char - context_chars),
                    end_char=hit.chunk.end_char + context_chars,
                    embedding=hit.chunk.embedding,
                    embedding_model=hit.chunk.embedding_model,
                    embedded_at=hit.chunk.embedded_at,
                )
                
                # Update hit with context
                hit.chunk = context_chunk
                hit.text = context
        
        return hits
    
    def find_similar_chunks(
        self,
        chunk_id: str,
        top_k: int = 5,
        similarity_threshold: float = 0.0,
    ) -> List[SearchHit]:
        """
        Find chunks similar to a specific chunk.
        
        Args:
            chunk_id: ID of the reference chunk
            top_k: Number of results to return
            similarity_threshold: Minimum similarity threshold
            
        Returns:
            List of similar chunks
        """
        # Get the reference chunk
        reference_chunk = self.backend.get_chunk(chunk_id)
        if not reference_chunk:
            raise KnowledgeSearchError(f"Chunk not found: {chunk_id}")
        
        if not reference_chunk.embedding:
            raise KnowledgeSearchError(f"Chunk has no embedding: {chunk_id}")
        
        try:
            # Search using the chunk's embedding
            similar_chunks = self.backend.search_similar(
                reference_chunk.embedding,
                top_k=top_k + 1,  # +1 to exclude the reference chunk itself
                similarity_threshold=similarity_threshold,
            )
            
            # Convert to SearchHit objects, excluding the reference chunk
            hits = []
            rank = 1
            for similar_chunk_id, similarity_score in similar_chunks:
                if similar_chunk_id == chunk_id:
                    continue  # Skip the reference chunk itself
                
                chunk = self.backend.get_chunk(similar_chunk_id)
                if chunk:
                    source_path = self._get_source_path(chunk.source_id)
                    
                    hit = SearchHit.from_chunk(
                        chunk=chunk,
                        similarity_score=similarity_score,
                        rank=rank,
                        source_path=source_path,
                    )
                    hits.append(hit)
                    rank += 1
                
                if len(hits) >= top_k:
                    break
            
            return hits
            
        except Exception as e:
            raise KnowledgeSearchError(f"Similar chunk search failed: {e}")
    
    def _generate_query_embedding(self, query: str) -> List[float]:
        """Generate embedding for the search query."""
        try:
            embeddings = self.embedding_client.get_embeddings([query], model=self.embedding_model)
            if not embeddings:
                raise KnowledgeSearchError("No embedding generated for query")
            return embeddings[0]
        except Exception as e:
            raise KnowledgeSearchError(f"Failed to generate query embedding: {e}")
    
    def _get_source_path(self, source_id: str) -> Optional[str]:
        """Get the file path for a source ID."""
        try:
            with self.backend._get_connection() as conn:
                cursor = conn.execute(
                    "SELECT path FROM sources WHERE source_id = ?", 
                    (source_id,)
                )
                row = cursor.fetchone()
                return row[0] if row else None
        except Exception:
            return None
    
    def _get_context(self, chunk: Chunk, context_chars: int) -> str:
        """Get context around a chunk."""
        try:
            # Get all chunks from the same source
            source_chunks = self.backend.get_source_chunks(chunk.source_id)
            
            # Find chunks before and after
            context_chunks = []
            for source_chunk in source_chunks:
                if (source_chunk.start_char <= chunk.start_char + context_chars and
                    source_chunk.end_char >= chunk.start_char - context_chars):
                    context_chunks.append(source_chunk)
            
            if not context_chunks:
                return chunk.text
            
            # Sort by position and merge
            context_chunks.sort(key=lambda c: c.start_char)
            merged_text = " ".join(c.text for c in context_chunks)
            
            return merged_text
            
        except Exception:
            # Fallback to original chunk text
            return chunk.text
    
    def get_search_stats(self) -> Dict[str, Any]:
        """Get search system statistics."""
        backend_stats = self.backend.get_stats()
        
        return {
            'backend': backend_stats,
            'embedding': {
                'model': self.embedding_model,
                'dimension': self.backend.embedding_dimension,
            },
            'search_capabilities': {
                'semantic_search': True,
                'context_search': True,
                'similar_chunks': True,
                'extension_accelerated': backend_stats.get('extension_available', False),
            },
        }
