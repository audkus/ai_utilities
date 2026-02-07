#!/usr/bin/env python3
"""
Knowledge Indexing Recipe
Complete example of creating and searching a knowledge base with AI Utilities.
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_utilities import AiClient, safe_write_bytes
from ai_utilities.knowledge import KnowledgeIndexer, KnowledgeSource

def main():
    print("📚 Knowledge Indexing Recipe")
    print("=" * 50)
    
    # Create client
    client = AiClient()
    
    # Create knowledge base
    indexer = KnowledgeIndexer("my_knowledge")
    
    # Add some knowledge sources
    sources = [
        KnowledgeSource(
            name="Python Documentation",
            content="Python is a high-level programming language known for its simplicity and readability.",
            metadata={"category": "documentation", "language": "python"}
        ),
        KnowledgeSource(
            name="Machine Learning Basics",
            content="Machine learning is a subset of artificial intelligence that focuses on algorithms that can learn from data.",
            metadata={"category": "education", "topic": "ml"}
        ),
        KnowledgeSource(
            name="AI Ethics",
            content="AI ethics involves the moral principles and guidelines for developing responsible artificial intelligence systems.",
            metadata={"category": "ethics", "topic": "ai"}
        )
    ]
    
    print("📚 Adding knowledge sources...")
    for source in sources:
        indexer.add_source(source)
        print(f"  ✅ Added: {source.name}")
    
    # Build the index
    print("\n🔧 Building knowledge index...")
    indexer.build_index()
    
    # Search the knowledge base
    queries = [
        "What is Python?",
        "How does machine learning work?",
        "What are AI ethics?"
        "How do I use Python for data science?"
        "What is the best way to learn programming?"
    ]
    
    print("\n🔍 Searching knowledge base:")
    for query in queries:
        results = indexer.search(query, max_results=3)
        print(f"\n📝 Query: {query}")
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result.name} (score: {result.score:.2f})")
            print(f"     {result.text[:100]}...")
    
    print("\n✅ Knowledge indexing complete!")

if __name__ == "__main__":
    main()
