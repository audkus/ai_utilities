#!/usr/bin/env python3
"""
Document Workflow Step 1: Extract Text

Extract text content from PDF documents using AI Utilities.
"""

from pathlib import Path
import sys

# === BOOTSTRAP: Ensure ai_utilities is importable from any location ===
script_path = Path(__file__).resolve()
repo_root = script_path.parent.parent.parent

# Add src directory to sys.path if not already there
src_dir = repo_root / "src"
src_dir_str = str(src_dir)
if src_dir_str not in sys.path:
    sys.path.insert(0, src_dir_str)

# Add repo root to sys.path for examples import
repo_root_str = str(repo_root)
if repo_root_str not in sys.path:
    sys.path.insert(0, repo_root_str)

from examples._common import print_header, output_dir, require_env, assets_dir
# === END BOOTSTRAP ===

from ai_utilities import AiClient, AiSettings


def main():
    """Extract text from PDF documents."""
    
    print_header("📄 Document Workflow Step 1: Extract Text")
    
    # Check for required environment variables
    if not require_env(['OPENAI_API_KEY']):
        print("❌ CONFIGURATION REQUIRED - Cannot proceed without API key")
        return 1
    
    # Initialize AI client
    print("\n🔧 Initializing AI client...")
    try:
        client = AiClient()
        print("✅ AI client initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        return 1
    
    # Use asset from examples/assets directory
    document_file = assets_dir() / "sample_document.pdf"
    print(f"\n📄 Processing document: {document_file}")
    
    # Check if document file exists
    if not document_file.exists():
        print(f"❌ Document file not found: {document_file}")
        print("💡 Make sure sample_document.pdf exists in examples/assets/")
        return 1
    
    try:
        # Upload the document
        print("   Uploading document...")
        uploaded_file = client.upload_file(str(document_file), purpose="assistants")
        print(f"✅ Document uploaded: {uploaded_file.file_id}")
        
        # Extract text using AI
        print("   Extracting text content...")
        extraction_prompt = f"""
        Please extract all text content from document {uploaded_file.file_id}.
        Return the extracted text in a clean, readable format.
        Preserve the structure and formatting as much as possible.
        """
        
        extracted_text = client.ask(extraction_prompt)
        
        # Save extracted text to output directory
        script_output_dir = output_dir(Path(__file__))
        text_file = script_output_dir / "extracted_text.txt"
        
        text_file.write_text(extracted_text, encoding='utf-8')
        print(f"✅ Text extracted and saved to: {text_file}")
        
        # Show extraction info
        print(f"\n📊 Extraction Information:")
        print(f"   Document: {document_file.name}")
        print(f"   File ID: {uploaded_file.file_id}")
        print(f"   Text length: {len(extracted_text)} characters")
        print(f"   Lines: {len(extracted_text.splitlines())}")
        print(f"   Words: {len(extracted_text.split())}")
        
        # Show preview of extracted text
        preview_lines = extracted_text.splitlines()[:5]
        print(f"\n📝 Text Preview:")
        for i, line in enumerate(preview_lines, 1):
            print(f"   {i}: {line[:80]}{'...' if len(line) > 80 else ''}")
        
    except Exception as e:
        print(f"❌ Text extraction failed: {e}")
        return 1
    
    print(f"\n🎉 Text extraction complete!")
    
    # Show output directory
    script_output_dir = output_dir(Path(__file__))
    print(f"\n📁 All outputs saved to: {script_output_dir}")
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    if exit_code != 0:
        print("\n💡 Need help? Check the documentation or run with proper configuration")
    exit(exit_code)
