"""Unit tests for Files API functionality."""

import asyncio
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime

import pytest

from ai_utilities import AiClient, AsyncAiClient, UploadedFile
from ai_utilities.providers.base_provider import BaseProvider
from ai_utilities.providers.provider_exceptions import FileTransferError, ProviderCapabilityError
from ai_utilities.providers.openai_compatible_provider import OpenAICompatibleProvider


class FakeProvider(BaseProvider):
    """Fake provider for testing file operations."""
    
    def __init__(self, should_fail_upload=False, should_fail_download=False, fake_file_id="file-123"):
        self.should_fail_upload = should_fail_upload
        self.should_fail_download = should_fail_download
        self.fake_file_id = fake_file_id
        self.uploaded_files = []
    
    def ask(self, prompt, *, return_format="text", **kwargs):
        return "Fake response"
    
    def ask_many(self, prompts, *, return_format="text", **kwargs):
        return ["Fake response"] * len(prompts)
    
    def upload_file(self, path, *, purpose="assistants", filename=None, mime_type=None):
        """Fake upload implementation."""
        if self.should_fail_upload:
            raise FileTransferError("upload", "fake", Exception("Upload failed"))
        
        # Create fake uploaded file
        fake_file = UploadedFile(
            file_id=self.fake_file_id,
            filename=filename or path.name,
            bytes=path.stat().st_size,
            provider="fake",
            purpose=purpose,
            created_at=datetime.now()
        )
        
        self.uploaded_files.append(fake_file)
        return fake_file
    
    def download_file(self, file_id):
        """Fake download implementation."""
        if self.should_fail_download:
            raise FileTransferError("download", "fake", Exception("Download failed"))
        
        if file_id == self.fake_file_id:
            return b"Fake file content"
        raise ValueError(f"Unknown file_id: {file_id}")


class FakeAsyncProvider:
    """Fake async provider for testing AsyncAiClient."""
    
    def __init__(self, should_fail_upload=False, should_fail_download=False, fake_file_id="file-123"):
        self.should_fail_upload = should_fail_upload
        self.should_fail_download = should_fail_download
        self.fake_file_id = fake_file_id
        self.uploaded_files = []
    
    async def ask(self, prompt, *, return_format="text", **kwargs):
        return "Fake response"
    
    async def ask_many(self, prompts, *, return_format="text", **kwargs):
        return ["Fake response"] * len(prompts)
    
    async def upload_file(self, path, *, purpose="assistants", filename=None, mime_type=None):
        """Fake async upload implementation."""
        if self.should_fail_upload:
            raise FileTransferError("upload", "fake", Exception("Upload failed"))
        
        # Create fake uploaded file
        fake_file = UploadedFile(
            file_id=self.fake_file_id,
            filename=filename or path.name,
            bytes=path.stat().st_size,
            provider="fake",
            purpose=purpose,
            created_at=datetime.now()
        )
        
        self.uploaded_files.append(fake_file)
        return fake_file
    
    async def download_file(self, file_id):
        """Fake async download implementation."""
        if self.should_fail_download:
            raise FileTransferError("download", "fake", Exception("Download failed"))
        
        if file_id == self.fake_file_id:
            return b"Fake file content"
        raise ValueError(f"Unknown file_id: {file_id}")


@pytest.fixture
def mock_env_vars():
    """Mock environment variables to bypass interactive setup."""
    with patch.dict(os.environ, {
        'AI_API_KEY': 'test-key',
        'AI_PROVIDER': 'openai',
        'AI_MODEL': 'test-model-1'
    }):
        yield


class TestFileUpload:
    """Test file upload functionality."""
    
    def test_upload_file_success(self, mock_env_vars):
        """Test successful file upload."""
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("Test content")
            temp_path = Path(f.name)
        
        try:
            # Setup client with fake provider
            provider = FakeProvider()
            client = AiClient(provider=provider)
            
            # Upload file
            result = client.upload_file(temp_path, purpose="assistants")
            
            # Verify result
            assert isinstance(result, UploadedFile)
            assert result.file_id == "file-123"
            assert result.filename == temp_path.name
            assert result.provider == "fake"
            assert result.purpose == "assistants"
            assert result.bytes > 0
            
            # Verify provider was called
            assert len(provider.uploaded_files) == 1
            
        finally:
            # Cleanup
            temp_path.unlink()
    
    def test_upload_file_with_custom_filename(self, mock_env_vars):
        """Test file upload with custom filename."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("Test content")
            temp_path = Path(f.name)
        
        try:
            provider = FakeProvider()
            client = AiClient(provider=provider)
            
            # Upload with custom filename
            result = client.upload_file(temp_path, filename="custom.txt")
            
            assert result.filename == "custom.txt"
            
        finally:
            temp_path.unlink()
    
    def test_upload_file_nonexistent(self, mock_env_vars):
        """Test upload with nonexistent file."""
        provider = FakeProvider()
        client = AiClient(provider=provider)
        
        # Should raise ValueError for nonexistent file
        with pytest.raises(ValueError, match="File does not exist"):
            client.upload_file(Path("nonexistent.txt"))
    
    def test_upload_file_directory(self, mock_env_vars):
        """Test upload with directory path."""
        provider = FakeProvider()
        client = AiClient(provider=provider)
        
        # Should raise ValueError for directory
        with pytest.raises(ValueError, match="Path is not a file"):
            client.upload_file(Path("/tmp"))  # Assuming /tmp exists and is a directory
    
    def test_upload_file_path_string(self, mock_env_vars):
        """Test upload with path string instead of Path object."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("Test content")
            temp_path = Path(f.name)
        
        try:
            provider = FakeProvider()
            client = AiClient(provider=provider)
            
            # Upload with string path
            result = client.upload_file(str(temp_path))
            
            assert isinstance(result, UploadedFile)
            assert result.filename == temp_path.name
            
        finally:
            temp_path.unlink()
    
    def test_upload_file_provider_error(self, mock_env_vars):
        """Test upload when provider raises error."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("Test content")
            temp_path = Path(f.name)
        
        try:
            provider = FakeProvider(should_fail_upload=True)
            client = AiClient(provider=provider)
            
            # Should raise FileTransferError
            with pytest.raises(FileTransferError, match="upload failed"):
                client.upload_file(temp_path)
                
        finally:
            temp_path.unlink()
    
    def test_upload_file_capability_error(self, mock_env_vars):
        """Test upload with provider that doesn't support files."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("Test content")
            temp_path = Path(f.name)
        
        try:
            provider = OpenAICompatibleProvider(base_url="http://localhost:1234/v1")
            client = AiClient(provider=provider)
            
            # Should raise ProviderCapabilityError
            with pytest.raises(ProviderCapabilityError, match="Files API"):
                client.upload_file(temp_path)
                
        finally:
            temp_path.unlink()


class TestFileDownload:
    """Test file download functionality."""
    
    def test_download_file_success(self, mock_env_vars):
        """Test successful file download."""
        provider = FakeProvider()
        client = AiClient(provider=provider)
        
        # Download file as bytes
        content = client.download_file("file-123")
        
        assert content == b"Fake file content"
        assert isinstance(content, bytes)
    
    def test_download_file_to_path(self, mock_env_vars):
        """Test download file to specific path."""
        provider = FakeProvider()
        client = AiClient(provider=provider)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "downloaded.txt"
            
            # Download to file
            result_path = client.download_file("file-123", to_path=output_path)
            
            # Verify file was created
            assert result_path == output_path
            assert output_path.exists()
            
            # Verify content
            with open(output_path, "rb") as f:
                content = f.read()
            assert content == b"Fake file content"
    
    def test_download_file_to_path_string(self, mock_env_vars):
        """Test download file to path string."""
        provider = FakeProvider()
        client = AiClient(provider=provider)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "downloaded.txt"
            
            # Download to string path
            result_path = client.download_file("file-123", to_path=str(output_path))
            
            assert result_path == output_path
            assert output_path.exists()
    
    def test_download_file_creates_directories(self, mock_env_vars):
        """Test download creates parent directories."""
        provider = FakeProvider()
        client = AiClient(provider=provider)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create nested path that doesn't exist
            output_path = Path(temp_dir) / "nested" / "dir" / "file.txt"
            
            # Download should create directories
            result_path = client.download_file("file-123", to_path=output_path)
            
            assert result_path == output_path
            assert output_path.exists()
            assert output_path.parent.exists()
    
    def test_download_file_empty_id(self, mock_env_vars):
        """Test download with empty file_id."""
        provider = FakeProvider()
        client = AiClient(provider=provider)
        
        # Should raise ValueError for empty file_id
        with pytest.raises(ValueError, match="file_id cannot be empty"):
            client.download_file("")
        
        with pytest.raises(ValueError, match="file_id cannot be empty"):
            client.download_file(None)
    
    def test_download_file_provider_error(self, mock_env_vars):
        """Test download when provider raises error."""
        provider = FakeProvider(should_fail_download=True)
        client = AiClient(provider=provider)
        
        # Should raise FileTransferError
        with pytest.raises(FileTransferError, match="download failed"):
            client.download_file("file-123")
    
    def test_download_file_capability_error(self, mock_env_vars):
        """Test download with provider that doesn't support files."""
        provider = OpenAICompatibleProvider(base_url="http://localhost:1234/v1")
        client = AiClient(provider=provider)
        
        # Should raise ProviderCapabilityError
        with pytest.raises(ProviderCapabilityError, match="Files API"):
            client.download_file("file-123")
    
    def test_download_file_unknown_id(self, mock_env_vars):
        """Test download with unknown file_id."""
        provider = FakeProvider()
        client = AiClient(provider=provider)
        
        # Should raise ValueError from provider
        with pytest.raises(ValueError, match="Unknown file_id"):
            client.download_file("unknown-file-id")


class TestAsyncFileOperations:
    """Test async file operations."""
    
    @pytest.mark.asyncio
    async def test_async_upload_file_success(self):
        """Test successful async file upload."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("Test content")
            temp_path = Path(f.name)
        
        try:
            provider = FakeAsyncProvider()
            client = AsyncAiClient(provider=provider)
            
            # Upload file asynchronously
            result = await client.upload_file(temp_path, purpose="assistants")
            
            # Verify result
            assert isinstance(result, UploadedFile)
            assert result.file_id == "file-123"
            assert result.purpose == "assistants"
            
        finally:
            temp_path.unlink()
    
    @pytest.mark.asyncio
    async def test_async_download_file_success(self):
        """Test successful async file download."""
        provider = FakeAsyncProvider()
        client = AsyncAiClient(provider=provider)
        
        # Download file asynchronously
        content = await client.download_file("file-123")
        
        assert content == b"Fake file content"
        assert isinstance(content, bytes)
    
    @pytest.mark.asyncio
    async def test_async_download_file_to_path(self):
        """Test async download file to specific path."""
        provider = FakeAsyncProvider()
        client = AsyncAiClient(provider=provider)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "async_downloaded.txt"
            
            # Download to file asynchronously
            result_path = await client.download_file("file-123", to_path=output_path)
            
            assert result_path == output_path
            assert output_path.exists()
            
            # Verify content
            with open(output_path, "rb") as f:
                content = f.read()
            assert content == b"Fake file content"
    
    @pytest.mark.asyncio
    async def test_async_upload_file_validation(self):
        """Test async upload validation."""
        provider = FakeAsyncProvider()
        client = AsyncAiClient(provider=provider)
        
        # Should raise ValueError for nonexistent file
        with pytest.raises(ValueError, match="File does not exist"):
            await client.upload_file(Path("nonexistent.txt"))
    
    @pytest.mark.asyncio
    async def test_async_download_file_validation(self):
        """Test async download validation."""
        provider = FakeAsyncProvider()
        client = AsyncAiClient(provider=provider)
        
        # Should raise ValueError for empty file_id
        with pytest.raises(ValueError, match="file_id cannot be empty"):
            await client.download_file("")
    
    @pytest.mark.asyncio
    async def test_async_capability_errors(self):
        """Test async capability errors."""
        provider = OpenAICompatibleProvider(base_url="http://localhost:1234/v1")
        client = AsyncAiClient(provider=provider)
        
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("Test content")
            temp_path = Path(f.name)
        
        try:
            # Should raise ProviderCapabilityError
            with pytest.raises(ProviderCapabilityError, match="Files API"):
                await client.upload_file(temp_path)
            
            with pytest.raises(ProviderCapabilityError, match="Files API"):
                await client.download_file("file-123")
                
        finally:
            temp_path.unlink()


class TestUploadedFileModel:
    """Test UploadedFile model."""
    
    def test_uploaded_file_creation(self):
        """Test UploadedFile model creation."""
        file = UploadedFile(
            file_id="file-123",
            filename="test.txt",
            bytes=1024,
            provider="openai",
            purpose="assistants"
        )
        
        assert file.file_id == "file-123"
        assert file.filename == "test.txt"
        assert file.bytes == 1024
        assert file.provider == "openai"
        assert file.purpose == "assistants"
        assert file.created_at is None
    
    def test_uploaded_file_with_datetime(self):
        """Test UploadedFile with datetime."""
        now = datetime.now()
        file = UploadedFile(
            file_id="file-123",
            filename="test.txt",
            bytes=1024,
            provider="openai",
            created_at=now
        )
        
        assert file.created_at == now
    
    def test_uploaded_file_string_representation(self):
        """Test UploadedFile string representation."""
        file = UploadedFile(
            file_id="file-123",
            filename="test.txt",
            bytes=1024,
            provider="openai"
        )
        
        str_repr = str(file)
        assert "file-123" in str_repr
        assert "test.txt" in str_repr
        assert "openai" in str_repr
        
        repr_str = repr(file)
        assert "file-123" in repr_str
        assert "test.txt" in repr_str
        assert "1024" in repr_str
