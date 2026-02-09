#!/usr/bin/env python3
"""
Simple Image Generation Example

Basic example: Generate an image and download it.
"""

from pathlib import Path
import sys
import os
import requests

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

from examples._common import print_header, output_dir, require_env, safe_write_bytes
# === END BOOTSTRAP ===

from ai_utilities import AiClient


def main():
    """Generate an image and download it."""
    
    print_header("🎨 Image Generation Quickstart")
    
    # Check for required environment variables
    if not require_env(['OPENAI_API_KEY']):
        print("❌ CONFIGURATION REQUIRED - Cannot proceed without API key")
        return 1
    
    # Initialize AI client
    print("\n� Initializing AI client...")
    try:
        client = AiClient()
        print("✅ AI client initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        return 1
    
    # Generate image
    print("\n🎨 Generating image...")
    try:
        # Generate an image
        response = client.generate_image(
            "A cute dog playing fetch",
            size="1024x1024",
            quality="standard",
            n=1
        )
        
        print("✅ Image generated successfully!")
        print(f"   Image URL: {response.data[0].url}")
        
        # Download the image
        print("\n📥 Downloading image...")
        image_response = requests.get(response.data[0].url)
        image_response.raise_for_status()
        
        # Save to output directory
        script_output_dir = output_dir(Path(__file__))
        image_file = script_output_dir / "generated_image.png"
        
        safe_write_bytes(image_file, image_response.content)
        print(f"✅ Image saved to: {image_file}")
        
        # Show image info
        print(f"\n📊 Image Information:")
        print(f"   Size: {len(image_response.content)} bytes")
        print(f"   Dimensions: 1024x1024")
        print(f"   Style: Digital art")
        
    except Exception as e:
        print(f"❌ Image generation failed: {e}")
        return 1
    
    print(f"\n🎉 Image generation complete!")
    
    # Show output directory
    script_output_dir = output_dir(Path(__file__))
    print(f"\n📁 All outputs saved to: {script_output_dir}")
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    if exit_code != 0:
        print("\n💡 Need help? Check the documentation or run with proper configuration")
    exit(exit_code)
