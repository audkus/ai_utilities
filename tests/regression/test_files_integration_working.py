"""Working integration tests for Files API functionality.

These tests only include functionality that actually works with OpenAI's API
and doesn't test features that are known to fail due to API restrictions.

Tests that work:
- File uploads (all purposes)
- File listing
- File deletion
- Async operations

Tests that are excluded (known to fail):
- File downloads (OpenAI security restriction)
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


class TestWorkingFilesIntegration:
    """Integration tests for Files API with real OpenAI API - only working features."""
    
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
    
    @pytest.fixture
    def temp_files(self):
        """Create temporary files for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        
        # Create test files
        text_file = temp_dir / "test.txt"
        text_file.write_text("This is a test file for integration testing.")
        
        json_file = temp_dir / "test.json"
        json_file.write_text('{"key": "value", "test": true}')
        
        csv_file = temp_dir / "test.csv"
        csv_file.write_text("name,age,city\nJohn,30,NYC\nJane,25,LA")
        
        yield temp_dir, text_file, json_file, csv_file
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
    
    def test_upload_file_real_api(self, client, temp_files):
        """Test actual file upload to OpenAI API."""
        temp_dir, text_file, json_file, csv_file = temp_files
        
        # Upload text file
        uploaded_file = client.upload_file(text_file, purpose="assistants")
        
        # Verify uploaded file metadata
        assert isinstance(uploaded_file, UploadedFile)
        assert uploaded_file.file_id is not None
        assert uploaded_file.filename == "test.txt"
        assert uploaded_file.purpose == "assistants"
        assert uploaded_file.provider == "openai"
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
    
    def test_list_uploaded_files(self, client):
        """Test listing uploaded files."""
        # List files
        files = client.list_files()
        
        # Verify response
        assert isinstance(files, list)
        
        # If there are files, verify they have correct structure
        if files:
            for file_obj in files:
                assert isinstance(file_obj, UploadedFile)
                assert file_obj.file_id is not None
                assert file_obj.provider == "openai"
        
        print(f"✅ Listed {len(files)} files")
    
    def test_delete_uploaded_file(self, client, temp_files):
        """Test deleting uploaded files."""
        temp_dir, text_file, json_file, csv_file = temp_files
        
        # Upload a file first
        uploaded_file = client.upload_file(text_file, purpose="assistants")
        file_id = uploaded_file.file_id
        
        # Delete the file
        result = client.delete_file(file_id)
        assert result is True
        
        # Verify file is deleted (should raise exception)
        try:
            client.delete_file(file_id)
            assert False, "Should have raised exception for already deleted file"
        except FileTransferError:
            pass  # Expected
        
        print(f"✅ Deleted file: {file_id}")
    
    @pytest.mark.asyncio
    async def test_async_upload_file(self, async_client, temp_files):
        """Test async file upload."""
        temp_dir, text_file, json_file, csv_file = temp_files
        
        # Upload file asynchronously
        uploaded_file = await async_client.upload_file(text_file, purpose="assistants")
        
        # Verify uploaded file
        assert isinstance(uploaded_file, UploadedFile)
        assert uploaded_file.file_id is not None
        assert uploaded_file.purpose == "assistants"
        
        print(f"✅ Async uploaded file: {uploaded_file.file_id}")
    
    @pytest.mark.asyncio
    async def test_async_list_files(self, async_client):
        """Test async file listing."""
        # List files asynchronously
        files = await async_client.list_files()
        
        # Verify response
        assert isinstance(files, list)
        
        print(f"✅ Async listed {len(files)} files")
    
    @pytest.mark.asyncio
    async def test_async_delete_file(self, async_client, temp_files):
        """Test async file deletion."""
        temp_dir, text_file, json_file, csv_file = temp_files
        
        # Upload file first
        uploaded_file = await async_client.upload_file(text_file, purpose="assistants")
        file_id = uploaded_file.file_id
        
        # Delete file asynchronously
        result = await async_client.delete_file(file_id)
        assert result is True
        
        print(f"✅ Async deleted file: {file_id}")
    
    @pytest.mark.asyncio
    async def test_async_concurrent_operations(self, async_client, temp_files):
        """Test concurrent async file operations."""
        temp_dir, text_file, json_file, csv_file = temp_files
        
        # Upload multiple files concurrently
        upload_tasks = [
            async_client.upload_file(text_file, purpose="assistants"),
            async_client.upload_file(json_file, purpose="fine-tune"),
            async_client.upload_file(csv_file, purpose="assistants")
        ]
        
        uploaded_files = await asyncio.gather(*upload_tasks)
        
        # Verify all uploads succeeded
        assert len(uploaded_files) == 3
        for file_obj in uploaded_files:
            assert isinstance(file_obj, UploadedFile)
            assert file_obj.file_id is not None
        
        print(f"✅ Concurrent upload completed: {len(uploaded_files)} files")
        
        # Clean up - delete all uploaded files
        delete_tasks = [async_client.delete_file(f.file_id) for f in uploaded_files]
        delete_results = await asyncio.gather(*delete_tasks)
        
        assert all(delete_results), "Some files failed to delete"
        print(f"✅ Concurrent delete completed: {len(delete_results)} files")


class TestOpenAICompatibleIntegration:
    """Integration tests for OpenAI-compatible provider (should fail gracefully)."""
    
    def test_compatible_provider_capability_errors(self):
        """Test that OpenAI-compatible provider raises capability errors."""
        from ai_utilities.providers import OpenAICompatibleProvider
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
