#!/usr/bin/env python3
"""
Files API Demo Script

This script demonstrates the Files API functionality including:
- File upload and download
- Error handling
- Async operations
- File management

Usage:
    python examples/files_demo.py
"""

import asyncio
import tempfile
import time
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

from ai_utilities import AiClient, AsyncAiClient, UploadedFile


def main():
    """Demonstrate Files API operations."""
    
    print_header("📁 Advanced Files API Demo")
    
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
    print(f"\n📄 Using file: {document_file}")
    
    # Check if document file exists
    if not document_file.exists():
        print(f"❌ Document file not found: {document_file}")
        print("💡 Make sure sample_document.pdf exists in examples/assets/")
        return 1
    
    # Basic file operations
    print("\n🎯 Basic File Operations")
    print("-" * 30)
    
    try:
        # Upload file
        print("   Uploading file...")
        uploaded_file = client.upload_file(str(document_file), purpose="assistants")
        print(f"✅ File uploaded: {uploaded_file.file_id}")
        
        # Get file info
        print("   Getting file info...")
        file_info = client.get_file_info(uploaded_file.file_id)
        print(f"   File name: {file_info.filename}")
        print(f"   File size: {file_info.bytes} bytes")
        print(f"   Purpose: {file_info.purpose}")
        print(f"   Created at: {file_info.created_at}")
        
        # Download as bytes
        print("   Downloading as bytes...")
        content = client.download_file(uploaded_file.file_id)
        print(f"✅ Downloaded {len(content)} bytes")
        
        # Download to file
        print("   Downloading to file...")
        script_output_dir = output_dir(Path(__file__))
        download_path = script_output_dir / "downloaded_document.pdf"
        
        path = client.download_file(uploaded_file.file_id, to_path=str(download_path))
        print(f"✅ Downloaded to: {path}")
        
    except Exception as e:
        print(f"❌ File operations failed: {e}")
        return 1
    
    # List files
    print("\n🎯 List Files")
    print("-" * 30)
    
    try:
        print("   Listing uploaded files...")
        files = client.list_files()
        print(f"✅ Found {len(files)} files")
        
        for file in files[:5]:  # Show first 5 files
            print(f"   - {file.filename} ({file.bytes} bytes, {file.purpose})")
        
        if len(files) > 5:
            print(f"   ... and {len(files) - 5} more files")
            
    except Exception as e:
        print(f"❌ List files failed: {e}")
        return 1
    
    # Delete file
    print("\n🎯 Delete File")
    print("-" * 30)
    
    try:
        print(f"   Deleting file: {uploaded_file.file_id}")
        client.delete_file(uploaded_file.file_id)
        print("✅ File deleted successfully")
        
    except Exception as e:
        print(f"❌ Delete file failed: {e}")
        return 1
    
    # Show summary
    print(f"\n📊 Operations Summary:")
    print(f"   File uploaded: {document_file.name}")
    print(f"   File size: {document_file.stat().st_size} bytes")
    print(f"   Output directory: {script_output_dir}")
    
    print(f"\n🎉 Advanced Files API demo complete!")
    
    # Show output directory
    script_output_dir = output_dir(Path(__file__))
    print(f"\n📁 All outputs saved to: {script_output_dir}")
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    if exit_code != 0:
        print("\n💡 Need help? Check the documentation or run with proper configuration")
    exit(exit_code)
