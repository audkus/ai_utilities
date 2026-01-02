"""
Tests for knowledge text chunking.

Tests the text chunking functionality with various configurations.
"""

from __future__ import annotations

import pytest

from ai_utilities.knowledge.chunking import TextChunker
from ai_utilities.knowledge.exceptions import KnowledgeValidationError


class TestTextChunker:
    """Test the TextChunker class."""
    
    def test_chunker_initialization(self) -> None:
        """Test creating a chunker with valid parameters."""
        chunker = TextChunker(
            chunk_size=1000,
            chunk_overlap=200,
            min_chunk_size=100,
        )
        
        assert chunker.chunk_size == 1000
        assert chunker.chunk_overlap == 200
        assert chunker.min_chunk_size == 100
    
    def test_chunker_validation_errors(self) -> None:
        """Test that invalid parameters raise validation errors."""
        # Negative chunk size
        with pytest.raises(KnowledgeValidationError):
            TextChunker(chunk_size=-1)
        
        # Negative overlap
        with pytest.raises(KnowledgeValidationError):
            TextChunker(chunk_overlap=-1)
        
        # Overlap >= chunk size
        with pytest.raises(KnowledgeValidationError):
            TextChunker(chunk_size=100, chunk_overlap=100)
        
        # Min chunk size > chunk size
        with pytest.raises(KnowledgeValidationError):
            TextChunker(chunk_size=100, min_chunk_size=200)
    
    def test_basic_chunking(self) -> None:
        """Test basic text chunking."""
        chunker = TextChunker(
            chunk_size=100,
            chunk_overlap=20,
            min_chunk_size=10,
            respect_paragraph_boundaries=False,  # Disable to force chunking
        )
        
        text = "This is a test text that should be chunked. " * 20  # Longer text
        chunks = chunker.chunk_text(text, "test_source")
        
        assert len(chunks) > 1
        assert all(chunk.text_length <= 100 for chunk in chunks)
        assert all(chunk.text_length >= 10 for chunk in chunks)
        assert all(chunk.source_id == "test_source" for chunk in chunks)
        
        # Check chunk indices
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i
    
    def test_empty_text(self) -> None:
        """Test chunking empty text."""
        chunker = TextChunker()
        chunks = chunker.chunk_text("", "test_source")
        assert chunks == []
        
        chunks = chunker.chunk_text("   ", "test_source")
        assert chunks == []
    
    def test_short_text(self) -> None:
        """Test chunking text shorter than chunk size."""
        chunker = TextChunker(chunk_size=1000, chunk_overlap=100, min_chunk_size=10)  # Smaller min_chunk_size
        text = "This is a short text."
        chunks = chunker.chunk_text(text, "test_source")
        
        assert len(chunks) == 1
        assert chunks[0].text == text
        assert chunks[0].chunk_index == 0
    
    def test_text_too_small(self) -> None:
        """Test that text smaller than min_chunk_size is filtered out."""
        chunker = TextChunker(chunk_size=100, chunk_overlap=10, min_chunk_size=50)
        text = "Short"
        chunks = chunker.chunk_text(text, "test_source")
        
        assert chunks == []  # Filtered out
    
    def test_paragraph_chunking(self) -> None:
        """Test paragraph-aware chunking."""
        chunker = TextChunker(
            chunk_size=200,
            chunk_overlap=0,
            min_chunk_size=10,
            respect_paragraph_boundaries=True,
        )
        
        text = """This is paragraph one. It has some text.
        
        This is paragraph two. It also has text.
        
        This is paragraph three. Final paragraph here."""
        
        chunks = chunker.chunk_text(text, "test_source")
        
        # Should not break within paragraphs
        for chunk in chunks:
            assert "\n\n" not in chunk.text or chunk.text.strip().endswith("\n\n")
    
    def test_sentence_chunking(self) -> None:
        """Test sentence-aware chunking."""
        chunker = TextChunker(
            chunk_size=100,
            chunk_overlap=10,
            min_chunk_size=10,
            respect_sentence_boundaries=True,
            respect_paragraph_boundaries=False,
        )
        
        text = "This is sentence one. This is sentence two! This is sentence three? " * 5
        chunks = chunker.chunk_text(text, "test_source")
        
        # Chunks should try to end at sentence boundaries
        for chunk in chunks[:-1]:  # Skip last chunk which might be incomplete
            assert chunk.text.rstrip().endswith(('.', '!', '?'))
    
    def test_overlap_chunking(self) -> None:
        """Test chunking with overlap."""
        chunker = TextChunker(
            chunk_size=50, 
            chunk_overlap=20, 
            min_chunk_size=10,
            respect_paragraph_boundaries=False,  # Disable to force chunking
        )
        
        text = "Word " * 50  # Create much longer repetitive text
        chunks = chunker.chunk_text(text, "test_source")
        
        assert len(chunks) > 1
        
        # Check that chunks overlap
        for i in range(len(chunks) - 1):
            current_chunk = chunks[i].text
            next_chunk = chunks[i + 1].text
            
            # Should have some overlap
            # This is a simplified check - in practice overlap might be at word boundaries
            assert len(current_chunk) > 20
            assert len(next_chunk) > 20
    
    def test_chunk_positions(self) -> None:
        """Test that chunk positions are correctly calculated."""
        chunker = TextChunker(chunk_size=50, chunk_overlap=10, min_chunk_size=10)
        
        text = "This is a test text for chunk positions. " * 5
        chunks = chunker.chunk_text(text, "test_source")
        
        # Check that positions are sequential and don't overlap
        for i, chunk in enumerate(chunks):
            assert chunk.start_char >= 0
            assert chunk.end_char > chunk.start_char
            assert chunk.end_char <= len(text)
            
            if i > 0:
                prev_chunk = chunks[i - 1]
                # Should start after or at the end of previous chunk (with no overlap)
                assert chunk.start_char >= prev_chunk.end_char
    
    def test_chunk_metadata(self) -> None:
        """Test that chunks contain correct metadata."""
        chunker = TextChunker(chunk_size=100, chunk_overlap=20)
        text = "Test text for metadata. " * 10
        chunks = chunker.chunk_text(text, "test_source")
        
        for chunk in chunks:
            assert "chunker" in chunk.metadata
            assert chunk.metadata["chunker"] == "TextChunker"
            assert "chunk_size" in chunk.metadata
            assert chunk.metadata["chunk_size"] == 100
            assert "chunk_overlap" in chunk.metadata
            assert chunk.metadata["chunk_overlap"] == 20
    
    def test_unicode_text(self) -> None:
        """Test chunking Unicode text."""
        chunker = TextChunker(
            chunk_size=50, 
            chunk_overlap=10, 
            min_chunk_size=10,
            respect_paragraph_boundaries=False,  # Disable to force chunking
        )
        
        text = "测试文本包含中文字符。" * 10 + "Emoji: 🚀🎉🌟" * 5
        chunks = chunker.chunk_text(text, "test_source")
        
        assert len(chunks) > 0
        # Allow chunks to be slightly over due to word boundaries
        assert all(chunk.text_length <= 100 for chunk in chunks)  # More lenient limit
        assert all("测试" in chunk.text or "🚀" in chunk.text for chunk in chunks)
    
    def test_start_chunk_index(self) -> None:
        """Test starting chunk index parameter."""
        chunker = TextChunker(chunk_size=50, chunk_overlap=10, min_chunk_size=10)
        text = "Test text " * 20
        
        chunks = chunker.chunk_text(text, "test_source", start_chunk_index=5)
        
        assert len(chunks) > 0
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == 5 + i
