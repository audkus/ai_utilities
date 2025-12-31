#!/usr/bin/env python3
"""
Image Generation Demo

This script demonstrates how to generate images using AI.
Shows both synchronous and asynchronous image generation workflows.
"""

import asyncio
import requests
from pathlib import Path

from ai_utilities import AiClient, AsyncAiClient
from ai_utilities.providers.provider_exceptions import FileTransferError, ProviderCapabilityError


def basic_image_generation():
    """Basic synchronous image generation."""
    print("=== Basic Image Generation ===")
    
    client = AiClient()
    
    try:
        # Generate a single image
        print("Generating image of a dog...")
        image_urls = client.generate_image("A cute golden retriever playing fetch in a park")
        
        print(f"✅ Generated {len(image_urls)} image(s):")
        for i, url in enumerate(image_urls, 1):
            print(f"  {i}. {url}")
        
        return image_urls[0]  # Return first image URL
        
    except ProviderCapabilityError as e:
        print(f"❌ Provider doesn't support image generation: {e}")
    except Exception as e:
        print(f"❌ Image generation failed: {e}")
        return None


def advanced_image_generation():
    """Advanced image generation with custom parameters."""
    print("\n=== Advanced Image Generation ===")
    
    client = AiClient()
    
    try:
        # Generate multiple high-quality images
        print("Generating high-quality landscape images...")
        image_urls = client.generate_image(
            "A majestic mountain landscape at sunrise with a lake reflection",
            size="1792x1024",  # Wide landscape format
            quality="hd",       # High quality
            n=3                 # Generate 3 images
        )
        
        print(f"✅ Generated {len(image_urls)} HD images:")
        for i, url in enumerate(image_urls, 1):
            print(f"  {i}. {url}")
        
        return image_urls
        
    except Exception as e:
        print(f"❌ Advanced image generation failed: {e}")
        return []


def download_image(image_url: str, save_path: str) -> bool:
    """Download an image from URL to local file."""
    try:
        print(f"Downloading image from {image_url}...")
        
        response = requests.get(image_url)
        response.raise_for_status()
        
        # Save the image
        with open(save_path, "wb") as f:
            f.write(response.content)
        
        print(f"✅ Image saved to: {save_path}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to download image: {e}")
        return False


async def async_image_generation():
    """Asynchronous image generation."""
    print("\n=== Asynchronous Image Generation ===")
    
    client = AsyncAiClient()
    
    try:
        # Generate images concurrently
        print("Generating multiple images concurrently...")
        
        tasks = [
            client.generate_image("A futuristic city skyline at night"),
            client.generate_image("A peaceful garden with butterflies"),
            client.generate_image("A steaming cup of coffee on a wooden table")
        ]
        
        results = await asyncio.gather(*tasks)
        
        print(f"✅ Generated {len(results)} sets of images:")
        for i, urls in enumerate(results, 1):
            print(f"  Set {i}: {len(urls)} image(s)")
            for j, url in enumerate(urls, 1):
                print(f"    {j}. {url}")
        
        return results
        
    except Exception as e:
        print(f"❌ Async image generation failed: {e}")
        return []


def image_gallery_creation():
    """Create a themed image gallery."""
    print("\n=== Image Gallery Creation ===")
    
    client = AiClient()
    
    # Define themes for our gallery
    themes = [
        "A serene beach with palm trees at sunset",
        "A cozy cabin in the woods with a fireplace",
        "A bustling city street with neon lights",
        "A tranquil mountain lake with surrounding peaks"
    ]
    
    gallery = {}
    
    try:
        print("Creating themed image gallery...")
        
        for theme in themes:
            print(f"Generating: {theme}")
            image_urls = client.generate_image(
                theme,
                size="1024x1024",
                quality="standard",
                n=2  # 2 variations per theme
            )
            
            gallery[theme] = image_urls
            print(f"  ✅ Generated {len(image_urls)} images")
        
        print(f"\n📸 Gallery complete with {len(gallery)} themes:")
        for theme, urls in gallery.items():
            print(f"  📂 {theme}: {len(urls)} images")
        
        return gallery
        
    except Exception as e:
        print(f"❌ Gallery creation failed: {e}")
        return {}


def image_variations():
    """Generate variations of the same concept."""
    print("\n=== Image Variations ===")
    
    client = AiClient()
    
    base_concept = "A red sports car"
    variations = [
        f"{base_concept} on a city street",
        f"{base_concept} on a winding mountain road",
        f"{base_concept} in a modern garage",
        f"{base_concept} at sunset on a coastal highway"
    ]
    
    try:
        print("Generating variations of a red sports car...")
        
        all_images = []
        for variation in variations:
            print(f"  Generating: {variation}")
            images = client.generate_image(
                variation,
                size="1024x1024",
                quality="hd",
                n=1
            )
            all_images.extend(images)
        
        print(f"✅ Generated {len(all_images)} variations:")
        for i, url in enumerate(all_images, 1):
            print(f"  {i}. {url}")
        
        return all_images
        
    except Exception as e:
        print(f"❌ Variation generation failed: {e}")
        return []


def error_handling_examples():
    """Demonstrate error handling for image generation."""
    print("\n=== Error Handling Examples ===")
    
    client = AiClient()
    
    # Test 1: Empty prompt
    print("Test 1: Empty prompt")
    try:
        client.generate_image("")
    except ValueError as e:
        print(f"✅ Caught ValueError: {e}")
    
    # Test 2: Invalid number of images
    print("\nTest 2: Invalid number of images")
    try:
        client.generate_image("A test image", n=15)  # Too many images
    except ValueError as e:
        print(f"✅ Caught ValueError: {e}")
    
    # Test 3: OpenAI-compatible provider (should fail)
    print("\nTest 3: OpenAI-compatible provider")
    try:
        from ai_utilities.providers import OpenAICompatibleProvider
        
        compatible_provider = OpenAICompatibleProvider(base_url="http://localhost:1234/v1")
        compatible_client = AiClient(provider=compatible_provider)
        
        compatible_client.generate_image("A test image")
    except ProviderCapabilityError as e:
        print(f"✅ Caught ProviderCapabilityError: {e.capability}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def practical_use_cases():
    """Practical use cases for image generation."""
    print("\n=== Practical Use Cases ===")
    
    client = AiClient()
    
    # Use Case 1: Blog post illustrations
    print("Use Case 1: Blog post illustrations")
    blog_topic = "The benefits of meditation"
    illustration = client.generate_image(
        f"A peaceful person meditating in a zen garden representing {blog_topic}",
        size="1024x1024",
        quality="standard"
    )
    print(f"  📝 Blog illustration: {illustration[0]}")
    
    # Use Case 2: Social media content
    print("\nUse Case 2: Social media content")
    social_media_post = "New product launch"
    social_image = client.generate_image(
        f"Modern product launch event with excited customers representing {social_media_post}",
        size="1792x1024",  # Wide format for social media
        quality="hd"
    )
    print(f"  📱 Social media image: {social_image[0]}")
    
    # Use Case 3: Presentation visuals
    print("\nUse Case 3: Presentation visuals")
    presentation_topic = "Digital transformation"
    presentation_visual = client.generate_image(
        f"Digital transformation concept with technology and people representing {presentation_topic}",
        size="1024x1024",
        quality="standard"
    )
    print(f"  📊 Presentation visual: {presentation_visual[0]}")


def main():
    """Run all image generation examples."""
    print("🎨 Image Generation Demo")
    print("=" * 60)
    print("This demo shows how to generate images using AI.")
    print("Make sure you have an OpenAI API key with DALL-E access.")
    print()
    
    # Check API key
    import os
    if not os.getenv("AI_API_KEY"):
        print("❌ AI_API_KEY environment variable not set!")
        print("Please set your OpenAI API key:")
        print("export AI_API_KEY='your-openai-key'")
        return
    
    try:
        # Run examples
        basic_image_generation()
        advanced_image_generation()
        
        # Download an example image
        print("\n=== Download Example ===")
        image_url = basic_image_generation()
        if image_url:
            download_image(image_url, "generated_dog.png")
        
        # Async example
        asyncio.run(async_image_generation())
        
        # Gallery creation
        image_gallery_creation()
        
        # Variations
        image_variations()
        
        # Error handling
        error_handling_examples()
        
        # Practical use cases
        practical_use_cases()
        
        print("\n" + "=" * 60)
        print("✅ All image generation demos completed!")
        print("\n💡 Tips:")
        print("- Be specific in your prompts for better results")
        print("- Use 'hd' quality for important images")
        print("- Choose appropriate sizes for your use case")
        print("- Generate multiple images to get options")
        print("- Combine with text generation for complete content")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
