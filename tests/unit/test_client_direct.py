"""Simple test to verify client.py coverage."""

def test_direct_client_import():
    """Test direct import from client.py to verify coverage."""
    from ai_utilities.client import _sanitize_namespace
    
    # This should definitely hit the client.py code
    result = _sanitize_namespace("test@domain.com")
    assert isinstance(result, str)  # Contract: result is string type
    assert len(result) > 0  # Contract: non-empty result
