"""
Fake embedding provider for testing knowledge functionality.

This module provides a deterministic embedding provider that returns
predictable vectors for testing without requiring network access.
"""

from __future__ import annotations

import hashlib
from typing import List


class FakeEmbeddingProvider:
    """
    Fake embedding provider that returns deterministic vectors based on text hash.
    
    This allows for predictable testing without requiring actual API calls.
    """
    
    def __init__(self, embedding_dimension: int = 1536) -> None:
        """
        Initialize the fake embedding provider.
        
        Args:
            embedding_dimension: Dimension of embeddings to generate
        """
        self.embedding_dimension = embedding_dimension
    
    def get_embeddings(self, texts: List[str], model: str = "text-embedding-3-small") -> List[List[float]]:
        """
        Generate deterministic embeddings for the given texts.
        
        Args:
            texts: List of texts to embed
            model: Embedding model name (ignored for fake provider)
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        
        for text in texts:
            # Generate deterministic vector based on text hash
            text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
            
            # Convert hash to floating point vector
            embedding = []
            for i in range(0, len(text_hash), 8):
                # Take 8 characters of hash and convert to a float between -1 and 1
                chunk = text_hash[i:i+8]
                if len(chunk) < 8:
                    chunk = chunk.ljust(8, '0')
                
                # Convert hex chunk to integer, then to normalized float
                int_val = int(chunk, 16)
                float_val = (int_val / (2**64 - 1)) * 2 - 1  # Normalize to [-1, 1]
                embedding.append(float_val)
            
            # Pad or truncate to desired dimension
            while len(embedding) < self.embedding_dimension:
                # Add some deterministic variation
                embedding.append(embedding[0] * 0.1)
            
            if len(embedding) > self.embedding_dimension:
                embedding = embedding[:self.embedding_dimension]
            
            embeddings.append(embedding)
        
        return embeddings
    
    def __call__(self, texts: List[str], model: str = "text-embedding-3-small") -> List[List[float]]:
        """Make the provider callable like a real embedding client."""
        return self.get_embeddings(texts, model)
