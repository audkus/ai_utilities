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

from ai_utilities import AiClient, AsyncAiClient, UploadedFile, AiSettings
from ai_utilities.providers.provider_exceptions import FileTransferError, ProviderCapabilityError

# Skip integration tests if no API key
has_api_key = bool(os.getenv("OPENAI_API_KEY") or os.getenv("AI_OPENAI_API_KEY"))
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not has_api_key, reason="No OpenAI API key set")
]


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
        settings = AiSettings(
            openai_api_key=os.getenv("OPENAI_API_KEY") or os.getenv("AI_OPENAI_API_KEY"),  # Use provider-specific key
            provider="openai",
            model="gpt-4o-mini"  # Use a real model for integration tests
        )
        return AiClient(settings=settings)
    
    @pytest.fixture
    def async_client(self):
        """Create AsyncAiClient with real OpenAI provider."""
        settings = AiSettings(
            openai_api_key=os.getenv("OPENAI_API_KEY") or os.getenv("AI_OPENAI_API_KEY"),  # Use provider-specific key
            provider="openai",
            model="gpt-4o-mini"  # Use a real model for integration tests
        )
        return AsyncAiClient(settings=settings)
    
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
        
        # Upload a file with assistants purpose (downloadable for some files)
        # Note: OpenAI restricts downloading assistants files, so we'll test the error handling
        uploaded_file = client.upload_file(text_file, purpose="assistants")
        
        # Download the file content (this should fail with OpenAI's restrictions)
        try:
            content = client.download_file(uploaded_file.file_id)
            # If it succeeds, verify the content
            assert isinstance(content, bytes)
            assert len(content) > 0
            print(f"✅ Download successful: {len(content)} bytes")
        except FileTransferError as e:
            # Expected behavior for OpenAI assistants files
            assert "Not allowed to download files of purpose: assistants" in str(e)
            print(f"✅ Correctly handled download restriction: {e}")
    
    def test_download_file_to_disk(self, client, temp_files):
        """Test downloading file to disk."""
        temp_dir, text_file, json_file, csv_file = temp_files
        
        # Create a JSONL file for fine-tuning (required format)
        jsonl_file = temp_dir / "fine_tune_data.jsonl"
        with open(jsonl_file, 'w') as f:
            f.write('{"prompt": "What is 2+2?", "completion": "4"}\n')
            f.write('{"prompt": "What is 3+3?", "completion": "6"}\n')
        
        # Upload a JSONL file with fine-tune purpose (allows downloading)
        uploaded_file = client.upload_file(jsonl_file, purpose="fine-tune")
        
        # Download to specific path
        download_path = temp_dir / "downloaded.json"
        saved_path = client.download_file(
            uploaded_file.file_id, 
            to_path=download_path
        )
        
        # Verify file was saved
        assert saved_path == download_path
        assert download_path.exists()
        
        # Verify content (JSONL format)
        with open(download_path) as f:
            saved_content = f.read()
        assert "prompt" in saved_content
        assert "completion" in saved_content
        
        print(f"✅ Downloaded to: {saved_path}")
    
    def test_upload_download_roundtrip(self, client, temp_files):
        """Test complete upload/download roundtrip."""
        temp_dir, text_file, json_file, csv_file = temp_files
        
        # Create a JSONL file for fine-tuning (required format)
        jsonl_file = temp_dir / "fine_tune_data.jsonl"
        with open(jsonl_file, 'w') as f:
            f.write('{"prompt": "What is 2+2?", "completion": "4"}\n')
            f.write('{"prompt": "What is 3+3?", "completion": "6"}\n')
        
        # Read original content
        with open(jsonl_file, 'rb') as f:
            original_content = f.read()
        
        # Upload file with fine-tune purpose (allows downloading)
        uploaded_file = client.upload_file(jsonl_file, purpose="fine-tune")
        
        # Download file
        downloaded_content = client.download_file(uploaded_file.file_id)
        
        # Verify roundtrip integrity
        assert downloaded_content == original_content
        
        print(f"✅ Roundtrip successful: {len(original_content)} bytes")
    
    def test_list_uploaded_files(self, client, temp_files):
        """Test that uploaded files appear in file list."""
        temp_dir, text_file, json_file, csv_file = temp_files
        
        # Upload files
        file1 = client.upload_file(text_file, purpose="assistants")
        file2 = client.upload_file(json_file, purpose="fine-tune")
        
        # List files using client method
        files = client.list_files()
        
        # Find our uploaded files
        uploaded_ids = {file1.file_id, file2.file_id}
        found_ids = {f.file_id for f in files if f.file_id in uploaded_ids}
        
        assert found_ids == uploaded_ids, "Not all uploaded files found in list"
        
        # Test filtering by purpose
        assistants_files = client.list_files(purpose="assistants")
        fine_tune_files = client.list_files(purpose="fine-tune")
        
        assert file1.file_id in [f.file_id for f in assistants_files]
        assert file2.file_id in [f.file_id for f in fine_tune_files]
        
        print(f"✅ Found {len(found_ids)} uploaded files in client list")
    
    def test_delete_uploaded_file(self, client, temp_files):
        """Test deleting uploaded files."""
        temp_dir, text_file, json_file, csv_file = temp_files
        
        # Upload a file
        uploaded_file = client.upload_file(text_file, purpose="assistants")
        
        # Verify file exists in list
        files_before = client.list_files()
        assert uploaded_file.file_id in [f.file_id for f in files_before]
        
        # Delete the file using client method
        success = client.delete_file(uploaded_file.file_id)
        assert success, "File deletion should return True"
        
        # Verify file is no longer in list
        files_after = client.list_files()
        assert uploaded_file.file_id not in [f.file_id for f in files_after]
        
        print(f"✅ Successfully deleted file: {uploaded_file.file_id}")
    
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
        
        # Upload file with assistants purpose (test download restrictions)
        uploaded_file = await async_client.upload_file(text_file, purpose="assistants")
        
        # Download asynchronously (this should fail with OpenAI's restrictions)
        try:
            content = await async_client.download_file(uploaded_file.file_id)
            # If it succeeds, verify the content
            assert isinstance(content, bytes)
            assert len(content) > 0
            text_content = content.decode('utf-8')
            assert "integration" in text_content
            assert "test data" in text_content
            print(f"✅ Async download successful: {len(content)} bytes")
        except FileTransferError as e:
            # Expected behavior for OpenAI assistants files
            assert "Not allowed to download files of purpose: assistants" in str(e)
            print(f"✅ Correctly handled async download restriction: {e}")
    
    @pytest.mark.asyncio
    async def test_async_upload_download_roundtrip(self, async_client, temp_files):
        """Test async upload/download roundtrip."""
        temp_dir, text_file, json_file, csv_file = temp_files
        
        # Read original content
        with open(text_file, 'rb') as f:
            original_content = f.read()
        
        # Upload and download asynchronously with assistants purpose (test restrictions)
        uploaded_file = await async_client.upload_file(text_file, purpose="assistants")
        
        try:
            downloaded_content = await async_client.download_file(uploaded_file.file_id)
            # If download succeeds, verify integrity
            assert downloaded_content == original_content
            print(f"✅ Async roundtrip successful: {len(original_content)} bytes")
        except FileTransferError as e:
            # Expected behavior for OpenAI assistants files
            assert "Not allowed to download files of purpose: assistants" in str(e)
            print(f"✅ Correctly handled async roundtrip restriction: {e}")
    
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
        
        # Clean up - delete all uploaded files concurrently
        start_time = time.time()
        delete_tasks = [async_client.delete_file(file.file_id) for file in uploaded_files]
        delete_results = await asyncio.gather(*delete_tasks)
        delete_time = time.time() - start_time
        
        # Verify all deletions succeeded
        assert all(delete_results), "Some files failed to delete"
        print(f"✅ Concurrent delete: {len(delete_results)} files in {delete_time:.2f}s")
    
    def test_file_size_limits(self, client, temp_files):
        """Test uploading files of different sizes."""
        temp_dir, text_file, json_file, csv_file = temp_files
        
        # Create a larger file (but still reasonable for testing)
        large_file = temp_dir / "large.txt"
        with open(large_file, "w") as f:
            for i in range(1000):
                f.write(f"Line {i}: This is test content for file size testing.\n")
        
        # Upload the larger file with assistants purpose
        uploaded_file = client.upload_file(large_file, purpose="assistants")
        
        # Verify it was uploaded successfully
        assert uploaded_file.bytes > 50000  # Should be > 50KB
        print(f"✅ Large file upload successful: {uploaded_file.bytes} bytes")
        
        # Skip download test for assistants files (OpenAI restriction)
        print(f"✅ Skipped download test for assistants file (OpenAI restriction)")
    
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
            uploaded_file = client.upload_file(file_path, purpose="assistants")  # Use assistants purpose
            uploaded_files.append(uploaded_file)
            print(f"✅ Uploaded {file_path.suffix} file: {uploaded_file.file_id}")
        
        # Skip download test for assistants files (OpenAI restriction)
        print(f"✅ All {len(uploaded_files)} file types uploaded successfully (downloads skipped due to OpenAI restrictions)")
    
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
        from pathlib import Path
        import tempfile
        import os
        
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test content for capability error test")
            test_file_path = f.name
        
        try:
            # Create client with OpenAI-compatible provider
            provider = OpenAICompatibleProvider(base_url="http://localhost:1234/v1")
            settings = AiSettings(api_key="fake-key", provider="openai_compatible")
            client = AiClient(settings=settings, provider=provider)
            
            # Test upload capability error
            with pytest.raises(ProviderCapabilityError) as exc_info:
                client.upload_file(test_file_path)
            
            assert exc_info.value.capability == "Files API (upload)"
            assert exc_info.value.provider == "openai_compatible"
            
            # Test download capability error
            with pytest.raises(ProviderCapabilityError) as exc_info:
                client.download_file("file-123")
            
            assert exc_info.value.capability == "Files API (download)"
            assert exc_info.value.provider == "openai_compatible"
            
            print("✅ OpenAI-compatible provider correctly raises capability errors")
        finally:
            # Clean up the temporary file
            if os.path.exists(test_file_path):
                os.unlink(test_file_path)
