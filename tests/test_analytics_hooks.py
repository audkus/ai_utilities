"""Tests for analytics hooks functionality."""

import pytest
from unittest.mock import Mock, patch
from ai_utilities import AiSettings, AiClient
from ai_utilities.analytics.events import AiRequestEvent, AiResponseEvent, AiErrorEvent
from ai_utilities.analytics.hooks import NullAnalyticsHook, CompositeAnalyticsHook


class TestAnalyticsHooks:
    """Test analytics hook functionality."""
    
    def test_no_hook_configured_ask_works_normally(self):
        """When no hook configured, ask() works as before and emits nothing."""
        settings = AiSettings(provider="openai", api_key="fake-key")
        client = AiClient(settings)
        
        # Should not raise any errors about missing analytics
        assert client.settings.analytics_hook is None
        assert hasattr(client, 'ask')
    
    def test_null_hook_does_nothing(self):
        """NullAnalyticsHook does nothing when called."""
        hook = NullAnalyticsHook()
        event = Mock()
        
        # Should not raise any errors
        hook.handle(event)
        # No assertions needed - just ensuring no exceptions
    
    def test_composite_hook_fans_out_to_multiple_hooks(self):
        """CompositeAnalyticsHook calls all child hooks."""
        hook1 = Mock()
        hook2 = Mock()
        hook3 = Mock()
        
        composite = CompositeAnalyticsHook([hook1, hook2, hook3])
        event = Mock()
        
        composite.handle(event)
        
        # All hooks should be called
        hook1.handle.assert_called_once_with(event)
        hook2.handle.assert_called_once_with(event)
        hook3.handle.assert_called_once_with(event)
    
    def test_composite_hook_swallows_child_hook_errors(self):
        """CompositeAnalyticsHook continues even if child hooks fail."""
        hook1 = Mock()
        hook2 = Mock(side_effect=Exception("Hook error"))
        hook3 = Mock()
        
        composite = CompositeAnalyticsHook([hook1, hook2, hook3])
        event = Mock()
        
        # Should not raise exception despite hook2 failing
        composite.handle(event)
        
        # Other hooks should still be called
        hook1.handle.assert_called_once_with(event)
        hook2.handle.assert_called_once_with(event)
        hook3.handle.assert_called_once_with(event)
    
    @patch('ai_utilities.providers.openai_provider.OpenAIProvider')
    def test_hook_receives_request_response_events(self, mock_provider_class):
        """When hook configured, emits request+response events in correct order."""
        # Setup mock provider
        mock_provider = Mock()
        mock_provider.ask.return_value = "Test response"
        mock_provider_class.return_value = mock_provider
        
        # Setup analytics hook
        events = []
        def capture_event(event):
            events.append(event)
        
        settings = AiSettings(
            provider="openai", 
            api_key="fake-key",
            analytics_hook=capture_event
        )
        client = AiClient(settings)
        
        # Make a request
        response = client.ask("Test prompt")
        
        # Should receive exactly 2 events
        assert len(events) == 2
        assert isinstance(events[0], AiRequestEvent)
        assert isinstance(events[1], AiResponseEvent)
        
        # Check request event
        request_event = events[0]
        assert request_event.event_type == "request"
        assert request_event.provider == "openai"
        assert request_event.model == "test-model-1"
        assert request_event.success is True
        assert request_event.request_id is not None
        
        # Check response event
        response_event = events[1]
        assert response_event.event_type == "response"
        assert response_event.provider == "openai"
        assert response_event.model == "test-model-1"
        assert response_event.success is True
        assert response_event.request_id == request_event.request_id
        assert response_event.latency_ms is not None
        assert response_event.latency_ms >= 0
        
        # Response should be normal
        assert response == "Test response"
    
    @patch('ai_utilities.providers.openai_provider.OpenAIProvider')
    def test_hook_receives_error_events_on_provider_failure(self, mock_provider_class):
        """When provider raises, emits request+error events and re-raises original exception."""
        # Setup mock provider to raise error
        test_error = Exception("Provider error")
        mock_provider = Mock()
        mock_provider.ask.side_effect = test_error
        mock_provider_class.return_value = mock_provider
        
        # Setup analytics hook
        events = []
        def capture_event(event):
            events.append(event)
        
        settings = AiSettings(
            provider="openai", 
            api_key="fake-key",
            analytics_hook=capture_event
        )
        client = AiClient(settings)
        
        # Should raise original exception
        with pytest.raises(Exception, match="Provider error"):
            client.ask("Test prompt")
        
        # Should receive exactly 2 events
        assert len(events) == 2
        assert isinstance(events[0], AiRequestEvent)
        assert isinstance(events[1], AiErrorEvent)
        
        # Check error event
        error_event = events[1]
        assert error_event.event_type == "error"
        assert error_event.provider == "openai"
        assert error_event.success is False
        assert error_event.request_id == events[0].request_id
        assert error_event.error_type == "Exception"
        assert error_event.error_message == "Provider error"
        assert error_event.latency_ms is not None
    
    @patch('ai_utilities.providers.openai_provider.OpenAIProvider')
    def test_hook_failure_does_not_break_user_code(self, mock_provider_class):
        """When hook itself throws, AiClient still works normally."""
        # Setup mock provider
        mock_provider = Mock()
        mock_provider.ask.return_value = "Test response"
        mock_provider_class.return_value = mock_provider
        
        # Setup analytics hook that fails
        def failing_hook(event):
            raise Exception("Hook error")
        
        settings = AiSettings(
            provider="openai", 
            api_key="fake-key",
            analytics_hook=failing_hook
        )
        client = AiClient(settings)
        
        # Should still work normally despite hook failing
        response = client.ask("Test prompt")
        assert response == "Test response"
    
    @patch('ai_utilities.providers.openai_provider.OpenAIProvider')
    def test_hook_error_on_provider_failure_still_raises_original(self, mock_provider_class):
        """When both hook and provider fail, original provider exception is raised."""
        # Setup mock provider to raise error
        test_error = Exception("Provider error")
        mock_provider = Mock()
        mock_provider.ask.side_effect = test_error
        mock_provider_class.return_value = mock_provider
        
        # Setup analytics hook that also fails
        def failing_hook(event):
            raise Exception("Hook error")
        
        settings = AiSettings(
            provider="openai", 
            api_key="fake-key",
            analytics_hook=failing_hook
        )
        client = AiClient(settings)
        
        # Should raise original provider exception, not hook exception
        with pytest.raises(Exception, match="Provider error"):
            client.ask("Test prompt")
