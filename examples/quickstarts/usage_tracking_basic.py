"""Example demonstrating optional usage tracking in ai_utilities v1."""

from ai_utilities import AiClient


def main():
    """Demonstrate usage tracking functionality."""
    
    print("=== AI Utilities v1 Usage Tracking Example ===\n")
    
    # Example 1: Client with usage tracking enabled
    print("1. Creating AI client with usage tracking enabled...")
    client = AiClient(track_usage=True)
    
    # Make some requests (using fake provider for demo)
    # Note: For demo purposes, we'll skip the fake provider setup
    # In real usage, you would configure a real provider
    print("Making some test requests...")
    try:
        response1 = client.ask("What is the capital of France?")
        response2 = client.ask("Explain quantum computing in simple terms")
        response3 = client.ask("List 5 benefits of Python")
    except Exception as e:
        print(f"   Note: Demo requires real provider setup. Error: {e}")
        print("   In real usage, configure your API key and provider.")
    
    # Show usage summary
    print("\n2. Usage Summary:")
    client.print_usage_summary()
    
    # Get detailed stats
    stats = client.get_usage_stats()
    if stats:
        print("\n3. Detailed Statistics:")
        print(f"   Today's requests: {stats.requests_today}")
        print(f"   Today's tokens: {stats.tokens_used_today}")
        print(f"   Total requests: {stats.total_requests}")
        print(f"   Total tokens: {stats.total_tokens}")
        print(f"   Last reset: {stats.last_reset}")
    
    # Example 2: Custom usage file location
    print("\n4. Using custom usage file location...")
    custom_file = Path("my_ai_usage.json")
    custom_client = AiClient(track_usage=True, usage_file=custom_file)
    custom_client.provider = FakeProvider()
    
    custom_client.ask("Another test question")
    
    print(f"Usage tracked to: {custom_file}")
    if custom_file.exists():
        print("✓ Custom usage file created successfully")
        # Clean up
        custom_file.unlink()
    
    # Example 3: Client without usage tracking (default)
    print("\n5. Client without usage tracking (default behavior)...")
    default_client = AiClient()
    default_client.provider = FakeProvider()
    
    default_client.ask("This won't be tracked")
    
    print("Usage tracking status:", "Enabled" if default_client.get_usage_stats() else "Disabled")
    
    print("\n=== Example Complete ===")

if __name__ == "__main__":
    main()
