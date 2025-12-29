"""Integration tests for Files API functionality.

These tests require a real OpenAI API key and make actual API calls.
They are marked as "integration" and can be skipped with: pytest -m "not integration"
"""

import asyncio
import os
import tempfile
from pathlib import Path
from datetime import datetime

import pytest

from ai_utilities import AiClient, AsyncAiClient, UploadedFile
from ai_utilities.providers.provider_exceptions import FileTransferError, ProviderCapabilityError


# Skip integration tests if no API key
pytest.importorskip("openai")
has_api_key = bool(os.getenv("AI_API_KEY"))
pytestmark = pytest.mark.integration if has_api_key else pytest.mark.skip(reason="No AI_API_KEY set")


class TestFilesIntegration:
    """Integration tests for Files API with real OpenAI API."""
    
    @pytest.fixture
    def temp_files(self):
        """Create temporary files for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        
        # Create test files
        text_file = temp_dir / "test.txt"
        with open(text_file, "w") as f:
            f.write("This is a test file for Files API integration testing.\n")
            f.write("It contains multiple lines of text.\n")
        
        json_file = temp_dir / "test.json"
        with open(json_file, "w") as f:
            f.write('{"test": true, "type": "integration", "content": "test data"}\n')
        
        csv_file = temp_dir / "test.csv"
        with open(csv_file, "w") as f:
            f.write("id,name,value\n")
            f.write("1,test1,100\n")
            f.write("2,test2,200\n")
        
        yield temp_dir, text_file, json_file, csv_file
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def client(self):
        """Create AiClient with real OpenAI provider."""
        return AiClient()
    
    @pytest.fixture
    def async_client(self):
        """Create AsyncAiClient with real OpenAI provider."""
        return AsyncAiClient()
    
    def test_upload_file_real_api(self, client, temp_files):
        """Test actual file upload to OpenAI API."""
        temp_dir, text_file, json_file, csv_file = temp_files
        
        # Upload text file
        uploaded_file = client.upload_file(text_file, purpose="assistants")
        
        # Verify uploaded file metadata
        assert isinstance(uploaded_file, UploadedFile)
        assert uploaded_file.file_id.startswith("file-")
        assert uploaded_file.filename == "test.txt"
        assert uploaded_file.bytes > 0
        assert uploaded_file.provider == "openai"
        assert uploaded_file.purpose == "assistants"
        assert uploaded_file.created_at is not None
        assert isinstance(uploaded_file.created_at, datetime)
        
        print(f"✅ Uploaded file: {uploaded_file.file_id}")
        return uploaded_file
    
    def test_upload_file_different_purposes(self, client, temp_files):
        """Test uploading files with different purposes."""
        temp_dir, text_file, json_file, csv_file = temp_files
        
        # Test assistants purpose
        assistants_file = client.upload_file(text_file, purpose="assistants")
        assert assistants_file.purpose == "assistants"
        
        # Test fine-tune purpose
        fine_tune_file = client.upload_file(json_file, purpose="fine-tune")
        assert fine_tune_file.purpose == "fine-tune"
        
        print(f"✅ Uploaded files with different purposes")
    
    def test_upload_file_custom_filename(self, client, temp_files):
        """Test uploading file with custom filename."""
        temp_dir, text_file, json_file, csv_file = temp_files
        
        # Upload with custom filename
        uploaded_file = client.upload_file(
            text_file, 
            purpose="assistants",
            filename="custom-name.txt"
        )
        
        assert uploaded_file.filename == "custom-name.txt"
        print(f"✅ Uploaded with custom filename: {uploaded_file.filename}")
    
    def test_download_file_real_api(self, client, temp_files):
        """Test actual file download from OpenAI API."""
        temp_dir, text_file, json_file, csv_file = temp_files
        
        # First upload a file
        uploaded_file = client.upload_file(text_file, purpose="assistants")
        
        # Download the file content
        content = client.download_file(uploaded_file.file_id)
        
        # Verify downloaded content
        assert isinstance(content, bytes)
        assert len(content) > 0
        
        # Convert to string and verify original content
        text_content = content.decode('utf-8')
        assert "This is a test file" in text_content
        assert "multiple lines of text" in text_content
        
        print(f"✅ Downloaded {len(content)} bytes")
    
    def test_download_file_to_disk(self, client, temp_files):
        """Test downloading file to disk."""
        temp_dir, text_file, json_file, csv_file = temp_files
        
        # Upload a file
        uploaded_file = client.upload_file(json_file, purpose="assistants")
        
        # Download to specific path
        download_path = temp_dir / "downloaded.json"
        saved_path = client.download_file(
            uploaded_file.file_id, 
            to_path=download_path
        )
        
        # Verify file was saved
        assert saved_path == download_path
        assert download_path.exists()
        
        # Verify content
        with open(download_path) as f:
            saved_content = f.read()
        assert "integration" in saved_content
        assert "test data" in saved_content
        
        print(f"✅ Downloaded to: {saved_path}")
    
    def test_upload_download_roundtrip(self, client, temp_files):
        """Test complete upload/download roundtrip."""
        temp_dir, text_file, json_file, csv_file = temp_files
        
        # Read original content
        with open(csv_file, 'rb') as f:
            original_content = f.read()
        
        # Upload file
        uploaded_file = client.upload_file(csv_file, purpose="assistants")
        
        # Download file
        downloaded_content = client.download_file(uploaded_file.file_id)
        
        # Verify roundtrip integrity
        assert downloaded_content == original_content
        
        print(f"✅ Roundtrip successful: {len(original_content)} bytes")
    
    def test_list_uploaded_files(self, client, temp_files):
        """Test that uploaded files appear in OpenAI file list."""
        temp_dir, text_file, json_file, csv_file = temp_files
        
        # Upload files
        file1 = client.upload_file(text_file, purpose="assistants")
        file2 = client.upload_file(json_file, purpose="fine-tune")
        
        # List files using OpenAI client directly
        openai_files = client.provider.client.files.list()
        
        # Find our uploaded files
        uploaded_ids = {file1.file_id, file2.file_id}
        found_ids = {f.id for f in openai_files.data if f.id in uploaded_ids}
        
        assert found_ids == uploaded_ids, "Not all uploaded files found in list"
        
        print(f"✅ Found {len(found_ids)} uploaded files in API list")
    
    def test_delete_uploaded_file(self, client, temp_files):
        """Test deleting uploaded files."""
        temp_dir, text_file, json_file, csv_file = temp_files
        
        # Upload a file
        uploaded_file = client.upload_file(text_file, purpose="assistants")
        
        # Delete the file using OpenAI client directly
        client.provider.client.files.delete(uploaded_file.file_id)
        
        # Try to download (should fail)
        with pytest.raises(FileTransferError) as exc_info:
            client.download_file(uploaded_file.file_id)
        
        assert "Not found" in str(exc_info.value) or "404" in str(exc_info.value)
        
        print(f"✅ Successfully deleted and confirmed file is gone")
    
    @pytest.mark.asyncio
    async def test_async_upload_file(self, async_client, temp_files):
        """Test async file upload."""
        temp_dir, text_file, json_file, csv_file = temp_files
        
        # Upload file asynchronously
        uploaded_file = await async_client.upload_file(text_file, purpose="assistants")
        
        # Verify uploaded file
        assert isinstance(uploaded_file, UploadedFile)
        assert uploaded_file.file_id.startswith("file-")
        assert uploaded_file.filename == "test.txt"
        assert uploaded_file.purpose == "assistants"
        
        print(f"✅ Async upload successful: {uploaded_file.file_id}")
    
    @pytest.mark.asyncio
    async def test_async_download_file(self, async_client, temp_files):
        """Test async file download."""
        temp_dir, text_file, json_file, csv_file = temp_files
        
        # Upload file
        uploaded_file = await async_client.upload_file(json_file, purpose="assistants")
        
        # Download asynchronously
        content = await async_client.download_file(uploaded_file.file_id)
        
        # Verify content
        assert isinstance(content, bytes)
        assert len(content) > 0
        text_content = content.decode('utf-8')
        assert "integration" in text_content
        
        print(f"✅ Async download successful: {len(content)} bytes")
    
    @pytest.mark.asyncio
    async def test_async_upload_download_roundtrip(self, async_client, temp_files):
        """Test async upload/download roundtrip."""
        temp_dir, text_file, json_file, csv_file = temp_files
        
        # Read original content
        with open(text_file, 'rb') as f:
            original_content = f.read()
        
        # Upload and download asynchronously
        uploaded_file = await async_client.upload_file(text_file, purpose="assistants")
        downloaded_content = await async_client.download_file(uploaded_file.file_id)
        
        # Verify integrity
        assert downloaded_content == original_content
        
        print(f"✅ Async roundtrip successful: {len(original_content)} bytes")
    
    @pytest.mark.asyncio
    async def test_async_concurrent_operations(self, async_client, temp_files):
        """Test concurrent async file operations."""
        temp_dir, text_file, json_file, csv_file = temp_files
        
        import time
        start_time = time.time()
        
        # Upload files concurrently
        upload_tasks = [
            async_client.upload_file(text_file, purpose="assistants"),
            async_client.upload_file(json_file, purpose="fine-tune"),
            async_client.upload_file(csv_file, purpose="assistants")
        ]
        
        uploaded_files = await asyncio.gather(*upload_tasks)
        upload_time = time.time() - start_time
        
        # Verify all uploads succeeded
        assert len(uploaded_files) == 3
        for file in uploaded_files:
            assert isinstance(file, UploadedFile)
            assert file.file_id.startswith("file-")
        
        print(f"✅ Concurrent upload: {len(uploaded_files)} files in {upload_time:.2f}s")
        
        # Download files concurrently
        start_time = time.time()
        download_tasks = [
            async_client.download_file(file.file_id) for file in uploaded_files
        ]
        
        contents = await asyncio.gather(*download_tasks)
        download_time = time.time() - start_time
        
        # Verify all downloads succeeded
        assert len(contents) == 3
        for content in contents:
            assert isinstance(content, bytes)
            assert len(content) > 0
        
        print(f"✅ Concurrent download: {len(contents)} files in {download_time:.2f}s")
    
    def test_file_size_limits(self, client, temp_files):
        """Test uploading files of different sizes."""
        temp_dir, text_file, json_file, csv_file = temp_files
        
        # Create a larger file (but still reasonable for testing)
        large_file = temp_dir / "large.txt"
        with open(large_file, "w") as f:
            for i in range(1000):
                f.write(f"Line {i}: This is test content for file size testing.\n")
        
        # Upload the larger file
        uploaded_file = client.upload_file(large_file, purpose="assistants")
        
        # Verify it was uploaded successfully
        assert uploaded_file.bytes > 50000  # Should be > 50KB
        print(f"✅ Large file upload successful: {uploaded_file.bytes} bytes")
        
        # Download and verify integrity
        content = client.download_file(uploaded_file.file_id)
        assert len(content) == uploaded_file.bytes
    
    def test_different_file_types(self, client, temp_files):
        """Test uploading different file types."""
        temp_dir, text_file, json_file, csv_file = temp_files
        
        # Create additional file types
        # JavaScript file
        js_file = temp_dir / "test.js"
        with open(js_file, "w") as f:
            f.write("console.log('Hello from JavaScript file');\n")
        
        # Python file
        py_file = temp_dir / "test.py"
        with open(py_file, "w") as f:
            f.write("# Python test file\nprint('Hello, World!')\n")
        
        # Upload different file types
        files_to_test = [
            (text_file, "text/plain"),
            (json_file, "application/json"),
            (csv_file, "text/csv"),
            (js_file, "application/javascript"),
            (py_file, "text/x-python")
        ]
        
        uploaded_files = []
        for file_path, expected_mime in files_to_test:
            uploaded_file = client.upload_file(file_path, purpose="assistants")
            uploaded_files.append(uploaded_file)
            print(f"✅ Uploaded {file_path.suffix} file: {uploaded_file.file_id}")
        
        # Verify all files can be downloaded
        for uploaded_file in uploaded_files:
            content = client.download_file(uploaded_file.file_id)
            assert len(content) > 0
        
        print(f"✅ All {len(uploaded_files)} file types work correctly")
    
    def test_error_handling_real_api(self, client, temp_files):
        """Test error handling with real API."""
        temp_dir, text_file, json_file, csv_file = temp_files
        
        # Test downloading non-existent file
        with pytest.raises(FileTransferError) as exc_info:
            client.download_file("file-nonexistent")
        
        assert "Not found" in str(exc_info.value) or "404" in str(exc_info.value)
        print("✅ Correct error for non-existent file")
        
        # Upload a file then delete it to test download of deleted file
        uploaded_file = client.upload_file(text_file, purpose="assistants")
        
        # Delete the file
        client.provider.client.files.delete(uploaded_file.file_id)
        
        # Try to download deleted file
        with pytest.raises(FileTransferError) as exc_info:
            client.download_file(uploaded_file.file_id)
        
        assert "Not found" in str(exc_info.value) or "404" in str(exc_info.value)
        print("✅ Correct error for deleted file")


class TestOpenAICompatibleIntegration:
    """Integration tests for OpenAI-compatible provider (should fail gracefully)."""
    
    def test_compatible_provider_capability_errors(self):
        """Test that OpenAI-compatible provider raises capability errors."""
        from ai_utilities.providers import OpenAICompatibleProvider
        
        # Create client with OpenAI-compatible provider
        provider = OpenAICompatibleProvider(base_url="http://localhost:1234/v1")
        client = AiClient(provider=provider)
        
        # Test upload capability error
        with pytest.raises(ProviderCapabilityError) as exc_info:
            client.upload_file("test.txt")
        
        assert exc_info.value.capability == "Files API (upload)"
        assert exc_info.value.provider == "openai_compatible"
        
        # Test download capability error
        with pytest.raises(ProviderCapabilityError) as exc_info:
            client.download_file("file-123")
        
        assert exc_info.value.capability == "Files API (download)"
        assert exc_info.value.provider == "openai_compatible"
        
        print("✅ OpenAI-compatible provider correctly raises capability errors")
