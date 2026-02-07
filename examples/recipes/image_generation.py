#!/usr/bin/env python3
"""
Image Generation Recipe
Complete example of generating images with AI Utilities.
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_utilities import AiClient, safe_write_bytes

def main():
    print("🎨 Image Generation Recipe")
    print("=" * 50)
    
    # Create client
    client = AiClient()
    
    # Generate a simple image
    print("🎨 Generating image...")
    response = client.generate_image(
        prompt="A cute robot cat sitting on a rainbow",
        model="dall-e-3",
        size="1024x1024"
    )
    
    # Display results
    print(f"📝 Image description: {response.prompt}")
    print(f"🖼️  Model: {response.model}")
    print(f"⏱️  Size: {response.size}")
    print(f"💰 Cost: ${response.cost:.4f}")
    
    # Save the image
    output_dir = Path(__file__).parent / "_output" / Path(__file__).stem
    output_dir.mkdir(parents=True, exist_ok=True)
    
    image_file = output_dir / "generated_image.png"
    safe_write_bytes(image_file, response.image_data)
    
    print(f"💾 Saved to: {image_file}")
    print("✅ Image generation complete!")

if __name__ == "__main__":
    main()
