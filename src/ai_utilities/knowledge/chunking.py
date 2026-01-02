"""
Text chunking functionality for knowledge indexing.

This module provides deterministic text chunking with configurable size and overlap,
designed to break down large documents into manageable pieces for embedding and search.
"""

from __future__ import annotations

import re
from typing import Iterator, List

from .models import Chunk
from .exceptions import KnowledgeValidationError


class TextChunker:
    """Deterministic text chunker with configurable size and overlap."""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        min_chunk_size: int = 100,
        respect_sentence_boundaries: bool = True,
        respect_paragraph_boundaries: bool = True,
    ) -> None:
        """
        Initialize the text chunker.
        
        Args:
            chunk_size: Target size of each chunk in characters
            chunk_overlap: Number of characters to overlap between chunks
            min_chunk_size: Minimum size of a chunk to be considered valid
            respect_sentence_boundaries: Try to break at sentence boundaries
            respect_paragraph_boundaries: Try to break at paragraph boundaries
        """
        if chunk_size <= 0:
            raise KnowledgeValidationError("chunk_size must be positive")
        if chunk_overlap < 0:
            raise KnowledgeValidationError("chunk_overlap must be non-negative")
        if chunk_overlap >= chunk_size:
            raise KnowledgeValidationError("chunk_overlap must be less than chunk_size")
        if min_chunk_size <= 0:
            raise KnowledgeValidationError("min_chunk_size must be positive")
        if min_chunk_size > chunk_size:
            raise KnowledgeValidationError("min_chunk_size must be less than chunk_size")
        
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        self.respect_sentence_boundaries = respect_sentence_boundaries
        self.respect_paragraph_boundaries = respect_paragraph_boundaries
    
    def chunk_text(
        self,
        text: str,
        source_id: str,
        start_chunk_index: int = 0,
    ) -> List[Chunk]:
        """
        Split text into chunks.
        
        Args:
            text: The text to chunk
            source_id: ID of the source this text belongs to
            start_chunk_index: Starting index for chunk numbering
            
        Returns:
            List of chunks
        """
        if not text.strip():
            return []
        
        # Normalize text
        normalized_text = self._normalize_text(text)
        
        if self.respect_paragraph_boundaries:
            chunks = list(self._chunk_by_paragraphs(normalized_text, source_id, start_chunk_index))
        else:
            chunks = list(self._chunk_by_size(normalized_text, source_id, start_chunk_index))
        
        # Filter out chunks that are too small
        filtered_chunks = [chunk for chunk in chunks if chunk.text_length >= self.min_chunk_size]
        
        return filtered_chunks
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for consistent chunking."""
        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Ensure proper spacing around punctuation
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        text = re.sub(r'([.!?])\s*\n', r'\1\n\n', text)  # Ensure double newlines after sentences
        text = re.sub(r'\n{3,}', '\n\n', text)  # Limit consecutive newlines
        
        return text.strip()
    
    def _chunk_by_paragraphs(
        self,
        text: str,
        source_id: str,
        start_chunk_index: int = 0,
    ) -> Iterator[Chunk]:
        """Chunk text respecting paragraph boundaries."""
        paragraphs = text.split('\n\n')
        
        current_chunk_text = ""
        current_chunk_start = 0
        chunk_index = start_chunk_index
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # If adding this paragraph would exceed chunk size, create a chunk
            if len(current_chunk_text) + len(paragraph) > self.chunk_size and current_chunk_text:
                yield self._create_chunk(
                    current_chunk_text,
                    source_id,
                    chunk_index,
                    current_chunk_start,
                    current_chunk_start + len(current_chunk_text),
                )
                chunk_index += 1
                
                # Start new chunk with overlap if configured
                if self.chunk_overlap > 0:
                    overlap_text = self._get_overlap_text(current_chunk_text)
                    current_chunk_text = overlap_text + "\n\n" + paragraph
                    current_chunk_start = current_chunk_start + len(current_chunk_text) - len(overlap_text)
                else:
                    current_chunk_text = paragraph
                    current_chunk_start = current_chunk_start + len(current_chunk_text)
            else:
                if current_chunk_text:
                    current_chunk_text += "\n\n" + paragraph
                else:
                    current_chunk_text = paragraph
                    current_chunk_start = 0
        
        # Don't forget the last chunk
        if current_chunk_text:
            yield self._create_chunk(
                current_chunk_text,
                source_id,
                chunk_index,
                current_chunk_start,
                current_chunk_start + len(current_chunk_text),
            )
    
    def _chunk_by_size(
        self,
        text: str,
        source_id: str,
        start_chunk_index: int = 0,
    ) -> Iterator[Chunk]:
        """Chunk text by size, optionally respecting sentence boundaries."""
        chunk_index = start_chunk_index
        position = 0
        
        while position < len(text):
            # Calculate end position for this chunk
            end_pos = min(position + self.chunk_size, len(text))
            
            if end_pos == len(text):
                # Last chunk - take everything remaining
                chunk_text = text[position:].strip()
                if chunk_text:
                    yield self._create_chunk(
                        chunk_text,
                        source_id,
                        chunk_index,
                        position,
                        len(text),
                    )
                break
            
            # Try to find a good break point
            if self.respect_sentence_boundaries:
                break_pos = self._find_sentence_break(text, position, end_pos)
            else:
                break_pos = end_pos
            
            chunk_text = text[position:break_pos].strip()
            if chunk_text:
                yield self._create_chunk(
                    chunk_text,
                    source_id,
                    chunk_index,
                    position,
                    break_pos,
                )
            
            chunk_index += 1
            
            # Calculate next position with overlap
            if self.chunk_overlap > 0:
                position = max(position + 1, break_pos - self.chunk_overlap)
            else:
                position = break_pos
    
    def _find_sentence_break(self, text: str, start: int, end: int) -> int:
        """Find the best sentence break position between start and end."""
        # Look for sentence endings in the last 25% of the chunk
        search_start = max(start, start + int(self.chunk_size * 0.75))
        search_text = text[search_start:end]
        
        # Find all sentence endings
        sentence_endings = []
        for match in re.finditer(r'[.!?]\s+', search_text):
            sentence_endings.append(search_start + match.end())
        
        if sentence_endings:
            # Return the last sentence ending before end
            return sentence_endings[-1]
        
        # No sentence boundaries found, return end position
        return end
    
    def _get_overlap_text(self, text: str) -> str:
        """Get overlap text from the end of a chunk."""
        if self.chunk_overlap >= len(text):
            return text
        
        # Try to break at a word boundary
        overlap_text = text[-self.chunk_overlap:]
        word_break = overlap_text.find(' ')
        
        return overlap_text if word_break == -1 else overlap_text[word_break:]
    
    def _create_chunk(
        self,
        text: str,
        source_id: str,
        chunk_index: int,
        start_char: int,
        end_char: int,
    ) -> Chunk:
        """Create a Chunk object with the given parameters."""
        # Create a stable chunk ID based on source path, index, and content hash
        from hashlib import sha256
        content_hash = sha256(text.encode('utf-8')).hexdigest()[:8]
        chunk_id = f"{source_id}:{chunk_index}:{content_hash}"
        
        return Chunk(
            chunk_id=chunk_id,
            source_id=source_id,
            text=text,
            chunk_index=chunk_index,
            start_char=start_char,
            end_char=end_char,
            metadata={
                "chunker": "TextChunker",
                "chunk_size": self.chunk_size,
                "chunk_overlap": self.chunk_overlap,
            },
        )
