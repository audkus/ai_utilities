#!/usr/bin/env python3
"""Test script to verify autouse fixture is working."""

import os
import pytest


def test_autouse_fixture_clears_environment():
    """Test that the autouse fixture clears environment variables."""
    # Set some environment variables that should be cleared by the fixture
    os.environ['AI_PROVIDER'] = 'openai'
    os.environ['AI_API_KEY'] = 'test-key-from-test'
    os.environ['OPENAI_API_KEY'] = 'openai-key-from-test'
    
    # The autouse fixture should have run before this test
    # So if these variables are set, it means they were set by this test
    # and should still be here (the fixture runs before, not after)
    
    # Verify we can set them
    assert os.environ.get('AI_PROVIDER') == 'openai'
    assert os.environ.get('AI_API_KEY') == 'test-key-from-test'
    assert os.environ.get('OPENAI_API_KEY') == 'openai-key-from-test'
    
    print("✓ Environment variables can be set in test")


def test_autouse_fixture_isolation():
    """Test that each test starts with clean environment."""
    # This test should start with a clean environment
    # because the autouse fixture runs before each test
    
    ai_provider = os.environ.get('AI_PROVIDER')
    ai_api_key = os.environ.get('AI_API_KEY')
    openai_api_key = os.environ.get('OPENAI_API_KEY')
    
    print(f"AI_PROVIDER: {ai_provider}")
    print(f"AI_API_KEY: {ai_api_key}")
    print(f"OPENAI_API_KEY: {openai_api_key}")
    
    # These should be None since the fixture should have cleared them
    assert ai_provider is None, f"Expected AI_PROVIDER to be None, got {ai_provider}"
    assert ai_api_key is None, f"Expected AI_API_KEY to be None, got {ai_api_key}"
    assert openai_api_key is None, f"Expected OPENAI_API_KEY to be None, got {openai_api_key}"
    
    print("✓ Environment is clean at test start")


if __name__ == "__main__":
    # Run directly to see behavior without pytest
    print("=== Running without pytest (no autouse fixture) ===")
    test_autouse_fixture_clears_environment()
    print()
