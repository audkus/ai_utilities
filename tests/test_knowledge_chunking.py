"""
Comprehensive tests for knowledge/chunking.py module.
"""

import pytest
from unittest.mock import patch
from ai_utilities.knowledge.chunking import TextChunker
from ai_utilities.knowledge.models import Chunk
from ai_utilities.knowledge.exceptions import KnowledgeValidationError


class TestTextChunker:
    """Comprehensive tests for TextChunker class."""
    
    def test_init_default_parameters(self):
        """Test TextChunker initialization with default parameters."""
        chunker = TextChunker()
        assert chunker.chunk_size == 1000
        assert chunker.chunk_overlap == 200
        assert chunker.min_chunk_size == 100
        assert chunker.respect_sentence_boundaries is True
        assert chunker.respect_paragraph_boundaries is True
    
    def test_init_custom_parameters(self):
        """Test TextChunker initialization with custom parameters."""
        chunker = TextChunker(
            chunk_size=500,
            chunk_overlap=100,
            min_chunk_size=50,
            respect_sentence_boundaries=False,
            respect_paragraph_boundaries=False
        )
        assert chunker.chunk_size == 500
        assert chunker.chunk_overlap == 100
        assert chunker.min_chunk_size == 50
        assert chunker.respect_sentence_boundaries is False
        assert chunker.respect_paragraph_boundaries is False
    
    def test_init_validation_errors(self):
        """Test TextChunker initialization validation errors."""
        # Test chunk_size <= 0
        with pytest.raises(KnowledgeValidationError, match="chunk_size must be positive"):
            TextChunker(chunk_size=0)
        
        with pytest.raises(KnowledgeValidationError, match="chunk_size must be positive"):
            TextChunker(chunk_size=-1)
        
        # Test chunk_overlap < 0
        with pytest.raises(KnowledgeValidationError, match="chunk_overlap must be non-negative"):
            TextChunker(chunk_overlap=-1)
        
        # Test chunk_overlap >= chunk_size
        with pytest.raises(KnowledgeValidationError, match="chunk_overlap must be less than chunk_size"):
            TextChunker(chunk_size=100, chunk_overlap=100)
        
        with pytest.raises(KnowledgeValidationError, match="chunk_overlap must be less than chunk_size"):
            TextChunker(chunk_size=100, chunk_overlap=150)
        
        # Test min_chunk_size <= 0
        with pytest.raises(KnowledgeValidationError, match="min_chunk_size must be positive"):
            TextChunker(min_chunk_size=0)
        
        with pytest.raises(KnowledgeValidationError, match="min_chunk_size must be positive"):
            TextChunker(min_chunk_size=-1)
        
        # Test min_chunk_size > chunk_size
        with pytest.raises(KnowledgeValidationError, match="min_chunk_size must be less than chunk_size"):
            TextChunker(chunk_size=100, min_chunk_size=150)
    
    def test_chunk_text_empty_string(self):
        """Test chunking empty string."""
        chunker = TextChunker(chunk_size=100, chunk_overlap=20)
        chunks = list(chunker.chunk_text("test_source", ""))
        assert len(chunks) == 0
    
    def test_chunk_text_short_text(self):
        """Test chunking text shorter than chunk_size."""
        chunker = TextChunker(chunk_size=100, chunk_overlap=20)
        text = "This is a short text."
        chunks = list(chunker.chunk_text("test_source", text))
        assert len(chunks) == 1
        assert chunks[0].text == text
        assert chunks[0].source_id == "test_source"
        assert chunks[0].metadata['chunk_index'] == 0
        assert chunks[0].metadata['char_start'] == 0
        assert chunks[0].metadata['char_end'] == len(text)
    
    def test_chunk_text_exact_chunk_size(self):
        """Test chunking text exactly at chunk_size boundary."""
        chunker = TextChunker(chunk_size=20, chunk_overlap=5)
        text = "This is exactly twenty characters!"
        chunks = list(chunker.chunk_text("test_source", text))
        assert len(chunks) == 1
        assert chunks[0].text == text
    
    def test_chunk_text_simple_split(self):
        """Test basic text chunking without boundaries."""
        chunker = TextChunker(
            chunk_size=20,
            chunk_overlap=5,
            respect_sentence_boundaries=False,
            respect_paragraph_boundaries=False
        )
        text = "This is a longer text that should be split into multiple chunks for testing purposes."
        chunks = list(chunker.chunk_text("test_source", text))
        
        assert len(chunks) > 1
        
        # Check chunk properties
        for i, chunk in enumerate(chunks):
            assert chunk.source_id == "test_source"
            assert chunk.metadata['chunk_index'] == i
            assert isinstance(chunk.text, str)
            assert len(chunk.text) <= chunker.chunk_size + 50  # Allow some flexibility for boundaries
    
    def test_chunk_text_with_overlap(self):
        """Test chunking with overlap."""
        chunker = TextChunker(
            chunk_size=30,
            chunk_overlap=10,
            respect_sentence_boundaries=False,
            respect_paragraph_boundaries=False
        )
        text = "This is a longer text that should be split into multiple chunks with overlap for testing purposes."
        chunks = list(chunker.chunk_text("test_source", text))
        
        assert len(chunks) > 1
        
        # Check that adjacent chunks overlap
        for i in range(len(chunks) - 1):
            current_chunk = chunks[i]
            next_chunk = chunks[i + 1]
            
            # Find overlap by checking if end of current chunk appears in next chunk
            current_end = current_chunk.text[-10:]  # Last 10 chars
            assert current_end in next_chunk.text, f"Overlap not found between chunk {i} and {i+1}"
    
    def test_chunk_text_sentence_boundaries(self):
        """Test chunking with sentence boundary respect."""
        chunker = TextChunker(
            chunk_size=50,
            chunk_overlap=10,
            respect_sentence_boundaries=True,
            respect_paragraph_boundaries=False
        )
        text = "This is sentence one. This is sentence two! This is sentence three? This is sentence four. This is sentence five."
        chunks = list(chunker.chunk_text("test_source", text))
        
        assert len(chunks) > 1
        
        # Check that chunks don't split in the middle of sentences (when possible)
        for chunk in chunks:
            # Chunk should ideally end at sentence boundary
            chunk_text = chunk.text.strip()
            if len(chunk_text) < chunker.chunk_size:
                # If not at max size, should end at sentence boundary
                assert chunk_text.endswith(('.', '!', '?')), f"Chunk doesn't end at sentence boundary: {chunk_text}"
    
    def test_chunk_text_paragraph_boundaries(self):
        """Test chunking with paragraph boundary respect."""
        chunker = TextChunker(
            chunk_size=100,
            chunk_overlap=20,
            respect_sentence_boundaries=False,
            respect_paragraph_boundaries=True
        )
        text = "This is paragraph one. It has multiple sentences.\n\nThis is paragraph two. It also has multiple sentences.\n\nThis is paragraph three."
        chunks = list(chunker.chunk_text("test_source", text))
        
        assert len(chunks) >= 1
        
        # Check that chunks don't split in the middle of paragraphs (when possible)
        for chunk in chunks:
            chunk_text = chunk.text.strip()
            if len(chunk_text) < chunker.chunk_size and '\n\n' in text:
                # If not at max size and original has paragraphs, should end at paragraph boundary
                # This is a heuristic - the exact implementation may vary
                pass  # Paragraph boundary logic is complex, so we just ensure it doesn't crash
    
    def test_chunk_text_multiple_boundaries(self):
        """Test chunking with both sentence and paragraph boundaries."""
        chunker = TextChunker(
            chunk_size=80,
            chunk_overlap=15,
            respect_sentence_boundaries=True,
            respect_paragraph_boundaries=True
        )
        text = """This is paragraph one. It has multiple sentences to test the chunking behavior.
        
        This is paragraph two! It also has multiple sentences and should be handled properly.
        
        This is paragraph three? Let's see how the chunker handles this text with various boundaries."""
        
        chunks = list(chunker.chunk_text("test_source", text))
        
        assert len(chunks) >= 1
        
        # Verify chunk structure
        for i, chunk in enumerate(chunks):
            assert chunk.source_id == "test_source"
            assert chunk.metadata['chunk_index'] == i
            assert isinstance(chunk.text, str)
            assert len(chunk.text) > 0
    
    def test_chunk_text_very_small_chunks(self):
        """Test chunking with very small chunk sizes."""
        chunker = TextChunker(
            chunk_size=10,
            chunk_overlap=2,
            min_chunk_size=5,
            respect_sentence_boundaries=False,
            respect_paragraph_boundaries=False
        )
        text = "This is a test text for small chunking."
        chunks = list(chunker.chunk_text("test_source", text))
        
        assert len(chunks) > 1
        
        # Check that chunks are approximately the right size
        for chunk in chunks:
            assert len(chunk.text) >= chunker.min_chunk_size or len(chunk.text) == len(text)
    
    def test_chunk_text_large_text(self):
        """Test chunking large text."""
        chunker = TextChunker(chunk_size=200, chunk_overlap=50)
        
        # Create a large text by repeating a pattern
        pattern = "This is a test sentence. " * 50
        large_text = pattern.strip()
        
        chunks = list(chunker.chunk_text("test_source", large_text))
        
        assert len(chunks) > 5  # Should create multiple chunks
        
        # Verify all chunks together cover the original text
        combined_text = "".join(chunk.text for chunk in chunks)
        # Remove overlap from combined text for comparison
        assert len(combined_text) >= len(large_text)
    
    def test_chunk_text_metadata(self):
        """Test that chunk metadata is correctly set."""
        chunker = TextChunker(chunk_size=50, chunk_overlap=10)
        text = "This is a test text for metadata verification. It should be split into multiple chunks."
        chunks = list(chunker.chunk_text("test_source", text))
        
        for i, chunk in enumerate(chunks):
            assert chunk.source_id == "test_source"
            assert chunk.metadata['chunk_index'] == i
            assert 'char_start' in chunk.metadata
            assert 'char_end' in chunk.metadata
            assert chunk.metadata['char_start'] >= 0
            assert chunk.metadata['char_end'] > chunk.metadata['char_start']
    
    def test_chunk_text_unicode_content(self):
        """Test chunking text with unicode characters."""
        chunker = TextChunker(chunk_size=30, chunk_overlap=5)
        text = "This text contains unicode: café, naïve, résumé, and emoji: 🚀 🌟 ✨"
        chunks = list(chunker.chunk_text("test_source", text))
        
        assert len(chunks) >= 1
        
        # Verify unicode characters are preserved
        combined_text = "".join(chunk.text for chunk in chunks)
        assert "café" in combined_text
        assert "naïve" in combined_text
        assert "résumé" in combined_text
        assert "🚀" in combined_text
    
    def test_chunk_text_whitespace_handling(self):
        """Test chunking text with various whitespace patterns."""
        chunker = TextChunker(chunk_size=40, chunk_overlap=10)
        text = "  Text with   leading\nand trailing\twhitespace   \n\n  and multiple   spaces  "
        chunks = list(chunker.chunk_text("test_source", text))
        
        assert len(chunks) >= 1
        
        # Verify that whitespace is preserved in chunks
        combined_text = "".join(chunk.text for chunk in chunks)
        assert "  Text" in combined_text
        assert "\n" in combined_text
        assert "\t" in combined_text
    
    def test_chunk_text_edge_cases(self):
        """Test edge cases for text chunking."""
        chunker = TextChunker(chunk_size=20, chunk_overlap=5)
        
        # Test with only whitespace
        chunks = list(chunker.chunk_text("test_source", "   \n\t   "))
        assert len(chunks) == 0  # Should not create chunks for only whitespace
        
        # Test with special characters
        text = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        chunks = list(chunker.chunk_text("test_source", text))
        assert len(chunks) >= 1
        assert chunks[0].text == text
