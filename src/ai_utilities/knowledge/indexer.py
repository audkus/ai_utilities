"""
Knowledge indexing functionality.

This module provides the main indexing logic for processing files,
chunking text, generating embeddings, and storing them in the vector database.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Set, Dict, Any

from .backend import SqliteVectorBackend
from .chunking import TextChunker
from .exceptions import KnowledgeIndexError, KnowledgeValidationError
from .sources import FileSourceLoader

logger = logging.getLogger(__name__)


class KnowledgeIndexer:
    """Main knowledge indexing system."""
    
    def __init__(
        self,
        backend: SqliteVectorBackend,
        file_loader: FileSourceLoader,
        chunker: TextChunker,
        embedding_client,
        embedding_model: str = "text-embedding-3-small",
    ) -> None:
        """
        Initialize the knowledge indexer.
        
        Args:
            backend: SQLite vector storage backend
            file_loader: File source loader
            chunker: Text chunker
            embedding_client: Client for generating embeddings
            embedding_model: Name of the embedding model to use
        """
        self.backend = backend
        self.file_loader = file_loader
        self.chunker = chunker
        self.embedding_client = embedding_client
        self.embedding_model = embedding_model
    
    def index_directory(
        self,
        directory: Path,
        recursive: bool = True,
        force_reindex: bool = False,
    ) -> Dict[str, Any]:
        """
        Index all supported files in a directory.
        
        Args:
            directory: Directory to index
            recursive: Whether to search subdirectories
            force_reindex: Whether to force reindexing all files
            
        Returns:
            Dictionary with indexing statistics
        """
        if not directory.exists():
            raise KnowledgeIndexError(f"Directory does not exist: {directory}")
        
        if not directory.is_dir():
            raise KnowledgeIndexError(f"Path is not a directory: {directory}")
        
        # Find all files to process
        files = self._find_files(directory, recursive)
        
        return self.index_files(files, force_reindex)
    
    def index_files(
        self,
        files: List[Path],
        force_reindex: bool = False,
    ) -> Dict[str, Any]:
        """
        Index a specific list of files.
        
        Args:
            files: List of files to index
            force_reindex: Whether to force reindexing all files
            
        Returns:
            Dictionary with indexing statistics
        """
        stats = {
            'total_files': len(files),
            'processed_files': 0,
            'skipped_files': 0,
            'error_files': 0,
            'total_chunks': 0,
            'total_embeddings': 0,
            'processing_time': 0.0,
            'errors': [],
        }
        
        start_time = datetime.utcnow()
        
        # Get existing sources to check for changes
        existing_sources = set(self.backend.get_existing_sources())
        
        for file_path in files:
            try:
                result = self._index_file(file_path, existing_sources, force_reindex)
                
                if result['processed']:
                    stats['processed_files'] += 1
                    stats['total_chunks'] += result['chunks_created']
                    stats['total_embeddings'] += result['embeddings_created']
                elif result['skipped']:
                    stats['skipped_files'] += 1
                else:
                    stats['error_files'] += 1
                    stats['errors'].append(f"{file_path}: {result['error']}")
                    
            except KnowledgeIndexError as e:
                # Re-raise KnowledgeIndexError as requested
                stats['error_files'] += 1
                error_msg = f"{file_path}: {str(e)}"
                stats['errors'].append(error_msg)
                logger.error(f"Failed to index file {file_path}: {e}")
                raise
            except KnowledgeValidationError as e:
                # Validation errors (like unsupported file types) should be counted as errors, not raised
                stats['error_files'] += 1
                error_msg = f"{file_path}: {str(e)}"
                stats['errors'].append(error_msg)
                logger.error(f"Validation error for {file_path}: {e}")
            except Exception as e:
                stats['error_files'] += 1
                error_msg = f"{file_path}: {str(e)}"
                stats['errors'].append(error_msg)
                logger.error(f"Failed to index file {file_path}: {e}")
                # Wrap other exceptions as KnowledgeIndexError
                raise KnowledgeIndexError(f"Failed to index {file_path}: {str(e)}") from e
        
        end_time = datetime.utcnow()
        stats['processing_time'] = (end_time - start_time).total_seconds()
        
        # Clean up stale files (files that were indexed but no longer exist)
        current_file_ids = {str(f) for f in files}
        stale_sources = existing_sources - current_file_ids
        if stale_sources:
            logger.info(f"Cleaning up {len(stale_sources)} stale sources")
            for source_id in stale_sources:
                try:
                    self.backend.delete_source(source_id)
                    logger.debug(f"Deleted stale source: {source_id}")
                except Exception as e:
                    logger.warning(f"Failed to delete stale source {source_id}: {e}")
        
        logger.info(
            f"Indexing completed: {stats['processed_files']} processed, "
            f"{stats['skipped_files']} skipped, {stats['error_files']} errors, "
            f"{stats['total_chunks']} chunks created"
        )
        
        return stats
    
    def _index_file(
        self,
        file_path: Path,
        existing_sources: Set[str],
        force_reindex: bool,
    ) -> Dict[str, Any]:
        """
        Index a single file.
        
        Returns:
            Dictionary with processing result
        """
        result = {
            'processed': False,
            'skipped': False,
            'chunks_created': 0,
            'embeddings_created': 0,
            'error': None,
            'source_id': None,  # Track source_id for cleanup
        }
        
        source_created = False
        chunks_stored = False
        
        try:
            # Load source
            source = self.file_loader.load_source(file_path)
            source_id = source.source_id
            result['source_id'] = source_id  # Store for cleanup
            
            # Check if we need to reindex
            if not force_reindex and source_id in existing_sources:
                existing_hash = self.backend.get_source_hash(source_id)
                if existing_hash == source.sha256_hash:
                    logger.debug(f"Skipping unchanged file: {file_path}")
                    result['skipped'] = True
                    return result
            
            # Extract text content
            text_content = self.file_loader.extract_text(source)
            
            if not text_content.strip():
                logger.debug(f"Skipping empty file: {file_path}")
                result['skipped'] = True
                return result
            
            # Create chunks
            try:
                chunks = self.chunker.chunk_text(text_content, source_id)
            except Exception as e:
                raise KnowledgeIndexError(f"Failed to chunk text from {file_path}: {str(e)}") from e
            
            if not chunks:
                logger.debug(f"No chunks created from file: {file_path}")
                result['skipped'] = True
                return result
            
            # Generate embeddings
            try:
                embeddings = self._generate_embeddings([chunk.text for chunk in chunks])
            except Exception as e:
                raise KnowledgeIndexError(f"Failed to generate embeddings for {file_path}: {str(e)}") from e
            
            if len(embeddings) != len(chunks):
                raise KnowledgeIndexError(
                    f"Embedding count mismatch: expected {len(chunks)}, got {len(embeddings)}"
                )
            
            # Attach embeddings to chunks
            now = datetime.utcnow()
            for chunk, embedding in zip(chunks, embeddings):
                chunk.embedding = embedding
                chunk.embedding_model = self.embedding_model
                chunk.embedded_at = now
            
            # Update source metadata
            source.chunk_count = len(chunks)
            source.indexed_at = now
            
            # Check if this is a reindex of an existing source
            is_reindex = source_id in existing_sources
            
            # Delete old chunks for this source if reindexing (before adding new ones)
            if is_reindex:
                # Only delete the old chunks, not the source record
                self.backend.delete_chunks_for_source(source_id)
            
            # Store source first (required for foreign key constraint)
            try:
                self.backend.upsert_source(source)
                source_created = True
            except Exception as e:
                raise KnowledgeIndexError(f"Failed to store source for {file_path}: {str(e)}") from e
            
            # Store chunks
            try:
                for chunk in chunks:
                    self.backend.upsert_chunk(chunk)
                chunks_stored = True
            except Exception as e:
                raise KnowledgeIndexError(f"Failed to store chunks for {file_path}: {str(e)}") from e
            
            result['processed'] = True
            result['chunks_created'] = len(chunks)
            result['embeddings_created'] = len(chunks)
            
            logger.info(f"Indexed file: {file_path} ({len(chunks)} chunks)")
            
        except Exception as e:
            # Clean up partial state to maintain atomicity
            try:
                if chunks_stored and not source_created:
                    # If chunks were stored but source failed, try to clean up
                    # This is a rare case, but we should handle it
                    pass
                elif source_created:
                    # If source was created but chunks failed, delete the source
                    # to avoid orphaned sources
                    source_id = result.get('source_id')
                    if source_id:
                        self.backend.delete_source(source_id)
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up partial state for {file_path}: {cleanup_error}")
            
            # Re-raise as KnowledgeIndexError if not already
            if not isinstance(e, (KnowledgeIndexError, KnowledgeValidationError)):
                result['error'] = str(e)
                raise KnowledgeIndexError(f"Failed to index {file_path}: {str(e)}") from e
            else:
                result['error'] = str(e)
                raise
        
        return result
    
    def _find_files(self, directory: Path, recursive: bool) -> List[Path]:
        """Find all supported files in a directory."""
        files = []
        
        if recursive:
            pattern = "**/*"
        else:
            pattern = "*"
        
        for file_path in directory.glob(pattern):
            if file_path.is_file() and self.file_loader.is_supported_file(file_path):
                files.append(file_path)
        
        return sorted(files)
    
    def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        try:
            # Use the embedding client to generate embeddings
            embeddings = []
            
            # Process in batches to avoid rate limits
            batch_size = 100
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                batch_embeddings = self.embedding_client.get_embeddings(batch, model=self.embedding_model)
                embeddings.extend(batch_embeddings)
            
            return embeddings
            
        except Exception as e:
            raise KnowledgeIndexError(f"Failed to generate embeddings: {e}")
    
    def remove_source(self, source_path: Path) -> bool:
        """
        Remove a source from the index.
        
        Args:
            source_path: Path to the source file
            
        Returns:
            True if source was removed, False if it wasn't found
        """
        try:
            source = self.file_loader.load_source(source_path)
            self.backend.delete_source(source.source_id)
            logger.info(f"Removed source from index: {source_path}")
            return True
        except FileNotFoundError:
            return False
        except Exception as e:
            raise KnowledgeIndexError(f"Failed to remove source {source_path}: {e}")
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get comprehensive indexing statistics."""
        backend_stats = self.backend.get_stats()
        
        return {
            'backend': backend_stats,
            'chunker': {
                'chunk_size': self.chunker.chunk_size,
                'chunk_overlap': self.chunker.chunk_overlap,
                'min_chunk_size': self.chunker.min_chunk_size,
            },
            'embedding': {
                'model': self.embedding_model,
                'dimension': self.backend.embedding_dimension,
            },
        }
    
    def reindex_changed_files(self, directory: Path, recursive: bool = True) -> Dict[str, Any]:
        """
        Reindex only files that have changed since last indexing.
        
        Args:
            directory: Directory to check for changes
            recursive: Whether to search subdirectories
            
        Returns:
            Dictionary with reindexing statistics including processed_files, skipped_files, errors
        """
        # Find all files
        files = self._find_files(directory, recursive)
        
        # Filter to only changed files
        changed_files = []
        unchanged_files = []
        existing_sources = set(self.backend.get_existing_sources())
        
        for file_path in files:
            try:
                source = self.file_loader.load_source(file_path)
                source_id = source.source_id
                
                if source_id not in existing_sources:
                    # New file
                    changed_files.append(file_path)
                else:
                    # Check if file has changed
                    existing_hash = self.backend.get_source_hash(source_id)
                    if existing_hash != source.sha256_hash:
                        changed_files.append(file_path)
                    else:
                        unchanged_files.append(file_path)
                        
            except Exception as e:
                logger.warning(f"Failed to check file {file_path}: {e}")
                # Include files that can't be checked as potentially changed
                changed_files.append(file_path)
        
        logger.info(f"Found {len(changed_files)} changed files to reindex, {len(unchanged_files)} unchanged")
        
        # Index only the changed files
        stats = self.index_files(changed_files, force_reindex=False)
        
        # Add unchanged files to skipped count
        stats['skipped_files'] += len(unchanged_files)
        stats['total_files'] = len(files)
        
        return stats
