"""Example demonstrating optional usage tracking in ai_utilities v1."""

from pathlib import Path
import sys

# === BOOTSTRAP: Ensure ai_utilities is importable from any location ===
script_path = Path(__file__).resolve()
repo_root = script_path.parent.parent.parent

# Add src directory to sys.path if not already there
src_dir = repo_root / "src"
src_dir_str = str(src_dir)
if src_dir_str not in sys.path:
    sys.path.insert(0, src_dir_str)

# Add repo root to sys.path for examples import
repo_root_str = str(repo_root)
if repo_root_str not in sys.path:
    sys.path.insert(0, repo_root_str)

from examples._common import print_header, output_dir
# === END BOOTSTRAP ===

from ai_utilities import AiClient


def main():
    """Demonstrate usage tracking functionality."""
    
    print_header("📊 AI Utilities Usage Tracking Example")
    
    # Example 1: Client with usage tracking enabled
    print("1. Creating AI client with usage tracking enabled...")
    try:
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
    except Exception as e:
        print(f"   Note: Usage tracking demo requires provider setup. Error: {e}")
        print("   In real usage, configure your API key and provider.")
        # Create a mock client for demonstration
        print("   Creating mock client for demonstration...")
        client = None
    
    # Show usage summary
    print("\n2. Usage Summary:")
    if client:
        client.print_usage_summary()
    else:
        print("   (Usage tracking requires a configured provider)")
    
    # Get detailed stats
    if client:
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
    script_output_dir = output_dir(Path(__file__))
    custom_file = script_output_dir / "my_ai_usage.json"
    
    try:
        custom_client = AiClient(track_usage=True, usage_file=custom_file)
        custom_client.ask("Another test question")
        
        print(f"Usage tracked to: {custom_file}")
        if custom_file.exists():
            print("✓ Custom usage file created successfully")
            # Clean up
            custom_file.unlink()
    except Exception as e:
        print(f"   Note: Custom usage tracking requires provider setup. Error: {e}")
        print("   In real usage, configure your API key and provider.")
    
    # Example 3: Client without usage tracking (default)
    print("\n5. Client without usage tracking (default behavior)...")
    try:
        default_client = AiClient()
        default_client.ask("This won't be tracked")
        
        print("Usage tracking status:", "Enabled" if default_client.get_usage_stats() else "Disabled")
    except Exception as e:
        print(f"   Note: Default client requires provider setup. Error: {e}")
        print("   Usage tracking would be disabled by default without provider.")
    
    print("\n=== Example Complete ===")
    
    # Show output directory
    print(f"\n📁 Outputs saved to: {script_output_dir}")
    return 0


if __name__ == "__main__":
    exit_code = main()
    if exit_code != 0:
        print("\n💡 Need help? Check the documentation")
    exit(exit_code)
