#!/usr/bin/env python3
"""
Image Generation Demo

This script demonstrates how to generate images using AI.
Shows both synchronous and asynchronous image generation workflows.
"""

import asyncio
import requests
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

from examples._common import print_header, output_dir, require_env, safe_write_bytes
# === END BOOTSTRAP ===

from ai_utilities import AiClient, AsyncAiClient
from ai_utilities.providers.provider_exceptions import FileTransferError, ProviderCapabilityError


def main():
    """Demonstrate image generation workflows."""
    
    print_header("🎨 Advanced Image Generation Demo")
    
    # Check for required environment variables
    if not require_env(['OPENAI_API_KEY']):
        print("❌ CONFIGURATION REQUIRED - Cannot proceed without API key")
        return 1
    
    # Initialize AI client
    print("\n🔧 Initializing AI client...")
    try:
        client = AiClient()
        print("✅ AI client initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        return 1
    
    # Basic image generation
    print("\n🎯 Basic Image Generation")
    print("-" * 30)
    
    try:
        # Generate a single image
        print("   Generating single image...")
        response = client.generate_image(
            "A majestic mountain landscape at sunset, digital art style",
            size="1024x1024",
            quality="standard",
            n=1
        )
        
        print("✅ Image generated successfully!")
        print(f"   Image URL: {response.data[0].url}")
        
        # Download the image
        print("   Downloading image...")
        image_response = requests.get(response.data[0].url)
        image_response.raise_for_status()
        
        # Save to output directory
        script_output_dir = output_dir(Path(__file__))
        image_file = script_output_dir / "mountain_landscape.png"
        
        safe_write_bytes(image_file, image_response.content)
        print(f"✅ Image saved to: {image_file}")
        
        # Show image info
        print(f"   Size: {len(image_response.content)} bytes")
        
    except Exception as e:
        print(f"❌ Image generation failed: {e}")
        return 1
    
    # Multiple image generation
    print("\n🎯 Multiple Image Generation")
    print("-" * 30)
    
    try:
        # Generate multiple images
        print("   Generating multiple images...")
        response = client.generate_image(
            "A cute robot cat playing with colorful yarn, cartoon style",
            size="512x512",
            quality="standard",
            n=2
        )
        
        print(f"✅ Generated {len(response.data)} images successfully!")
        
        # Download all images
        script_output_dir = output_dir(Path(__file__))
        
        for i, image_data in enumerate(response.data, 1):
            print(f"   Downloading image {i}...")
            image_response = requests.get(image_data.url)
            image_response.raise_for_status()
            
            image_file = script_output_dir / f"robot_cat_{i}.png"
            safe_write_bytes(image_file, image_response.content)
            print(f"✅ Image {i} saved to: {image_file}")
        
    except Exception as e:
        print(f"❌ Multiple image generation failed: {e}")
        return 1
    
    # Show summary
    print(f"\n📊 Generation Summary:")
    script_output_dir = output_dir(Path(__file__))
    
    generated_files = list(script_output_dir.glob("*.png"))
    print(f"   Total images generated: {len(generated_files)}")
    print(f"   Output directory: {script_output_dir}")
    
    for file in generated_files:
        size = file.stat().st_size
        print(f"   - {file.name}: {size} bytes")
    
    print(f"\n🎉 Advanced image generation demo complete!")
    
    # Show output directory
    script_output_dir = output_dir(Path(__file__))
    print(f"\n📁 All outputs saved to: {script_output_dir}")
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    if exit_code != 0:
        print("\n💡 Need help? Check the documentation or run with proper configuration")
    exit(exit_code)
