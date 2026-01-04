#!/usr/bin/env python3
"""
Complete Content Workflow Example

Demonstrates the full ai_utilities capabilities:
1. Upload documents for analysis
2. Generate images based on document content
3. Create comprehensive content packages

This shows how to combine document AI with image generation.
"""

import asyncio
import requests
from pathlib import Path

from ai_utilities import AiClient, AsyncAiClient
from ai_utilities.providers.provider_exceptions import FileTransferError, ProviderCapabilityError


def create_content_from_document():
    """Create images and content based on document analysis."""
    print("=== Content Creation from Document ===")
    
    client = AiClient()
    
    try:
        # Step 1: Upload and analyze document
        print("1. Uploading document for analysis...")
        uploaded_file = client.upload_file("sample_report.pdf", purpose="assistants")
        print(f"✅ Document uploaded: {uploaded_file.file_id}")
        
        # Step 2: Extract key concepts for image generation
        print("2. Extracting key concepts from document...")
        analysis = client.ask(
            f"Based on document {uploaded_file.file_id}, extract the main product concepts, "
            "features, and target audience. Provide a summary that would be good for creating marketing images."
        )
        print("✅ Document analysis complete")
        print(f"Analysis: {analysis[:200]}...")
        
        # Step 3: Generate marketing images based on analysis
        print("3. Generating marketing images...")
        
        # Generate images for different aspects
        image_prompts = [
            "A professional product showcase with modern design",
            "Happy customers using the product in real-world scenarios",
            "Technical diagram showing product features and benefits"
        ]
        
        all_images = []
        for prompt in image_prompts:
            print(f"  Generating: {prompt}")
            images = client.generate_image(
                prompt,
                size="1792x1024",  # Wide format for marketing
                quality="hd",
                n=2  # 2 variations per concept
            )
            all_images.extend(images)
        
        print(f"✅ Generated {len(all_images)} marketing images")
        
        # Step 4: Create marketing copy
        print("4. Creating marketing copy...")
        marketing_copy = client.ask(
            f"Based on document {uploaded_file.file_id} and the analysis, create compelling marketing copy "
            "including a headline, key benefits, and call-to-action. Make it professional and persuasive."
        )
        
        print("✅ Marketing copy created")
        print(f"Headline: {marketing_copy[:100]}...")
        
        return {
            'document_id': uploaded_file.file_id,
            'analysis': analysis,
            'images': all_images,
            'marketing_copy': marketing_copy
        }
        
    except Exception as e:
        print(f"❌ Content creation failed: {e}")
        return None


def create_blog_post_package():
    """Create a complete blog post package with text and images."""
    print("\n=== Blog Post Package Creation ===")
    
    client = AiClient()
    
    try:
        # Step 1: Generate blog post content
        print("1. Generating blog post content...")
        blog_topic = "The Future of Remote Work Technology"
        
        blog_content = client.ask(
            f"Write a comprehensive blog post about '{blog_topic}'. "
            "Include an engaging introduction, 3-4 main sections with detailed points, "
            "and a conclusion. Make it professional and informative (about 800 words)."
        )
        
        print("✅ Blog content generated")
        
        # Step 2: Extract key concepts for illustrations
        print("2. Planning illustrations...")
        illustration_concepts = client.ask(
            f"Based on this blog post about '{blog_topic}', suggest 3 specific illustration concepts "
            "that would enhance the reader's understanding. For each concept, provide a brief description "
            "suitable for image generation. Format as a numbered list."
        )
        
        print("✅ Illustration concepts planned")
        print(f"Concepts: {illustration_concepts}")
        
        # Step 3: Generate illustrations
        print("3. Generating blog illustrations...")
        
        # Parse concepts and generate images
        concepts = [
            "Remote worker in modern home office with multiple screens",
            "Team collaboration across different time zones with video calls",
            "Future technology integration in remote work environments"
        ]
        
        blog_images = []
        for concept in concepts:
            print(f"  Generating illustration: {concept}")
            images = client.generate_image(
                f"Professional blog illustration: {concept}",
                size="1024x1024",
                quality="standard",
                n=1
            )
            blog_images.extend(images)
        
        print(f"✅ Generated {len(blog_images)} blog illustrations")
        
        # Step 4: Create social media snippets
        print("4. Creating social media snippets...")
        social_snippets = client.ask(
            f"Based on the blog post about '{blog_topic}', create 3 different social media posts "
            "(Twitter, LinkedIn, Facebook) with appropriate length and tone for each platform."
        )
        
        print("✅ Social media snippets created")
        
        return {
            'topic': blog_topic,
            'content': blog_content,
            'illustration_concepts': illustration_concepts,
            'images': blog_images,
            'social_snippets': social_snippets
        }
        
    except Exception as e:
        print(f"❌ Blog post package creation failed: {e}")
        return None


async def create_product_launch_content():
    """Create comprehensive product launch content asynchronously."""
    print("\n=== Async Product Launch Content ===")
    
    client = AsyncAiClient()
    
    try:
        # Step 1: Generate product descriptions
        print("1. Generating product descriptions...")
        
        description_tasks = [
            client.ask("Write a compelling product description for a new smart home device"),
            client.ask("Create technical specifications for a smart home automation system"),
            client.ask("Write customer benefits and use cases for smart home technology")
        ]
        
        descriptions = await asyncio.gather(*description_tasks)
        
        print("✅ Product descriptions generated")
        
        # Step 2: Generate product images concurrently
        print("2. Generating product images...")
        
        image_tasks = [
            client.generate_image("Modern smart home device in living room setting", size="1024x1024", n=2),
            client.generate_image("Smart phone app interface showing home controls", size="1792x1024", n=2),
            client.generate_image("Family enjoying automated home convenience", size="1024x1024", n=2)
        ]
        
        image_results = await asyncio.gather(*image_tasks)
        all_images = [url for urls in image_results for url in urls]
        
        print(f"✅ Generated {len(all_images)} product images")
        
        # Step 3: Create marketing materials
        print("3. Creating marketing materials...")
        
        marketing_tasks = [
            client.ask("Create an email marketing campaign for smart home device launch"),
            client.ask("Write press release for new smart home technology product"),
            client.ask("Create FAQ section for smart home device customer questions")
        ]
        
        marketing_materials = await asyncio.gather(*marketing_tasks)
        
        print("✅ Marketing materials created")
        
        return {
            'descriptions': descriptions,
            'images': all_images,
            'marketing_materials': marketing_materials
        }
        
    except Exception as e:
        print(f"❌ Product launch content creation failed: {e}")
        return None


def download_content_package(content_package, output_dir="content_package"):
    """Download all content from a content package to local files."""
    print(f"\n=== Downloading Content Package ===")
    
    try:
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Create images directory
        images_dir = output_path / "images"
        images_dir.mkdir(exist_ok=True)
        
        # Download images
        if 'images' in content_package:
            print(f"Downloading {len(content_package['images'])} images...")
            
            for i, image_url in enumerate(content_package['images'], 1):
                try:
                    response = requests.get(image_url)
                    response.raise_for_status()
                    
                    # Save image
                    image_filename = f"image_{i:03d}.png"
                    image_path = images_dir / image_filename
                    
                    with open(image_path, "wb") as f:
                        f.write(response.content)
                    
                    print(f"  ✅ Saved: {image_filename}")
                    
                except Exception as e:
                    print(f"  ❌ Failed to download image {i}: {e}")
        
        # Save text content
        print("Saving text content...")
        
        if 'content' in content_package:
            with open(output_path / "blog_content.txt", "w") as f:
                f.write(content_package['content'])
            print("  ✅ Saved: blog_content.txt")
        
        if 'marketing_copy' in content_package:
            with open(output_path / "marketing_copy.txt", "w") as f:
                f.write(content_package['marketing_copy'])
            print("  ✅ Saved: marketing_copy.txt")
        
        if 'social_snippets' in content_package:
            with open(output_path / "social_snippets.txt", "w") as f:
                f.write(content_package['social_snippets'])
            print("  ✅ Saved: social_snippets.txt")
        
        # Save descriptions
        if 'descriptions' in content_package:
            with open(output_path / "product_descriptions.txt", "w") as f:
                for i, desc in enumerate(content_package['descriptions'], 1):
                    f.write(f"=== Description {i} ===\n")
                    f.write(desc)
                    f.write("\n\n")
            print("  ✅ Saved: product_descriptions.txt")
        
        print(f"✅ Content package saved to: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"❌ Failed to download content package: {e}")
        return None


def main():
    """Run the complete content workflow examples."""
    print("🚀 Complete Content Workflow Demo")
    print("=" * 70)
    print("This demo shows how to combine document analysis with image generation")
    print("to create comprehensive content packages.")
    print()
    
    try:
        # Run workflow examples
        print("Choose a workflow to run:")
        print("1. Document-based content creation")
        print("2. Blog post package creation")
        print("3. Product launch content (async)")
        print("4. Run all workflows")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == "1":
            content = create_content_from_document()
            if content:
                download_content_package(content, "document_content")
        
        elif choice == "2":
            content = create_blog_post_package()
            if content:
                download_content_package(content, "blog_package")
        
        elif choice == "3":
            content = asyncio.run(create_product_launch_content())
            if content:
                download_content_package(content, "product_launch")
        
        elif choice == "4":
            # Run all workflows
            print("\n" + "=" * 70)
            print("Running all workflows...")
            
            # Workflow 1
            content1 = create_content_from_document()
            if content1:
                download_content_package(content1, "document_content")
            
            # Workflow 2
            content2 = create_blog_post_package()
            if content2:
                download_content_package(content2, "blog_package")
            
            # Workflow 3
            content3 = asyncio.run(create_product_launch_content())
            if content3:
                download_content_package(content3, "product_launch")
        
        else:
            print("Invalid choice")
        
        print("\n" + "=" * 70)
        print("✅ Content workflow demo completed!")
        print("\n💡 What you can do with this:")
        print("- Create blog posts with custom illustrations")
        print("- Generate marketing materials from product specs")
        print("- Build comprehensive content packages")
        print("- Combine document analysis with visual content")
        print("- Automate content creation workflows")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
