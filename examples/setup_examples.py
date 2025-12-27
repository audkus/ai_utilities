"""Example demonstrating different setup approaches from default to detailed configuration."""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_utilities import AiClient, AiSettings


def main():
    """Demonstrate different setup approaches."""
    
    print("=== Setup Examples: Default to Detailed ===\n")
    
    # Example 1: Default setup (what most users will use)
    print("1. DEFAULT SETUP - What most users should use:")
    print("   Just create AiClient() and it handles everything automatically")
    try:
        client = AiClient()  # Default: auto_setup=True, smart_setup=False
        response = client.ask("What is 2+2?")
        print(f"   ✓ Response: {response}")
        print(f"   ✓ Model used: {client.settings.model}")
        print(f"   ✓ Temperature: {client.settings.temperature}")
        print(f"   ✓ Auto-setup: {client.settings.api_key is not None}")
        print()
    except Exception as e:
        print(f"   ✗ Error: {e}\n")
    
    # Example 2: Smart setup (recommended for developers who want model updates)
    print("2. SMART SETUP - For developers who want automatic model updates:")
    print("   Checks for new OpenAI models every 30 days (configurable)")
    try:
        client = AiClient(smart_setup=True)  # Enables model update checking
        response = client.ask("What is the capital of France?")
        print(f"   ✓ Response: {response}")
        print(f"   ✓ Update check interval: {client.settings.update_check_days} days")
        print("   ✓ Smart setup enabled: True")
        print()
    except Exception as e:
        print(f"   ✗ Error: {e}\n")
    
    # Example 3: Detailed explicit configuration
    print("3. DETAILED SETUP - For production or specific requirements:")
    print("   Explicit configuration with all options specified")
    try:
        settings = AiSettings(
            api_key="your-api-key-here",  # Explicit API key
            model="gpt-3.5-turbo",        # Specific model
            temperature=0.5,               # Lower temperature for more deterministic responses
            max_tokens=500,                # Limit response length
            base_url="https://api.openai.com/v1",  # Custom API URL if needed
            timeout=60,                    # Longer timeout
            update_check_days=7            # Check for updates weekly
        )
        client = AiClient(settings=settings, auto_setup=False, smart_setup=False)
        response = client.ask("Explain quantum computing in one sentence")
        print(f"   ✓ Response: {response}")
        print(f"   ✓ Model: {client.settings.model}")
        print(f"   ✓ Temperature: {client.settings.temperature}")
        print(f"   ✓ Max tokens: {client.settings.max_tokens}")
        print(f"   ✓ Timeout: {client.settings.timeout}s")
        print(f"   ✓ Update check: {client.settings.update_check_days} days")
        print()
    except Exception as e:
        print(f"   ✗ Error: {e}\n")
    
    # Example 4: Environment-based setup (recommended for production)
    print("4. ENVIRONMENT-BASED SETUP - Recommended for production:")
    print("   Set environment variables and let AiClient read them automatically")
    print("   Required env vars: AI_API_KEY")
    print("   Optional env vars: AI_MODEL, AI_TEMPERATURE, AI_UPDATE_CHECK_DAYS, etc.")
    try:
        # This will read from environment variables
        settings = AiSettings()  # Automatically reads from environment
        client = AiClient(settings=settings, auto_setup=False)
        response = client.ask("What is machine learning?")
        print(f"   ✓ Response: {response}")
        print("   ✓ Configuration loaded from environment variables")
        print(f"   ✓ API Key: {'Set' if settings.api_key else 'Missing'}")
        print(f"   ✓ Model: {settings.model}")
        print(f"   ✓ Temperature: {settings.temperature}")
        print(f"   ✓ Update check days: {settings.update_check_days}")
        print()
    except Exception as e:
        print(f"   ✗ Error: {e}\n")
    
    # Example 5: Mixed approach - explicit settings with smart features
    print("5. MIXED APPROACH - Custom settings with smart features:")
    print("   Combine explicit configuration with smart setup benefits")
    try:
        # Custom settings but still want model update checking
        settings = AiSettings(
            model="gpt-4",
            temperature=0.8,
            update_check_days=14  # Check every 2 weeks
        )
        client = AiClient(settings=settings, smart_setup=True)
        response = client.ask("What are the benefits of Python?")
        print(f"   ✓ Response: {response}")
        print(f"   ✓ Custom model: {client.settings.model}")
        print(f"   ✓ Custom temperature: {client.settings.temperature}")
        print(f"   ✓ Smart setup: Enabled with {client.settings.update_check_days}-day interval")
        print()
    except Exception as e:
        print(f"   ✗ Error: {e}\n")
    
    # Example 6: Development vs Production setup comparison
    print("6. DEVELOPMENT vs PRODUCTION SETUP PATTERNS:")
    print("\n   Development Setup:")
    print("   - Use smart_setup=True to stay updated with new models")
    print("   - Use interactive setup for easy configuration")
    print("   - Example: AiClient(smart_setup=True)")
    
    print("\n   Production Setup:")
    print("   - Use environment variables for configuration")
    print("   - Disable auto-setup for predictable behavior")
    print("   - Set longer update intervals or disable entirely")
    print("   - Example: AiClient(auto_setup=False, smart_setup=False)")
    
    print("\n   Testing/CI Setup:")
    print("   - Use FakeProvider for offline testing")
    print("   - Disable all network calls")
    print("   - Example: AiClient(provider=FakeProvider())")
    
    print("\n=== Setup Recommendations ===")
    print("• Beginners: Use AiClient() - it handles everything automatically")
    print("• Developers: Use AiClient(smart_setup=True) - stay updated with new models")
    print("• Production: Use environment variables + AiClient(auto_setup=False)")
    print("• Testing: Use FakeProvider for offline testing")
    print("• Custom needs: Use explicit AiSettings with your specific configuration")

if __name__ == "__main__":
    main()
