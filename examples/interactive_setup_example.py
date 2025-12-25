"""Example demonstrating interactive setup for AI utilities."""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_utilities import AiClient, AiSettings


def main():
    """Demonstrate interactive setup functionality."""
    
    print("=== Interactive Setup Example ===\n")
    
    # Example 1: Auto-setup when API key is missing
    print("1. Creating client with auto-setup (will prompt if API key missing):")
    try:
        client = AiClient()  # Will automatically prompt for setup if needed
        response = client.ask("What is 2+2?")
        print(f"✓ Response: {response}\n")
    except Exception as e:
        print(f"✗ Error: {e}\n")
    
    # Example 2: Force reconfiguration
    print("2. Force reconfiguration of settings:")
    try:
        settings = AiSettings.reconfigure()
        client = AiClient(settings, auto_setup=False)
        response = client.ask("What is the capital of France?")
        print(f"✓ Response: {response}\n")
    except Exception as e:
        print(f"✗ Error: {e}\n")
    
    # Example 3: Manual setup without auto-prompt
    print("3. Manual setup without auto-prompt:")
    try:
        # This will fail if API key is not set
        client = AiClient(auto_setup=False)
        response = client.ask("What is AI?")
        print(f"✓ Response: {response}\n")
    except Exception as e:
        print(f"✗ Expected error (no API key): {e}\n")
        print("   Use AiSettings.interactive_setup() to configure first\n")
    
    # Example 4: Check current settings
    print("4. Current settings check:")
    try:
        settings = AiSettings()
        print(f"   Model: {settings.model}")
        print(f"   Temperature: {settings.temperature}")
        print(f"   API Key: {'✓ Set' if settings.api_key else '✗ Missing'}")
        print(f"   Base URL: {settings.base_url or 'Default'}")
        print(f"   Timeout: {settings.timeout}s")
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    main()
