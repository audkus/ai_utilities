#!/usr/bin/env python3
"""
Document Workflow Step 1: Extract Text

Extract text content from PDF documents using AI Utilities.
"""

from pathlib import Path

from ai_utilities import AiClient, AiSettings
from _common import check_env_vars, get_outputs_dir


def main():
    """Extract text from PDF documents."""
    print("📄 Document Workflow Step 1: Extract Text")
    print("=" * 50)
    
    # Check for required environment variables
    missing_vars = check_env_vars(['OPENAI_API_KEY'])
    if missing_vars:
        print("❌ Cannot proceed without API key")
        return
    
    # Initialize the AI client
    print("\n🔧 Initializing AI client...")
    try:
        settings = AiSettings()
        client = AiClient(settings)
        print("✅ AI client initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        return
    
    # Extract text from PDF
    print("\n🎯 Example: Extract PDF Text")
    print("-" * 30)
    
    pdf_file = "sample_document.pdf"  # Replace with your PDF file
    print(f"📁 Extracting text from: {pdf_file}")
    
    try:
        # Extract text from PDF
        result = client.extract_text_from_pdf(pdf_file)
        
        print(f"   ✅ Text extraction complete!")
        print(f"   📊 Pages: {result.get('page_count', 'Unknown')}")
        print(f"   📝 Characters: {len(result.get('text', ''))}")
        print(f"   ⏱️  Time: {result.get('processing_time_seconds', 0):.2f}s")
        
        # Save extracted text
        outputs_dir = get_outputs_dir()
        output_file = outputs_dir / "extracted_text.txt"
        output_file.write_text(result.get('text', ''), encoding='utf-8')
        print(f"   📁 Text saved to: {output_file}")
        
        # Show preview
        text = result.get('text', '')
        preview = text[:200] + "..." if len(text) > 200 else text
        print(f"\n   📖 Text preview:")
        print(f"   {preview}")
        
    except Exception as e:
        print(f"   ❌ Extraction failed: {e}")
    
    print("\n🎉 Step 1 Complete!")
    print("\n💡 Next Steps:")
    print("   1. Run document_step_02_summarize.py to summarize the text")
    print("   2. Check outputs/ directory for extracted text")


if __name__ == "__main__":
    main()
