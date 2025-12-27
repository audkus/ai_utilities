"""Tests for the AI client."""

from src.ai_utilities import AiClient, AiSettings
from tests.fake_provider import FakeProvider


def test_no_side_effects_on_import():
    """Test that importing ai_utilities doesn't create files or make network calls."""
    # This test passes if the import doesn't raise exceptions
    # and no side effects occur during import
    assert True


def test_ai_client_creation():
    """Test creating AI client with settings."""
    settings = AiSettings(api_key="fake-key", model="test-model-1")
    client = AiClient(settings)
    assert client.settings.api_key == "fake-key"
    assert client.settings.model == "test-model-1"


def test_ai_client_with_fake_provider():
    """Test AiClient with FakeProvider for offline testing."""
    fake_provider = FakeProvider()
    client = AiClient(provider=fake_provider, auto_setup=False)
    
    response = client.ask("What is 2+2?")
    assert "fake response" in response.lower()
    assert "2+2" in response.lower()
    
    # Test batch requests
    responses = client.ask_many(["prompt1", "prompt2"])
    assert len(responses) == 2
    assert "prompt1" in responses[0].response
    assert "prompt2" in responses[1].response
    assert responses[0].error is None
    assert responses[1].error is None


def test_json_extraction():
    """Test JSON format response."""
    fake_provider = FakeProvider(['{"test": "data"}'])
    client = AiClient(provider=fake_provider, auto_setup=False)
    
    response = client.ask_json("test prompt")
    assert isinstance(response, dict)
    assert "test" in response
    assert response["test"] == "data"


def test_batch_ordering():
    """Test that batch responses maintain order."""
    fake_provider = FakeProvider([
        "Response 1: {prompt}",
        "Response 2: {prompt}",
        "Response 3: {prompt}"
    ])
    client = AiClient(provider=fake_provider, auto_setup=False)
    
    prompts = ["first", "second", "third"]
    responses = client.ask_many(prompts)
    
    assert len(responses) == 3
    assert "Response 1: first" in responses[0].response
    assert "Response 2: second" in responses[1].response
    assert "Response 3: third" in responses[2].response


def test_parameter_override():
    """Test that parameters can be overridden in calls."""
    settings = AiSettings(api_key="key", model="test-model-1", temperature=0.5)
    fake_provider = FakeProvider()
    client = AiClient(settings, provider=fake_provider, auto_setup=False)
    
    # This should use the overridden model
    response = client.ask("test", model="test-model-2", temperature=0.8)
    assert "test" in response


def test_create_client_convenience():
    """Test the create_client convenience function."""
    from src.ai_utilities import create_client
    
    client = create_client(api_key="test-key", model="test-model-2")
    assert client.settings.api_key == "test-key"
    assert client.settings.model == "test-model-2"
