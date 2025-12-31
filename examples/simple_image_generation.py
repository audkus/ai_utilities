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
        
        # Download and save
        response = requests.get(image_url)
        with open("cute_dog.png", "wb") as f:
            f.write(response.content)
        
        print("✅ Image saved as cute_dog.png")
    else:
        print("❌ No images generated")

if __name__ == "__main__":
    generate_and_download_image()
