#!/usr/bin/env python3
"""
Simple Image Generation Example

Basic example: Generate an image and download it.
"""

import requests

from ai_utilities import AiClient


def generate_and_download_image():
    """Generate an image and download it."""

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


if __name__ == "__main__":
    generate_and_download_image()
