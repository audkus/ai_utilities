#!/usr/bin/env python3
"""
Knowledge Indexing and Search Example

This script demonstrates how to use the knowledge indexing and search functionality
in ai_utilities to create a local-first semantic search system.
"""

import os
import tempfile
from pathlib import Path

from ai_utilities import AiClient, AiSettings


def main():
    """Main example function."""
    print("🔍 AI Utilities Knowledge Indexing Example")
    print("=" * 50)
    
    # Create a temporary directory for our example
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        print(f"📁 Using temporary directory: {temp_path}")
        
        # Create sample documents
        create_sample_documents(temp_path)
        
        # Configure AI client with knowledge settings
        settings = AiSettings(
            api_key=os.getenv("OPENAI_API_KEY", "dummy-key-for-testing"),
            knowledge_enabled=True,
            knowledge_db_path=temp_path / "knowledge.db",
            knowledge_roots=str(temp_path / "docs"),
            embedding_model="text-embedding-3-small",
            knowledge_chunk_size=500,
            knowledge_chunk_overlap=100,
        )
        
        # Create AI client
        client = AiClient(settings=settings)
        
        try:
            # Index the documents
            print("\n📚 Indexing documents...")
            stats = client.index_knowledge()
            
            print(f"✅ Indexing completed:")
            print(f"   Files processed: {stats['processed_files']}")
            print(f"   Chunks created: {stats['total_chunks']}")
            print(f"   Embeddings generated: {stats['total_embeddings']}")
            print(f"   Processing time: {stats['processing_time']:.2f}s")
            
            if stats['errors']:
                print(f"⚠️  Errors: {len(stats['errors'])}")
                for error in stats['errors']:
                    print(f"   - {error}")
            
            # Perform semantic searches
            print("\n🔍 Performing semantic searches...")
            
            search_queries = [
                "machine learning algorithms",
                "Python programming best practices", 
                "data visualization techniques",
                "web development frameworks",
            ]
            
            for query in search_queries:
                print(f"\n📝 Query: '{query}'")
                results = client.search_knowledge(query, top_k=3, similarity_threshold=0.3)
                
                if results:
                    for i, result in enumerate(results, 1):
                        print(f"   {i}. [Score: {result['similarity_score']:.3f}] {result['source_path'].name}")
                        print(f"      {result['text'][:100]}...")
                else:
                    print("   No relevant results found.")
            
            # Ask a question with knowledge context
            print("\n🤖 Asking question with knowledge context...")
            question = "What are the key considerations for machine learning model deployment?"
            
            try:
                result = client.ask_with_knowledge(question, top_k=3, similarity_threshold=0.3)
                
                print(f"💬 Question: {question}")
                print(f"📚 Knowledge sources used: {result.knowledge_count}")
                if result.knowledge_sources:
                    for source in result.knowledge_sources:
                        print(f"   - {Path(source).name}")
                
                print(f"\n🤖 Answer:")
                if isinstance(result.response, str):
                    print(result.response)
                else:
                    print(str(result.response))
                    
            except Exception as e:
                print(f"❌ Error asking with knowledge: {e}")
            
            # Show knowledge statistics
            print("\n📊 Knowledge Base Statistics:")
            try:
                # Get backend stats through the search functionality
                knowledge_config = client._get_knowledge_config()
                from ai_utilities.knowledge.backend import SqliteVectorBackend
                
                backend = SqliteVectorBackend(
                    db_path=knowledge_config.knowledge_db_path,
                    embedding_dimension=1536,
                    use_extension=knowledge_config.use_sqlite_extension,
                )
                
                stats = backend.get_stats()
                print(f"   Sources indexed: {stats['sources_count']}")
                print(f"   Total chunks: {stats['chunks_count']}")
                print(f"   Embeddings stored: {stats['embeddings_count']}")
                print(f"   Database size: {stats['db_size_bytes']:,} bytes")
                print(f"   SQLite extension: {'✅' if stats['extension_available'] else '❌ (fallback mode)'}")
                
            except Exception as e:
                print(f"❌ Error getting stats: {e}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            print("\n💡 Note: This example requires an OpenAI API key for embeddings.")
            print("   Set OPENAI_API_KEY environment variable to use real embeddings.")
            print("   Without a valid API key, the example will demonstrate the structure only.")


def create_sample_documents(temp_path: Path) -> None:
    """Create sample documents for indexing."""
    docs_dir = temp_path / "docs"
    docs_dir.mkdir(exist_ok=True)
    
    # Document 1: Machine Learning
    ml_doc = docs_dir / "machine_learning.md"
    ml_doc.write_text("""# Machine Learning Fundamentals

Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed.

## Key Concepts

### Supervised Learning
Supervised learning algorithms learn from labeled training data to make predictions about new, unseen data. Common algorithms include:
- Linear regression
- Decision trees
- Random forests
- Neural networks

### Unsupervised Learning
Unsupervised learning finds hidden patterns in unlabeled data. Techniques include:
- Clustering
- Dimensionality reduction
- Anomaly detection

### Model Deployment Considerations
When deploying machine learning models, consider:
- Model performance and accuracy
- Computational resource requirements
- Latency and throughput requirements
- Monitoring and maintenance
- Data privacy and security
- Model versioning and rollback capabilities
""")
    
    # Document 2: Python Programming
    python_doc = docs_dir / "python_programming.md"
    python_doc.write_text("""# Python Programming Best Practices

Python is a versatile programming language widely used in data science, web development, and automation.

## Code Style

Follow PEP 8 guidelines for consistent code style:
- Use 4 spaces for indentation
- Limit lines to 79 characters
- Use descriptive variable names
- Write docstrings for functions and classes

## Performance Optimization

### Efficient Data Structures
- Use lists for ordered collections
- Use dictionaries for key-value lookups
- Use sets for unique elements with fast membership testing

### Memory Management
- Use generators for large datasets
- Avoid unnecessary object creation
- Profile memory usage with memory_profiler

## Data Science Applications

Python excels in data science with libraries like:
- NumPy for numerical computing
- Pandas for data manipulation
- Matplotlib and Seaborn for visualization
- Scikit-learn for machine learning
""")
    
    # Document 3: Data Visualization
    viz_doc = docs_dir / "data_visualization.md"
    viz_doc.write_text("""# Data Visualization Techniques

Effective data visualization helps communicate insights and patterns in data clearly.

## Choosing the Right Chart Type

### Comparison Charts
- Bar charts for comparing quantities
- Line charts for trends over time
- Scatter plots for relationships between variables

### Distribution Charts
- Histograms for frequency distributions
- Box plots for statistical summaries
- Violin plots for distribution shapes

### Composition Charts
- Pie charts for parts of a whole (limited categories)
- Stacked bar charts for composition over time
- Area charts for cumulative totals

## Visualization Best Practices

### Design Principles
- Keep it simple and clear
- Use color meaningfully
- Label axes and data points
- Provide context with titles and annotations

### Interactive Visualizations
Modern web-based visualization libraries enable:
- Zooming and panning
- Tooltips with detailed information
- Filtering and dynamic updates
- Responsive design for different devices

Popular tools include Plotly, Bokeh, and D3.js for creating interactive web-based visualizations.
""")
    
    # Document 4: Web Development
    web_doc = docs_dir / "web_development.md"
    web_doc.write_text("""# Modern Web Development Frameworks

Web development has evolved significantly with the emergence of powerful frameworks and tools.

## Frontend Frameworks

### React
- Component-based architecture
- Virtual DOM for performance
- Large ecosystem and community
- Developed and maintained by Facebook

### Vue.js
- Progressive framework
- Easy learning curve
- Excellent documentation
- Flexible and adaptable

### Angular
- Full-featured framework
- TypeScript support
- Enterprise-grade features
- Developed by Google

## Backend Technologies

### Python Frameworks
- Django: Batteries-included framework
- Flask: Lightweight and flexible
- FastAPI: Modern async framework with automatic documentation

### JavaScript Runtimes
- Node.js: Server-side JavaScript
- Deno: Secure runtime with TypeScript support
- Bun: Fast JavaScript runtime

## Development Best Practices

### Performance Optimization
- Code splitting and lazy loading
- Image optimization and compression
- Caching strategies
- Minification and bundling

### Security Considerations
- Input validation and sanitization
- HTTPS implementation
- Authentication and authorization
- Protection against common vulnerabilities (XSS, CSRF, SQL injection)
""")
    
    print(f"📝 Created {len(list(docs_dir.glob('*.md')))} sample documents:")
    for doc in docs_dir.glob('*.md'):
        print(f"   - {doc.name}")


if __name__ == "__main__":
    main()
