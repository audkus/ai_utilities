#!/usr/bin/env python3
"""
Document Workflow Step 2: Summarize Text

Summarize extracted text content using AI Utilities.
"""

from pathlib import Path

from ai_utilities import AiClient, AiSettings
from _common import check_env_vars, get_outputs_dir


def main():
    """Summarize text content."""
    print("📄 Document Workflow Step 2: Summarize Text")
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
    
    # Read extracted text
    print("\n🎯 Example: Summarize Text")
    print("-" * 30)
    
    outputs_dir = get_outputs_dir()
    text_file = outputs_dir / "extracted_text.txt"
    
    if not text_file.exists():
        print(f"   ❌ Text file not found: {text_file}")
        print(f"   💡 Run document_step_01_extract.py first")
        return
    
    try:
        # Read the extracted text
        text = text_file.read_text(encoding='utf-8')
        print(f"   📖 Read {len(text)} characters from {text_file}")
        
        # Summarize the text
        print("   🔄 Generating summary...")
        summary = client.summarize_text(
            text,
            max_length=150,  # Maximum summary length
            focus="key_points"  # Focus on key points
        )
        
        print(f"   ✅ Summary generated!")
        print(f"   📝 Summary length: {len(summary)} characters")
        
        # Save summary
        summary_file = outputs_dir / "text_summary.txt"
        summary_file.write_text(summary, encoding='utf-8')
        print(f"   📁 Summary saved to: {summary_file}")
        
        # Show summary
        print(f"\n   📖 Summary:")
        print(f"   {summary}")
        
    except Exception as e:
        print(f"   ❌ Summarization failed: {e}")
    
    print("\n🎉 Step 2 Complete!")
    print("\n💡 Next Steps:")
    print("   1. Run document_step_03_transform.py to transform the text")
    print("   2. Check outputs/ directory for summary")


if __name__ == "__main__":
    main()
