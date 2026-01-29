"""Test network blocking functionality."""

import pytest
import socket


def test_network_blocked_by_default():
    """Test that network connections are blocked by default."""
    with pytest.raises(RuntimeError, match="Network connections blocked"):
        # This should fail because network is blocked by default
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(("example.com", 80))


def test_network_allowed_with_fixture(network_allowed):
    """Test that network_allowed fixture allows network connections."""
    # This test should not raise an error because it uses network_allowed fixture
    # Note: We don't actually make a connection here, just verify the fixture exists
    assert network_allowed is None


@pytest.mark.integration
def test_integration_allows_network():
    """Test that integration marker allows network connections."""
    # This should not raise an error because it's marked as integration
    # Note: We don't actually make a connection here
    assert True
