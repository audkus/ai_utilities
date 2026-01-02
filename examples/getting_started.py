"""
🌟 Getting Started with AI Utilities

This is the recommended starting point for new users.
Shows the simplest way to get up and running with AI Utilities.
"""

from ai_utilities import AiClient, AiSettings

def main():
    """Simple example showing the core AI Utilities workflow."""
    
    # Create client with explicit settings (no interactive setup)
    # In production, use environment variables or config files
    settings = AiSettings(
        provider="openai",
        api_key="your-api-key-here",  # Replace with your actual API key
        model="gpt-3.5-turbo"
    )
    
    client = AiClient(settings=settings)
    
    # Ask a question with caching (recommended for documentation/examples)
    try:
        result = client.ask(
            "Explain dependency injection in one paragraph",
            cache_namespace="docs"
        )
        
        # Print the result
        print("AI Response:")
        print(result.text)
        
        # You can also access metadata
        print(f"\nTokens used: {result.usage.total_tokens if result.usage else 'Unknown'}")
        print(f"Model: {result.model if result.model else 'Default'}")
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nTo run this example:")
        print("1. Get an API key from https://platform.openai.com/api-keys")
        print("2. Replace 'your-api-key-here' with your actual key")
        print("3. Or set environment variable: export OPENAI_API_KEY='your-key'")

if __name__ == "__main__":
    main()
