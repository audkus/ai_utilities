#!/usr/bin/env python3
"""
Files API Quickstart

Simple examples to get started with the Files API.
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

from ai_utilities import AiClient, AsyncAiClient


def main():
    """Demonstrate Files API operations."""
    
    print_header("📁 Files API Quickstart")
    
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
    
    # Basic file upload and download
    print("\n📤 Basic file upload and download...")
    
    # Use asset from examples/assets directory
    document_file = assets_dir() / "sample_document.pdf"
    print(f"📄 Using file: {document_file}")
    
    # Check if document file exists
    if not document_file.exists():
        print(f"❌ Document file not found: {document_file}")
        print("💡 Make sure sample_document.pdf exists in examples/assets/")
        return 1
    
    try:
        # Upload a file
        print("   Uploading file...")
        file = client.upload_file(str(document_file), purpose="assistants")
        print(f"✅ Uploaded: {file.file_id}")
        
        # Download as bytes
        print("   Downloading as bytes...")
        content = client.download_file(file.file_id)
        print(f"✅ Downloaded {len(content)} bytes")
        
        # Download to file
        print("   Downloading to file...")
        script_output_dir = output_dir(Path(__file__))
        download_path = script_output_dir / "downloaded_document.pdf"
        
        path = client.download_file(file.file_id, to_path=str(download_path))
        print(f"✅ Downloaded to: {path}")
        
        # Show file info
        print(f"\n📊 File Information:")
        print(f"   File ID: {file.file_id}")
        print(f"   Purpose: {file.purpose}")
        print(f"   Size: {len(content)} bytes")
        print(f"   Downloaded to: {download_path}")
        
    except Exception as e:
        print(f"❌ File operations failed: {e}")
        return 1
    
    print(f"\n🎉 Files API demonstration complete!")
    
    # Show output directory
    script_output_dir = output_dir(Path(__file__))
    print(f"\n📁 All outputs saved to: {script_output_dir}")
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    if exit_code != 0:
        print("\n💡 Need help? Check the documentation or run with proper configuration")
    exit(exit_code)
