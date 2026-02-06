#!/usr/bin/env python3
"""
Simple Text Generation Example

Demonstrates the core AI Utilities workflow with minimal setup.
"""

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

from examples._common import print_header, output_dir, require_env
# === END BOOTSTRAP ===

from ai_utilities import AiClient


def main():
    """Simple example showing the core AI Utilities workflow."""
    
    print_header("🌟 AI Utilities Quickstart")
    
    # Check for required environment variables
    if not require_env(['OPENAI_API_KEY']):
        print("❌ CONFIGURATION REQUIRED - Cannot proceed without API key")
        return 1  # Exit with non-zero code for tests
    
    # Create client with environment-based settings
    # The require_env() check above ensures API key is available
    try:
        client = AiClient()  # Uses environment variables automatically
        print("✅ AI client initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        return 1
    
    # Ask a question with caching (recommended for documentation/examples)
    try:
        result = client.ask(
            "Explain dependency injection in one paragraph",
            cache_namespace="docs"
        )
        
        # Print the result - handle different response formats
        print("AI Response:")
        if hasattr(result, 'text'):
            print(result.text)
            response_text = result.text
        elif isinstance(result, str):
            print(result)
            response_text = result
        else:
            print(f"Response: {result}")
            response_text = str(result)
        
        # You can also access metadata
        if hasattr(result, 'usage') and result.usage:
            print(f"\nTokens used: {result.usage.total_tokens}")
        else:
            print(f"\nTokens used: Unknown")
        
        if hasattr(result, 'model') and result.model:
            print(f"Model: {result.model}")
        else:
            print(f"Model: Default")
        
        # Save response to output directory
        script_output_dir = output_dir(Path(__file__))
        response_file = script_output_dir / "ai_response.txt"
        response_file.write_text(response_text, encoding='utf-8')
        print(f"✅ Response saved to: {response_file}")
        
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return 1
    
    print(f"\n🎉 Example complete!")
    
    # Show output directory
    script_output_dir = output_dir(Path(__file__))
    print(f"\n📁 All outputs saved to: {script_output_dir}")
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    if exit_code != 0:
        print("\n💡 Need help? Check the documentation or run with proper configuration")
    exit(exit_code)
