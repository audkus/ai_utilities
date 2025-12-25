"""Example demonstrating smart setup with configurable model checking."""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_utilities import AiClient, AiSettings


def main():
    """Demonstrate smart setup functionality."""
    
    print("=== Smart Setup Example ===\n")
    
    # Example 1: Basic auto-setup (only if API key missing)
    print("1. Basic auto-setup (only prompts if API key missing):")
    try:
        client = AiClient(auto_setup=True, smart_setup=False)
        response = client.ask("What is 2+2?")
        print(f"✓ Response: {response}\n")
    except Exception as e:
        print(f"✗ Error: {e}\n")
    
    # Example 2: Smart setup with default 30-day interval
    print("2. Smart setup (checks for new models every 30 days):")
    try:
        client = AiClient(auto_setup=False, smart_setup=True)
        response = client.ask("What is the capital of France?")
        print(f"✓ Response: {response}\n")
    except Exception as e:
        print(f"✗ Error: {e}\n")
    
    # Example 3: Smart setup with custom 7-day interval
    print("3. Smart setup with custom 7-day check interval:")
    try:
        settings = AiSettings(update_check_days=7)
        client = AiClient(settings=settings, auto_setup=False, smart_setup=True)
        response = client.ask("What is AI?")
        print(f"✓ Response: {response}\n")
    except Exception as e:
        print(f"✗ Error: {e}\n")
    
    # Example 4: Manual update check with detailed information
    print("4. Manual check for updates with detailed model information:")
    try:
        client = AiClient(auto_setup=False)
        update_info = client.check_for_updates()
        
        if 'error' in update_info:
            print(f"✗ Error: {update_info['error']}")
        else:
            print(f"   Has updates: {update_info['has_updates']}")
            print(f"   Total models: {update_info['total_models']}")
            print(f"   Cached: {update_info.get('cached', False)}")
            
            if update_info['new_models']:
                print(f"   New models: {', '.join(update_info['new_models'])}")
            
            if update_info['current_models']:
                print(f"   Current models (first 5): {', '.join(update_info['current_models'][:5])}")
        print()
    except Exception as e:
        print(f"✗ Error: {e}\n")
    
    # Example 5: Force fresh check (bypass cache)
    print("5. Force fresh check (bypasses cache):")
    try:
        client = AiClient(auto_setup=False)
        update_info = client.check_for_updates(force_check=True)
        print(f"   Fresh check completed: {not update_info.get('cached', True)}")
        print(f"   Total models found: {update_info.get('total_models', 0)}")
        print()
    except Exception as e:
        print(f"✗ Error: {e}\n")
    
    # Example 6: Check cache status and configuration
    print("6. Current configuration and cache status:")
    try:
        client = AiClient(auto_setup=False)
        print(f"   Update check interval: {client.settings.update_check_days} days")
        print(f"   Current model: {client.settings.model}")
        print(f"   Temperature: {client.settings.temperature}")
        
        cache_file = Path.home() / ".ai_utilities_model_cache.json"
        if cache_file.exists():
            import json
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
            print(f"   Last check: {cache_data.get('last_check', 'Never')}")
            print(f"   Has updates: {cache_data.get('has_updates', 'Unknown')}")
            print(f"   Cached models: {cache_data.get('total_models', 'Unknown')}")
        else:
            print("   No cache file exists (no checks performed yet)")
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    main()
