#!/usr/bin/env python3
"""
Document Workflow Step 2: Summarize Text

Summarize extracted text content using AI Utilities.
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
    """Summarize text content."""
    
    print_header("📄 Document Workflow Step 2: Summarize Text")
    
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
        
        # Summarize using AI
        print("   Generating summary...")
        summary_prompt = f"""
        Please provide a comprehensive summary of document {uploaded_file.file_id}.
        Include:
        1. Main topics and themes
        2. Key points and findings
        3. Important conclusions
        4. Overall purpose and audience
        
        Format the summary in a clear, structured way with headings.
        """
        
        summary = client.ask(summary_prompt)
        
        # Save summary to output directory
        script_output_dir = output_dir(Path(__file__))
        summary_file = script_output_dir / "document_summary.txt"
        
        summary_file.write_text(summary, encoding='utf-8')
        print(f"✅ Summary generated and saved to: {summary_file}")
        
        # Show summary info
        print(f"\n📊 Summary Information:")
        print(f"   Document: {document_file.name}")
        print(f"   File ID: {uploaded_file.file_id}")
        print(f"   Summary length: {len(summary)} characters")
        print(f"   Lines: {len(summary.splitlines())}")
        print(f"   Words: {len(summary.split())}")
        
        # Show preview of summary
        preview_lines = summary.splitlines()[:8]
        print(f"\n📝 Summary Preview:")
        for i, line in enumerate(preview_lines, 1):
            print(f"   {i}: {line[:80]}{'...' if len(line) > 80 else ''}")
        
    except Exception as e:
        print(f"❌ Summary generation failed: {e}")
        return 1
    
    print(f"\n🎉 Document summarization complete!")
    
    # Show output directory
    script_output_dir = output_dir(Path(__file__))
    print(f"\n📁 All outputs saved to: {script_output_dir}")
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    if exit_code != 0:
        print("\n💡 Need help? Check the documentation or run with proper configuration")
    exit(exit_code)
