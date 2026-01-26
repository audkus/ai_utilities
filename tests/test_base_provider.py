"""Unit tests for base_provider module."""

from pathlib import Path
from typing import Any, List, Literal, Union, Optional
import pytest

from ai_utilities.providers.base_provider import BaseProvider
from ai_utilities.providers.provider_exceptions import ProviderCapabilityError


class MockProvider(BaseProvider):
    """Mock implementation of BaseProvider for testing."""

    def ask(
        self, prompt: str, *, return_format: Literal["text", "json"] = "text", **kwargs
    ) -> Union[str, dict[str, Any]]:
        """Mock implementation that returns simple responses."""
        if return_format == "text":
            return f"Response to: {prompt}"
        else:
            return {"response": f"Response to: {prompt}", "format": "json"}

    def ask_many(
        self, prompts: List[str], *, return_format: Literal["text", "json"] = "text", **kwargs
    ) -> List[Union[str, dict[str, Any]]]:
        """Mock implementation that returns responses for each prompt."""
        responses = []
        for prompt in prompts:
            if return_format == "text":
                responses.append(f"Response to: {prompt}")
            else:
                responses.append({"response": f"Response to: {prompt}", "format": "json"})
        return responses

    def upload_file(
        self, path: Path, *, purpose: str = "assistants", filename: Optional[str] = None, mime_type: Optional[str] = None
    ) -> Any:
        """Mock implementation that returns a simple file object."""
        from ai_utilities.file_models import UploadedFile
        return UploadedFile(
            file_id="mock-file-id",
            filename=filename or path.name,
            bytes=1024,
            provider="mock",
            purpose=purpose
        )

    def download_file(self, file_id: str) -> bytes:
        """Mock implementation that returns mock file content."""
        return b"mock file content"

    def generate_image(
        self, prompt: str, *, size: Literal["256x256", "512x512", "1024x1024", "1792x1024", "1024x1792"] = "1024x1024", 
        quality: Literal["standard", "hd"] = "standard", n: int = 1
    ) -> List[str]:
        """Mock implementation that returns mock image URLs."""
        return [f"https://example.com/image_{i}.png" for i in range(n)]


class TestBaseProvider:
    """Test cases for BaseProvider abstract class."""

    def test_concrete_implementation_can_be_instantiated(self) -> None:
        """Test that a concrete implementation can be instantiated."""
        provider = MockProvider()
        assert isinstance(provider, BaseProvider)
        assert isinstance(provider, MockProvider)

    def test_ask_text_format(self) -> None:
        """Test ask method with text format."""
        provider = MockProvider()
        response = provider.ask("Hello, world!", return_format="text")
        
        assert isinstance(response, str)
        assert response == "Response to: Hello, world!"

    def test_ask_json_format(self) -> None:
        """Test ask method with JSON format."""
        provider = MockProvider()
        response = provider.ask("Hello, world!", return_format="json")
        
        assert isinstance(response, dict)
        assert response["response"] == "Response to: Hello, world!"
        assert response["format"] == "json"

    def test_ask_with_kwargs(self) -> None:
        """Test ask method with additional kwargs."""
        provider = MockProvider()
        response = provider.ask("Test", return_format="text", temperature=0.5, max_tokens=100)
        
        assert isinstance(response, str)
        assert "Test" in response

    def test_ask_many_text_format(self) -> None:
        """Test ask_many method with text format."""
        provider = MockProvider()
        prompts = ["Question 1", "Question 2", "Question 3"]
        responses = provider.ask_many(prompts, return_format="text")
        
        assert isinstance(responses, list)
        assert len(responses) == 3
        for i, response in enumerate(responses):
            assert isinstance(response, str)
            assert prompts[i] in response

    def test_ask_many_json_format(self) -> None:
        """Test ask_many method with JSON format."""
        provider = MockProvider()
        prompts = ["Question 1", "Question 2"]
        responses = provider.ask_many(prompts, return_format="json")
        
        assert isinstance(responses, list)
        assert len(responses) == 2
        for i, response in enumerate(responses):
            assert isinstance(response, dict)
            assert response["response"] == f"Response to: {prompts[i]}"
            assert response["format"] == "json"

    def test_ask_many_empty_list(self) -> None:
        """Test ask_many method with empty prompt list."""
        provider = MockProvider()
        responses = provider.ask_many([], return_format="text")
        
        assert isinstance(responses, list)
        assert len(responses) == 0

    def test_upload_file_basic(self) -> None:
        """Test upload_file method with basic parameters."""
        provider = MockProvider()
        test_path = Path("/tmp/test.txt")
        
        result = provider.upload_file(test_path)
        
        assert result.file_id == "mock-file-id"
        assert result.filename == "test.txt"
        assert result.bytes == 1024
        assert result.provider == "mock"
        assert result.purpose == "assistants"

    def test_upload_file_with_custom_parameters(self) -> None:
        """Test upload_file method with custom parameters."""
        provider = MockProvider()
        test_path = Path("/tmp/test.pdf")
        
        result = provider.upload_file(
            test_path, 
            purpose="fine-tune", 
            filename="custom.pdf", 
            mime_type="application/pdf"
        )
        
        assert result.file_id == "mock-file-id"
        assert result.filename == "custom.pdf"
        assert result.purpose == "fine-tune"

    def test_download_file(self) -> None:
        """Test download_file method."""
        provider = MockProvider()
        content = provider.download_file("file-123")
        
        assert isinstance(content, bytes)
        assert content == b"mock file content"

    def test_generate_image_default_parameters(self) -> None:
        """Test generate_image method with default parameters."""
        provider = MockProvider()
        images = provider.generate_image("A beautiful landscape")
        
        assert isinstance(images, list)
        assert len(images) == 1
        assert images[0] == "https://example.com/image_0.png"

    def test_generate_image_custom_parameters(self) -> None:
        """Test generate_image method with custom parameters."""
        provider = MockProvider()
        images = provider.generate_image(
            "A cat", 
            size="512x512", 
            quality="hd", 
            n=3
        )
        
        assert isinstance(images, list)
        assert len(images) == 3
        for i, image in enumerate(images):
            assert image == f"https://example.com/image_{i}.png"

    def test_ask_text_convenience_method(self) -> None:
        """Test ask_text convenience method."""
        provider = MockProvider()
        response = provider.ask_text("Hello")
        
        assert isinstance(response, str)
        assert response == "Response to: Hello"

    def test_ask_text_with_kwargs(self) -> None:
        """Test ask_text method with kwargs."""
        provider = MockProvider()
        response = provider.ask_text("Hello", temperature=0.7)
        
        assert isinstance(response, str)
        assert "Hello" in response

    def test_ask_text_with_provider_returning_dict(self) -> None:
        """Test ask_text when provider returns dict despite text format."""
        
        class DictReturningProvider(MockProvider):
            def ask(self, prompt: str, *, return_format: Literal["text", "json"] = "text", **kwargs) -> Union[str, dict[str, Any]]:
                # Always return dict, even for text format
                return {"data": f"Response to: {prompt}"}
        
        provider = DictReturningProvider()
        response = provider.ask_text("Hello")
        
        # Should convert dict to string
        assert isinstance(response, str)
        assert "Response to: Hello" in response

    def test_ask_text_with_provider_returning_str(self) -> None:
        """Test ask_text when provider returns string as expected."""
        
        class StringReturningProvider(MockProvider):
            def ask(self, prompt: str, *, return_format: Literal["text", "json"] = "text", **kwargs) -> Union[str, dict[str, Any]]:
                # Return string for text format
                return f"String response to: {prompt}"
        
        provider = StringReturningProvider()
        response = provider.ask_text("Hello")
        
        assert isinstance(response, str)
        assert response == "String response to: Hello"

    def test_abstract_class_cannot_be_instantiated(self) -> None:
        """Test that BaseProvider cannot be instantiated directly."""
        with pytest.raises(TypeError) as exc_info:
            BaseProvider()  # type: ignore
        
        assert "abstract" in str(exc_info.value).lower()

    def test_implementation_missing_abstract_methods_raises_error(self) -> None:
        """Test that incomplete implementation raises error."""
        
        class IncompleteProvider(BaseProvider):
            def ask(self, prompt: str, *, return_format: Literal["text", "json"] = "text", **kwargs) -> Union[str, dict[str, Any]]:
                return "response"
            # Missing other abstract methods
        
        with pytest.raises(TypeError) as exc_info:
            IncompleteProvider()  # type: ignore
        
        assert "abstract" in str(exc_info.value).lower()

    def test_method_signatures_match_interface(self) -> None:
        """Test that method signatures match the abstract interface."""
        provider = MockProvider()
        
        # Test that all methods exist and are callable
        assert hasattr(provider, 'ask')
        assert hasattr(provider, 'ask_many')
        assert hasattr(provider, 'upload_file')
        assert hasattr(provider, 'download_file')
        assert hasattr(provider, 'generate_image')
        assert hasattr(provider, 'ask_text')
        
        assert callable(provider.ask)
        assert callable(provider.ask_many)
        assert callable(provider.upload_file)
        assert callable(provider.download_file)
        assert callable(provider.generate_image)
        assert callable(provider.ask_text)

    def test_type_hints_are_preserved(self) -> None:
        """Test that type hints are preserved in the implementation."""
        import inspect
        
        # Check that MockProvider methods have proper type hints
        ask_sig = inspect.signature(MockProvider.ask)
        ask_text_sig = inspect.signature(MockProvider.ask_text)
        
        # Check return annotations
        assert ask_sig.return_annotation is not None
        assert ask_text_sig.return_annotation is not None

    def test_inheritance_hierarchy(self) -> None:
        """Test that BaseProvider follows correct inheritance."""
        provider = MockProvider()
        
        # Should be instance of both classes
        assert isinstance(provider, BaseProvider)
        assert isinstance(provider, MockProvider)
        
        # Should be subclass relationship
        assert issubclass(MockProvider, BaseProvider)
        assert issubclass(MockProvider, object)

    def test_provider_interface_contract(self) -> None:
        """Test that the provider interface contract is maintained."""
        provider = MockProvider()
        
        # Test ask contract
        text_response = provider.ask("test", return_format="text")
        json_response = provider.ask("test", return_format="json")
        assert isinstance(text_response, str)
        assert isinstance(json_response, dict)
        
        # Test ask_many contract
        many_responses = provider.ask_many(["test1", "test2"], return_format="text")
        assert isinstance(many_responses, list)
        assert len(many_responses) == 2
        assert all(isinstance(r, str) for r in many_responses)
        
        # Test ask_text contract
        text_only = provider.ask_text("test")
        assert isinstance(text_only, str)
        
        # Test file operations contract
        uploaded = provider.upload_file(Path("test.txt"))
        assert hasattr(uploaded, 'file_id')
        
        downloaded = provider.download_file("test-id")
        assert isinstance(downloaded, bytes)
        
        # Test image generation contract
        images = provider.generate_image("test")
        assert isinstance(images, list)
        assert len(images) >= 1
