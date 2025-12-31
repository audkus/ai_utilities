#!/usr/bin/env python3
"""
Files API Quickstart

Simple examples to get started with the Files API.
"""

from ai_utilities import AiClient, AsyncAiClient
from pathlib import Path

# Basic file upload and download
def basic_example():
    client = AiClient()
    
    # Upload a file
    file = client.upload_file("document.pdf", purpose="assistants")
    print(f"Uploaded: {file.file_id}")
    
    # Download as bytes
    content = client.download_file(file.file_id)
    
    # Download to file
    path = client.download_file(file.file_id, to_path="downloaded.pdf")

# Async file operations
async def async_example():
    client = AsyncAiClient()
    
    # Upload asynchronously
    file = await client.upload_file("data.csv", purpose="fine-tune")
    
    # Download asynchronously
    content = await client.download_file(file.file_id)

# Error handling
def error_handling_example():
    from ai_utilities.providers.provider_exceptions import FileTransferError, ProviderCapabilityError
    
    client = AiClient()
    
    try:
        file = client.upload_file("report.pdf")
    except FileTransferError as e:
        print(f"Upload failed: {e}")
    except ProviderCapabilityError as e:
        print(f"Provider doesn't support files: {e}")

if __name__ == "__main__":
    basic_example()
