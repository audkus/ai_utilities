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

from ai_utilities import AiClient, AsyncAiClient, UploadedFile
from ai_utilities.providers.provider_exceptions import FileTransferError, ProviderCapabilityError


def create_sample_files():
    """Create sample files for demonstration."""
    temp_dir = Path(tempfile.mkdtemp())
    
    # Create sample text file
    text_file = temp_dir / "sample.txt"
    with open(text_file, "w") as f:
        f.write("This is a sample text file for Files API demonstration.\n")
        f.write("It contains multiple lines of text.\n")
        f.write("The Files API can handle various file types.\n")
    
    # Create sample JSON file
    json_file = temp_dir / "data.json"
    with open(json_file, "w") as f:
        f.write('{"name": "demo", "type": "files-api", "version": "1.0"}\n')
    
    # Create sample CSV file
    csv_file = temp_dir / "data.csv"
    with open(csv_file, "w") as f:
        f.write("id,name,value\n")
        f.write("1,item1,100\n")
        f.write("2,item2,200\n")
        f.write("3,item3,300\n")
    
    print(f"Created sample files in: {temp_dir}")
    return temp_dir, text_file, json_file, csv_file


def demo_basic_operations():
    """Demonstrate basic file upload and download operations."""
    print("\n=== Basic Operations Demo ===")
    
    # Create sample files
    temp_dir, text_file, json_file, csv_file = create_sample_files()
    
    try:
        # Initialize client
        client = AiClient()
        print("✅ AiClient initialized")
        
        # Upload files with different purposes
        print("\n--- Uploading Files ---")
        
        # Upload text file for assistants
        try:
            text_uploaded = client.upload_file(text_file, purpose="assistants")
            print(f"✅ Uploaded text file: {text_uploaded.file_id}")
            print(f"   Filename: {text_uploaded.filename}")
            print(f"   Size: {text_uploaded.bytes} bytes")
            print(f"   Purpose: {text_uploaded.purpose}")
        except Exception as e:
            print(f"❌ Text upload failed: {e}")
            return
        
        # Upload JSON file for fine-tuning
        try:
            json_uploaded = client.upload_file(
                json_file, 
                purpose="fine-tune",
                filename="training-data.json"
            )
            print(f"✅ Uploaded JSON file: {json_uploaded.file_id}")
            print(f"   Custom filename: {json_uploaded.filename}")
        except Exception as e:
            print(f"❌ JSON upload failed: {e}")
            return
        
        # Upload CSV file
        try:
            csv_uploaded = client.upload_file(csv_file, purpose="assistants")
            print(f"✅ Uploaded CSV file: {csv_uploaded.file_id}")
        except Exception as e:
            print(f"❌ CSV upload failed: {e}")
            return
        
        # Download files
        print("\n--- Downloading Files ---")
        
        # Download as bytes
        try:
            content = client.download_file(text_uploaded.file_id)
            print(f"✅ Downloaded text content: {len(content)} bytes")
            print(f"   Preview: {content[:50]}...")
        except Exception as e:
            print(f"❌ Download failed: {e}")
        
        # Download to file
        try:
            download_dir = temp_dir / "downloads"
            download_dir.mkdir(exist_ok=True)
            
            saved_path = client.download_file(
                json_uploaded.file_id, 
                to_path=download_dir / "downloaded.json"
            )
            print(f"✅ Downloaded to: {saved_path}")
            
            # Verify content
            with open(saved_path) as f:
                saved_content = f.read()
            print(f"   Content: {saved_content.strip()}")
        except Exception as e:
            print(f"❌ File download failed: {e}")
        
        return [text_uploaded, json_uploaded, csv_uploaded]
    
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
        print(f"\n🧹 Cleaned up temporary directory: {temp_dir}")


def demo_error_handling():
    """Demonstrate error handling scenarios."""
    print("\n=== Error Handling Demo ===")
    
    client = AiClient()
    
    # Test 1: Nonexistent file
    print("\n--- Test 1: Nonexistent File ---")
    try:
        client.upload_file("nonexistent.txt")
    except ValueError as e:
        print(f"✅ Caught ValueError: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    # Test 2: Empty file ID
    print("\n--- Test 2: Empty File ID ---")
    try:
        client.download_file("")
    except ValueError as e:
        print(f"✅ Caught ValueError: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    # Test 3: Invalid file ID
    print("\n--- Test 3: Invalid File ID ---")
    try:
        client.download_file("invalid-file-id")
    except FileTransferError as e:
        print(f"✅ Caught FileTransferError: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def demo_provider_capabilities():
    """Demonstrate provider capability handling."""
    print("\n=== Provider Capabilities Demo ===")
    
    from ai_utilities.providers import OpenAICompatibleProvider
    
    # Create client with OpenAI-compatible provider
    compatible_provider = OpenAICompatibleProvider(base_url="http://localhost:1234/v1")
    client = AiClient(provider=compatible_provider)
    
    # Test upload capability
    print("\n--- Upload Capability Test ---")
    try:
        client.upload_file("test.txt")
    except ProviderCapabilityError as e:
        print(f"✅ Expected ProviderCapabilityError: {e.capability}")
        print(f"   Provider: {e.provider}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    # Test download capability
    print("\n--- Download Capability Test ---")
    try:
        client.download_file("file-123")
    except ProviderCapabilityError as e:
        print(f"✅ Expected ProviderCapabilityError: {e.capability}")
        print(f"   Provider: {e.provider}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


async def demo_async_operations():
    """Demonstrate async file operations."""
    print("\n=== Async Operations Demo ===")
    
    # Create sample files
    temp_dir, text_file, json_file, csv_file = create_sample_files()
    
    try:
        # Initialize async client
        client = AsyncAiClient()
        print("✅ AsyncAiClient initialized")
        
        # Upload files concurrently
        print("\n--- Concurrent Upload ---")
        start_time = time.time()
        
        upload_tasks = [
            client.upload_file(text_file, purpose="assistants"),
            client.upload_file(json_file, purpose="fine-tune"),
            client.upload_file(csv_file, purpose="assistants")
        ]
        
        try:
            uploaded_files = await asyncio.gather(*upload_tasks)
            upload_time = time.time() - start_time
            
            print(f"✅ Uploaded {len(uploaded_files)} files in {upload_time:.2f}s")
            for i, file in enumerate(uploaded_files):
                print(f"   File {i+1}: {file.filename} ({file.file_id})")
        except Exception as e:
            print(f"❌ Concurrent upload failed: {e}")
            return
        
        # Download files concurrently
        print("\n--- Concurrent Download ---")
        start_time = time.time()
        
        download_tasks = [
            client.download_file(file.file_id) for file in uploaded_files
        ]
        
        try:
            contents = await asyncio.gather(*download_tasks)
            download_time = time.time() - start_time
            
            print(f"✅ Downloaded {len(contents)} files in {download_time:.2f}s")
            for i, content in enumerate(contents):
                print(f"   Content {i+1}: {len(content)} bytes")
        except Exception as e:
            print(f"❌ Concurrent download failed: {e}")
    
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
        print(f"\n🧹 Cleaned up temporary directory: {temp_dir}")


def demo_file_metadata():
    """Demonstrate UploadedFile model and metadata handling."""
    print("\n=== File Metadata Demo ===")
    
    # Create sample file
    temp_dir, text_file, _, _ = create_sample_files()
    
    try:
        client = AiClient()
        
        # Upload file
        uploaded_file = client.upload_file(text_file, purpose="assistants")
        
        print(f"--- UploadedFile Object ---")
        print(f"Type: {type(uploaded_file)}")
        print(f"File ID: {uploaded_file.file_id}")
        print(f"Filename: {uploaded_file.filename}")
        print(f"Size: {uploaded_file.bytes} bytes")
        print(f"Provider: {uploaded_file.provider}")
        print(f"Purpose: {uploaded_file.purpose}")
        print(f"Created: {uploaded_file.created_at}")
        
        # Test string representations
        print(f"\n--- String Representations ---")
        print(f"str(): {uploaded_file}")
        print(f"repr(): {repr(uploaded_file)}")
        
        # Test JSON serialization
        print(f"\n--- JSON Serialization ---")
        json_data = uploaded_file.model_dump_json()
        print(f"JSON: {json_data}")
        
        dict_data = uploaded_file.model_dump()
        print(f"Dict: {dict_data}")
    
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
        print(f"\n🧹 Cleaned up temporary directory: {temp_dir}")


def main():
    """Run all demonstration scenarios."""
    print("🚀 Files API Demo")
    print("=" * 50)
    
    try:
        # Run demonstrations
        demo_basic_operations()
        demo_error_handling()
        demo_provider_capabilities()
        demo_file_metadata()
        
        # Run async demo
        print("\n" + "=" * 50)
        asyncio.run(demo_async_operations())
        
        print("\n" + "=" * 50)
        print("✅ All demos completed successfully!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
