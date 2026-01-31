"""Tests for providers/base.py protocols."""

import pytest
from typing import Dict, Any, Union
from unittest.mock import Mock

from ai_utilities.providers.base import SyncProvider, AsyncProvider


class TestSyncProvider:
    """Test SyncProvider protocol."""

    def test_sync_provider_protocol_exists(self) -> None:
        """Test that SyncProvider protocol exists."""
        assert SyncProvider is not None
        assert hasattr(SyncProvider, 'ask')

    def test_sync_provider_ask_method_signature(self) -> None:
        """Test that SyncProvider.ask has correct signature."""
        import inspect
        ask_method = SyncProvider.__dict__.get('ask')
        assert ask_method is not None
        
        # Check the method signature
        sig = inspect.signature(ask_method)
        params = list(sig.parameters.keys())
        
        expected_params = ['self', 'prompt', 'return_format', 'kwargs']
        assert params == expected_params
        
        # Check parameter types
        prompt_param = sig.parameters['prompt']
        return_format_param = sig.parameters['return_format']
        
        assert prompt_param.annotation == str
        assert 'Literal' in str(return_format_param.annotation)
        assert 'text' in str(return_format_param.annotation)
        assert 'json' in str(return_format_param.annotation)

    def test_sync_provider_runtime_checkable(self, isolated_env) -> None:
        """Test that SyncProvider is runtime_checkable."""
        from typing import runtime_checkable
        
        # Should be able to use isinstance with runtime_checkable
        class ConcreteSyncProvider(SyncProvider):
            def ask(self, prompt: str, *, return_format: str = "text", **kwargs) -> Union[str, Dict[str, Any]]:
                return f"Response to: {prompt}"
        
        concrete = ConcreteSyncProvider()
        assert isinstance(concrete, SyncProvider)

    def test_sync_provider_with_mock(self) -> None:
        """Test SyncProvider with a mock implementation."""
        mock_provider = Mock(spec=SyncProvider)
        mock_provider.ask.return_value = "Mock response"
        
        result = mock_provider.ask("Test prompt", return_format="text")
        assert result == "Mock response"
        mock_provider.ask.assert_called_once_with("Test prompt", return_format="text")

    def test_sync_provider_return_types(self) -> None:
        """Test that SyncProvider can return both string and dict."""
        class TestProvider:
            def ask(self, prompt: str, *, return_format: str = "text", **kwargs) -> Union[str, Dict[str, Any]]:
                if return_format == "json":
                    return {"response": f"Response to: {prompt}"}
                return f"Response to: {prompt}"
        
        provider = TestProvider()
        
        # Test text return
        text_result = provider.ask("test", return_format="text")
        assert isinstance(text_result, str)
        assert text_result == "Response to: test"
        
        # Test JSON return
        json_result = provider.ask("test", return_format="json")
        assert isinstance(json_result, dict)
        assert json_result == {"response": "Response to: test"}

    def test_sync_provider_kwargs_handling(self) -> None:
        """Test that SyncProvider handles kwargs correctly."""
        class TestProvider:
            def ask(self, prompt: str, *, return_format: str = "text", **kwargs) -> Union[str, Dict[str, Any]]:
                return f"Response with kwargs: {kwargs}"
        
        provider = TestProvider()
        result = provider.ask("test", return_format="text", temperature=0.5, max_tokens=100)
        assert "temperature" in result
        assert "max_tokens" in result


class TestAsyncProvider:
    """Test AsyncProvider protocol."""

    @pytest.mark.asyncio
    async def test_async_provider_protocol_exists(self) -> None:
        """Test that AsyncProvider protocol exists."""
        assert AsyncProvider is not None
        assert hasattr(AsyncProvider, 'ask')

    def test_async_provider_ask_method_signature(self) -> None:
        """Test that AsyncProvider.ask has correct signature."""
        import inspect
        ask_method = AsyncProvider.__dict__.get('ask')
        assert ask_method is not None
        
        # Check the method signature
        sig = inspect.signature(ask_method)
        params = list(sig.parameters.keys())
        
        expected_params = ['self', 'prompt', 'return_format', 'kwargs']
        assert params == expected_params
        
        # Check parameter types
        prompt_param = sig.parameters['prompt']
        return_format_param = sig.parameters['return_format']
        
        assert prompt_param.annotation == str
        assert 'Literal' in str(return_format_param.annotation)
        assert 'text' in str(return_format_param.annotation)
        assert 'json' in str(return_format_param.annotation)

    def test_async_provider_runtime_checkable(self, isolated_env) -> None:
        """Test that AsyncProvider is runtime_checkable."""
        from typing import runtime_checkable
        
        class ConcreteAsyncProvider(AsyncProvider):
            async def ask(self, prompt: str, *, return_format: str = "text", **kwargs) -> Union[str, Dict[str, Any]]:
                return f"Async response to: {prompt}"
        
        concrete = ConcreteAsyncProvider()
        assert isinstance(concrete, AsyncProvider)

    @pytest.mark.asyncio
    async def test_async_provider_with_mock(self) -> None:
        """Test AsyncProvider with a mock implementation."""
        mock_provider = Mock(spec=AsyncProvider)
        mock_provider.ask.return_value = "Mock async response"
        
        result = await mock_provider.ask("Test prompt", return_format="text")
        assert result == "Mock async response"
        mock_provider.ask.assert_called_once_with("Test prompt", return_format="text")

    @pytest.mark.asyncio
    async def test_async_provider_return_types(self) -> None:
        """Test that AsyncProvider can return both string and dict."""
        class TestAsyncProvider:
            async def ask(self, prompt: str, *, return_format: str = "text", **kwargs) -> Union[str, Dict[str, Any]]:
                if return_format == "json":
                    return {"response": f"Async response to: {prompt}"}
                return f"Async response to: {prompt}"
        
        provider = TestAsyncProvider()
        
        # Test text return
        text_result = await provider.ask("test", return_format="text")
        assert isinstance(text_result, str)
        assert text_result == "Async response to: test"
        
        # Test JSON return
        json_result = await provider.ask("test", return_format="json")
        assert isinstance(json_result, dict)
        assert json_result == {"response": "Async response to: test"}

    @pytest.mark.asyncio
    async def test_async_provider_kwargs_handling(self) -> None:
        """Test that AsyncProvider handles kwargs correctly."""
        class TestAsyncProvider:
            async def ask(self, prompt: str, *, return_format: str = "text", **kwargs) -> Union[str, Dict[str, Any]]:
                return f"Async response with kwargs: {kwargs}"
        
        provider = TestAsyncProvider()
        result = await provider.ask("test", return_format="text", temperature=0.5, max_tokens=100)
        assert "temperature" in result
        assert "max_tokens" in result


class TestProtocolCompatibility:
    """Test protocol compatibility and edge cases."""

    def test_protocols_are_distinct(self) -> None:
        """Test that SyncProvider and AsyncProvider are distinct protocols."""
        assert SyncProvider is not AsyncProvider
        assert SyncProvider.__name__ != AsyncProvider.__name__

    def test_protocol_inheritance(self) -> None:
        """Test protocol inheritance structure."""
        from typing import Protocol
        
        assert issubclass(SyncProvider, Protocol)
        assert issubclass(AsyncProvider, Protocol)

    def test_protocol_docstrings(self) -> None:
        """Test that protocols have proper docstrings."""
        assert SyncProvider.__doc__ is not None
        assert "Protocol for synchronous AI providers" in SyncProvider.__doc__
        
        assert AsyncProvider.__doc__ is not None
        assert "Protocol for asynchronous AI providers" in AsyncProvider.__doc__

    def test_protocol_method_docstrings(self) -> None:
        """Test that protocol methods have proper docstrings."""
        sync_ask = SyncProvider.__dict__.get('ask')
        async_ask = AsyncProvider.__dict__.get('ask')
        
        assert sync_ask.__doc__ is not None
        assert "Ask a synchronous question" in sync_ask.__doc__
        
        assert async_ask.__doc__ is not None
        assert "Ask an asynchronous question" in async_ask.__doc__
