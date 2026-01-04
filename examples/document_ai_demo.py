#!/usr/bin/env python3
"""
Document AI Demo

This script demonstrates how to upload documents and use them in AI conversations.
Shows the complete workflow from document upload to AI analysis.
"""

import asyncio
from pathlib import Path

from ai_utilities import AiClient, AsyncAiClient
from ai_utilities.providers.provider_exceptions import FileTransferError, ProviderCapabilityError


def analyze_document_sync():
    """Synchronous document analysis example."""
    print("=== Synchronous Document Analysis ===")
    
    client = AiClient()
    
    # Step 1: Upload the document
    print("\n1. Uploading document...")
    try:
        # Upload a PDF, Word doc, or any text file
        uploaded_file = client.upload_file(
            "sample_report.pdf",  # Sample report included with examples
            purpose="assistants"
        )
        print(f"✅ Document uploaded: {uploaded_file.file_id}")
        print(f"   Filename: {uploaded_file.filename}")
        print(f"   Size: {uploaded_file.bytes} bytes")
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return
    
    # Step 2: Ask AI to analyze the document
    print("\n2. Analyzing document...")
    try:
        analysis = client.ask(
            f"Please analyze the document {uploaded_file.file_id} and provide:\n"
            "1. A comprehensive summary\n"
            "2. Key insights and findings\n"
            "3. Recommendations based on the content\n"
            "4. Any important data points or metrics"
        )
        print("✅ Analysis complete:")
        print("-" * 50)
        print(analysis)
        print("-" * 50)
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
    
    # Step 3: Ask follow-up questions
    print("\n3. Follow-up questions...")
    try:
        followup = client.ask(
            f"Based on document {uploaded_file.file_id}, "
            "what are the top 3 action items for management?"
        )
        print("✅ Follow-up response:")
        print(followup)
    except Exception as e:
        print(f"❌ Follow-up failed: {e}")


async def analyze_document_async():
    """Asynchronous document analysis example."""
    print("\n=== Asynchronous Document Analysis ===")
    
    client = AsyncAiClient()
    
    # Step 1: Upload document asynchronously
    print("\n1. Uploading document asynchronously...")
    try:
        uploaded_file = await client.upload_file(
            "research_paper.pdf",
            purpose="assistants"
        )
        print(f"✅ Document uploaded: {uploaded_file.file_id}")
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return
    
    # Step 2: Perform multiple analyses concurrently
    print("\n2. Running concurrent analyses...")
    try:
        # Create multiple analysis tasks
        tasks = [
            client.ask(f"Summarize document {uploaded_file.file_id} in 3 paragraphs"),
            client.ask(f"Extract key findings from document {uploaded_file.file_id}"),
            client.ask(f"Identify methodology used in document {uploaded_file.file_id}"),
            client.ask(f"List limitations mentioned in document {uploaded_file.file_id}")
        ]
        
        # Run all analyses concurrently
        results = await asyncio.gather(*tasks)
        
        print("✅ Concurrent analyses complete:")
        topics = ["Summary", "Key Findings", "Methodology", "Limitations"]
        for i, (topic, result) in enumerate(zip(topics, results)):
            print(f"\n{i+1}. {topic}:")
            print(result[:200] + "..." if len(result) > 200 else result)
    
    except Exception as e:
        print(f"❌ Concurrent analysis failed: {e}")


def batch_document_processing():
    """Process multiple documents in batch."""
    print("\n=== Batch Document Processing ===")
    
    client = AiClient()
    
    # List of documents to process
    documents = [
        "q1_financials.pdf",
        "q2_financials.pdf", 
        "q3_financials.pdf",
        "annual_report.pdf"
    ]
    
    # Step 1: Upload all documents
    print("\n1. Uploading all documents...")
    uploaded_files = []
    
    for doc_path in documents:
        try:
            if Path(doc_path).exists():
                uploaded_file = client.upload_file(doc_path, purpose="assistants")
                uploaded_files.append(uploaded_file)
                print(f"✅ Uploaded: {uploaded_file.filename}")
            else:
                print(f"⚠️  File not found: {doc_path}")
        except Exception as e:
            print(f"❌ Failed to upload {doc_path}: {e}")
    
    if not uploaded_files:
        print("❌ No documents uploaded successfully")
        return
    
    # Step 2: Analyze each document
    print(f"\n2. Analyzing {len(uploaded_files)} documents...")
    analyses = []
    
    for i, uploaded_file in enumerate(uploaded_files):
        try:
            analysis = client.ask(
                f"Analyze document {uploaded_file.file_id} and extract:\n"
                "- Financial performance metrics\n"
                "- Key highlights\n"
                "- Risk factors\n"
                "- Strategic initiatives"
            )
            analyses.append({
                'filename': uploaded_file.filename,
                'file_id': uploaded_file.file_id,
                'analysis': analysis
            })
            print(f"✅ Analyzed: {uploaded_file.filename}")
        except Exception as e:
            print(f"❌ Analysis failed for {uploaded_file.filename}: {e}")
    
    # Step 3: Create summary report
    print("\n3. Creating summary report...")
    try:
        # Combine all analyses for a comprehensive report
        combined_context = "\n\n".join([
            f"Document: {item['filename']}\n{item['analysis']}"
            for item in analyses
        ])
        
        summary = client.ask(
            f"Based on the following analyses of multiple financial documents:\n\n"
            f"{combined_context}\n\n"
            "Please provide:\n"
            "1. Overall performance trend across all periods\n"
            "2. Consolidated key metrics\n"
            "3. Cross-document insights\n"
            "4. Executive summary recommendations"
        )
        
        print("✅ Summary report complete:")
        print("=" * 60)
        print(summary)
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Summary creation failed: {e}")


def document_qa_session():
    """Interactive Q&A session with uploaded document."""
    print("\n=== Interactive Document Q&A ===")
    
    client = AiClient()
    
    # Upload document
    print("\n1. Uploading reference document...")
    try:
        uploaded_file = client.upload_file(
            "technical_manual.pdf",
            purpose="assistants"
        )
        print(f"✅ Reference document ready: {uploaded_file.file_id}")
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return
    
    # Interactive Q&A loop
    print("\n2. Starting Q&A session (type 'quit' to exit)")
    print("Ask questions about the uploaded document...")
    
    while True:
        try:
            question = input("\nYour question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("👋 Ending Q&A session")
                break
            
            if not question:
                continue
            
            print("🤔 Thinking...")
            answer = client.ask(
                f"Based on document {uploaded_file.file_id}, please answer: {question}"
            )
            
            print(f"\n📝 Answer: {answer}")
            
        except KeyboardInterrupt:
            print("\n👋 Q&A session interrupted")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


def compare_documents():
    """Compare and analyze multiple documents."""
    print("\n=== Document Comparison Analysis ===")
    
    client = AiClient()
    
    # Upload documents for comparison
    documents_to_compare = [
        ("proposal_v1.pdf", "Initial Proposal"),
        ("proposal_v2.pdf", "Revised Proposal"),
        ("proposal_final.pdf", "Final Proposal")
    ]
    
    print("\n1. Uploading documents for comparison...")
    uploaded_docs = []
    
    for file_path, description in documents_to_compare:
        try:
            if Path(file_path).exists():
                uploaded_file = client.upload_file(file_path, purpose="assistants")
                uploaded_docs.append((uploaded_file, description))
                print(f"✅ Uploaded: {description}")
            else:
                print(f"⚠️  File not found: {file_path}")
        except Exception as e:
            print(f"❌ Failed to upload {description}: {e}")
    
    if len(uploaded_docs) < 2:
        print("❌ Need at least 2 documents for comparison")
        return
    
    # Step 2: Perform comparison analysis
    print("\n2. Analyzing differences and similarities...")
    try:
        # Create context for comparison
        file_references = "\n".join([
            f"- {desc}: {file.file_id}" 
            for file, desc in uploaded_docs
        ])
        
        comparison = client.ask(
            f"Compare the following documents:\n{file_references}\n\n"
            "Please provide:\n"
            "1. Key differences between versions\n"
            "2. Major changes and improvements\n"
            "3. Content that was removed\n"
            "4. New sections or additions\n"
            "5. Overall evolution of the document"
        )
        
        print("✅ Comparison analysis complete:")
        print("=" * 60)
        print(comparison)
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Comparison failed: {e}")


def create_document_templates():
    """Create templates for common document analysis tasks."""
    print("\n=== Document Analysis Templates ===")
    
    client = AiClient()
    
    # Template functions
    templates = {
        "financial_analysis": lambda file_id: (
            f"Analyze financial document {file_id} and provide:\n"
            "1. Revenue and profit metrics\n"
            "2. Expense breakdown\n"
            "3. Cash flow analysis\n"
            "4. Key financial ratios\n"
            "5. Investment recommendations"
        ),
        
        "legal_review": lambda file_id: (
            f"Review legal document {file_id} and identify:\n"
            "1. Key obligations and responsibilities\n"
            "2. Risk factors and liabilities\n"
            "3. Important dates and deadlines\n"
            "4. Compliance requirements\n"
            "5. Recommended actions"
        ),
        
        "technical_documentation": lambda file_id: (
            f"Analyze technical document {file_id} and extract:\n"
            "1. System architecture overview\n"
            "2. Key components and dependencies\n"
            "3. Implementation requirements\n"
            "4. Potential technical challenges\n"
            "5. Recommended next steps"
        ),
        
        "market_research": lambda file_id: (
            f"Analyze market research document {file_id} and provide:\n"
            "1. Market size and growth trends\n"
            "2. Competitive landscape\n"
            "3. Target audience insights\n"
            "4. Key opportunities and threats\n"
            "5. Strategic recommendations"
        )
    }
    
    print("Available analysis templates:")
    for i, template_name in enumerate(templates.keys(), 1):
        print(f"{i}. {template_name}")
    
    # Example usage
    print("\nExample usage:")
    try:
        # Upload a document
        uploaded_file = client.upload_file("sample_report.pdf", purpose="assistants")
        print(f"✅ Document uploaded: {uploaded_file.file_id}")
        
        # Use financial analysis template
        print("\nUsing financial analysis template...")
        analysis = client.ask(templates["financial_analysis"](uploaded_file.file_id))
        print("✅ Analysis complete:")
        print(analysis[:300] + "..." if len(analysis) > 300 else analysis)
        
    except Exception as e:
        print(f"❌ Template example failed: {e}")


def main():
    """Run all document AI examples."""
    print("🚀 Document AI Demo")
    print("=" * 60)
    print("This demo shows how to upload documents and use them in AI conversations.")
    print("Make sure you have sample documents like 'sample_report.pdf' in the examples directory.")
    print()
    
    try:
        # Run examples
        print("Choose an example to run:")
        print("1. Synchronous document analysis")
        print("2. Asynchronous document analysis") 
        print("3. Batch document processing")
        print("4. Interactive document Q&A")
        print("5. Document comparison")
        print("6. Analysis templates")
        print("7. Run all examples")
        
        choice = input("\nEnter choice (1-7): ").strip()
        
        if choice == "1":
            analyze_document_sync()
        elif choice == "2":
            asyncio.run(analyze_document_async())
        elif choice == "3":
            batch_document_processing()
        elif choice == "4":
            document_qa_session()
        elif choice == "5":
            compare_documents()
        elif choice == "6":
            create_document_templates()
        elif choice == "7":
            analyze_document_sync()
            asyncio.run(analyze_document_async())
            batch_document_processing()
            compare_documents()
            create_document_templates()
        else:
            print("Invalid choice")
    
    except KeyboardInterrupt:
        print("\n\n⚠️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
