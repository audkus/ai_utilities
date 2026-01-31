#!/usr/bin/env python3
"""
Simple Image Generation Example

Basic example: Generate an image and download it.
"""

import requests

from ai_utilities import AiClient


def check_env_vars(vars):
    missing_vars = []
    for var in vars:
        if var not in os.environ:
            missing_vars.append(var)
    return missing_vars


def main() -> int:
    """Basic image generation example."""
    print("🎨 AI Utilities Image Generation Quickstart")
    print("=" * 50)
    
    # Check for required environment variables
    missing_vars = check_env_vars(['OPENAI_API_KEY'])
    if missing_vars:
        print("❌ Cannot proceed without API key")
        print("💡 Set OPENAI_API_KEY environment variable")
        return 2

    # 1. Initialize AI client
    client = AiClient()

    # 2. Generate an image
    print("Generating image...")
    image_urls = client.generate_image("A cute dog playing fetch")

    # 3. Download the image
    if image_urls:
        image_url = image_urls[0]
        print(f"Image generated: {image_url}")

        # Download and save to current directory for demo purposes
        # In production, use a proper output path
        output_path = "cute_dog.png"
        response = requests.get(image_url)
        with open(output_path, "wb") as f:
            f.write(response.content)

        print(f"✅ Image saved as {output_path}")
    else:
        print("❌ No images generated")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
