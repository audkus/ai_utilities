#!/usr/bin/env python3
"""
Simple Document AI Example

Shows the basic workflow: Upload document → Ask AI questions about it
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

from ai_utilities import AiClient


def main():
    """Simple document analysis workflow."""
    
    print_header("📄 Document AI Quickstart")
    
    # Check for required environment variables
    if not require_env(['OPENAI_API_KEY']):
        print("❌ CONFIGURATION REQUIRED - Cannot proceed without API key")
        return 1
    
    # 1. Initialize AI client
    print("\n🔧 Initializing AI client...")
    try:
        client = AiClient()
        print("✅ AI client initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        return 1
    
    # 2. Upload your document
    print("\n📁 Uploading document...")
    
    # Use asset from examples/assets directory
    document_file = assets_dir() / "sample_document.pdf"
    print(f"📄 Uploading document: {document_file}")
    
    # Check if document file exists
    if not document_file.exists():
        print(f"❌ Document file not found: {document_file}")
        print("💡 Make sure sample_document.pdf exists in examples/assets/")
        return 1
    
    try:
        uploaded_file = client.upload_file(
            str(document_file),  # Sample document included with examples
            purpose="assistants"
        )
        print(f"✅ Document uploaded: {uploaded_file.file_id}")
        
        # 3. Ask AI to analyze the document
        print("\n🤖 Analyzing document...")
        summary = client.ask(
            f"Please summarize the document {uploaded_file.file_id} "
            "and extract the key points."
        )
        print("📝 Summary:")
        print(summary)
        
        # 4. Ask follow-up questions
        print("\n❓ Asking follow-up questions...")
        insights = client.ask(
            f"Based on document {uploaded_file.file_id}, "
            "what are the main insights or recommendations?"
        )
        print("💡 Insights:")
        print(insights)
        
        # Save results to output directory
        script_output_dir = output_dir(Path(__file__))
        
        summary_file = script_output_dir / "document_summary.txt"
        insights_file = script_output_dir / "document_insights.txt"
        
        summary_file.write_text(summary, encoding='utf-8')
        insights_file.write_text(insights, encoding='utf-8')
        
        print(f"\n📁 Results saved to:")
        print(f"   Summary: {summary_file}")
        print(f"   Insights: {insights_file}")
        
    except Exception as e:
        print(f"❌ Document processing failed: {e}")
        return 1
    
    print(f"\n🎉 Document analysis complete!")
    
    # Show output directory
    script_output_dir = output_dir(Path(__file__))
    print(f"\n📁 All outputs saved to: {script_output_dir}")
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    if exit_code != 0:
        print("\n💡 Need help? Check the documentation or run with proper configuration")
    exit(exit_code)
