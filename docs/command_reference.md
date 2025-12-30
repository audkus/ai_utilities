# Complete Command Reference

This document provides a comprehensive list of all commands and methods available in the ai_utilities library, organized by functionality.

## Table of Contents

- [Core Client Methods](#core-client-methods)
- [Text Generation](#text-generation)
- [Files API - Document Operations](#files-api---document-operations)
- [Image Generation](#image-generation)
- [Async Operations](#async-operations)
- [Provider Management](#provider-management)
- [Configuration](#configuration)
- [Error Handling](#error-handling)
- [Utility Functions](#utility-functions)

---

## Core Client Methods

### Initialize Clients

```python
from ai_utilities import AiClient, AsyncAiClient, create_client

# Synchronous client
client = AiClient()

# Async client  
async_client = AsyncAiClient()

# Quick client creation
client = create_client(
    provider="openai",
    model="gpt-4",
    api_key="your-key"
)

# With custom provider
from ai_utilities.providers import OpenAICompatibleProvider
provider = OpenAICompatibleProvider(base_url="http://localhost:11434/v1")
client = AiClient(provider=provider)
```

---

## Text Generation

### Basic Text Generation

```python
# Simple text response
response = client.ask("What is artificial intelligence?")
print(response)

# JSON response
data = client.ask("List 3 AI models", return_format="json")
print(data)  # Returns dict/list

# With parameters
response = client.ask(
    "Explain quantum computing",
    temperature=0.7,
    max_tokens=500
)
```

### Batch Text Generation

```python
# Multiple prompts
prompts = [
    "What is machine learning?",
    "Explain neural networks",
    "Define deep learning"
]

responses = client.ask_many(prompts)
for i, response in enumerate(responses):
    print(f"Q{i+1}: {prompts[i]}")
    print(f"A{i+1}: {response}\n")

# With JSON format
json_responses = client.ask_many(prompts, return_format="json")
```

### Advanced Text Operations

```python
# Temperature control (creativity)
creative = client.ask("Write a story", temperature=1.0)
precise = client.ask("Define algorithm", temperature=0.1)

# Token limits
short = client.ask("Summarize AI", max_tokens=50)
detailed = client.ask("Explain AI in detail", max_tokens=1000)

# System messages (if supported)
response = client.ask(
    "You are a helpful assistant. Explain photosynthesis.",
    system="You are a biology teacher."
)
```

---

## Files API - Document Operations

### Upload Documents

```python
from pathlib import Path

# Basic upload
uploaded_file = client.upload_file("document.pdf")
print(f"Uploaded: {uploaded_file.file_id}")

# With custom purpose
uploaded_file = client.upload_file(
    "training_data.json",
    purpose="fine-tune"
)

# With custom filename
uploaded_file = client.upload_file(
    Path("./local_file.docx"),
    filename="custom_name.docx"
)

# With MIME type
uploaded_file = client.upload_file(
    "data.csv",
    mime_type="text/csv"
)
```

### Download Documents

```python
# Download as bytes
content = client.download_file("file-abc123")

# Download to file
saved_path = client.download_file(
    "file-abc123",
    to_path="downloaded_document.pdf"
)

# Download with custom path
from pathlib import Path
saved_path = client.download_file(
    "file-abc123",
    to_path=Path("./downloads/report.pdf")
)
```

### Document AI Workflow

```python
# Upload and analyze
doc = client.upload_file("financial_report.pdf", purpose="assistants")

# Ask questions about the document
summary = client.ask(
    f"Summarize document {doc.file_id} and extract key insights."
)

# Follow-up questions
recommendations = client.ask(
    f"Based on document {doc.file_id}, what are your recommendations?"
)

# Extract specific data
metrics = client.ask(
    f"From document {doc.file_id}, extract all financial metrics "
    "and present them in a table format."
)
```

### Multi-Document Analysis

```python
# Upload multiple documents
docs = [
    client.upload_file("q1_report.pdf", purpose="assistants"),
    client.upload_file("q2_report.pdf", purpose="assistants"),
    client.upload_file("q3_report.pdf", purpose="assistants")
]

# Compare documents
comparison = client.ask(
    f"Compare these quarterly reports: {[d.file_id for d in docs]}. "
    "Identify trends, patterns, and key changes over time."
)

# Extract common themes
themes = client.ask(
    f"Analyze themes across documents {[d.file_id for d in docs]} "
    "and identify recurring topics."
)
```

---

## Image Generation

### Basic Image Generation

```python
# Generate single image
image_urls = client.generate_image("A cute dog playing fetch")
print(f"Generated: {image_urls[0]}")

# Generate multiple images
image_urls = client.generate_image(
    "A majestic mountain landscape",
    n=3  # Generate 3 images
)
```

### Advanced Image Generation

```python
# Different sizes
square = client.generate_image("A cat", size="1024x1024")
landscape = client.generate_image("A beach", size="1792x1024")
portrait = client.generate_image("A tall building", size="1024x1792")

# High quality images
hd_images = client.generate_image(
    "A luxury car",
    quality="hd",
    size="1792x1024"
)

# Multiple variations
variations = client.generate_image(
    "A red sports car",
    size="1024x1024",
    quality="hd",
    n=5
)
```

### Image Download

```python
import requests

# Generate and download
image_urls = client.generate_image("A sunset over mountains")
image_url = image_urls[0]

# Download image
response = requests.get(image_url)
with open("sunset.png", "wb") as f:
    f.write(response.content)

print("Image saved as sunset.png")
```

### Content Creation Workflows

```python
# Blog post with illustrations
topic = "The Future of Remote Work"

# Generate content
content = client.ask(f"Write a blog post about {topic}")

# Generate illustrations
illustrations = client.generate_image(
    f"Professional illustration about {topic}",
    size="1792x1024",
    n=3
)

# Complete blog post package
blog_package = {
    'content': content,
    'images': illustrations,
    'topic': topic
}
```

---

## Async Operations

### Async Text Generation

```python
import asyncio
from ai_utilities import AsyncAiClient

async def text_operations():
    client = AsyncAiClient()
    
    # Single request
    response = await client.ask("Explain async programming")
    
    # Multiple requests concurrently
    tasks = [
        client.ask("What is Python?"),
        client.ask("What is JavaScript?"),
        client.ask("What is Rust?")
    ]
    
    responses = await asyncio.gather(*tasks)
    return responses

# Run async operations
results = asyncio.run(text_operations())
```

### Async File Operations

```python
async def file_operations():
    client = AsyncAiClient()
    
    # Upload files concurrently
    upload_tasks = [
        client.upload_file("doc1.pdf", purpose="assistants"),
        client.upload_file("doc2.pdf", purpose="assistants"),
        client.upload_file("doc3.pdf", purpose="assistants")
    ]
    
    uploaded_files = await asyncio.gather(*upload_tasks)
    
    # Analyze documents concurrently
    analysis_tasks = [
        client.ask(f"Summarize {file.file_id}") 
        for file in uploaded_files
    ]
    
    analyses = await asyncio.gather(*analysis_tasks)
    return uploaded_files, analyses

# Run
files, analyses = asyncio.run(file_operations())
```

### Async Image Generation

```python
async def image_operations():
    client = AsyncAiClient()
    
    # Generate images concurrently
    image_tasks = [
        client.generate_image("A cat sleeping"),
        client.generate_image("A dog playing"),
        client.generate_image("A bird flying")
    ]
    
    image_results = await asyncio.gather(*image_tasks)
    
    # Flatten results
    all_images = [url for urls in image_results for url in urls]
    return all_images

# Run
images = asyncio.run(image_operations())
```

### Complete Async Workflow

```python
async def complete_workflow():
    client = AsyncAiClient()
    
    # Step 1: Generate content
    content_task = client.ask("Write about sustainable technology")
    
    # Step 2: Generate images
    image_task = client.generate_image(
        "Sustainable technology concept",
        size="1792x1024",
        n=2
    )
    
    # Step 3: Wait for both
    content, images = await asyncio.gather(content_task, image_task)
    
    return {
        'content': content,
        'images': images
    }

# Run
workflow_result = asyncio.run(complete_workflow())
```

---

## Provider Management

### Check Provider Capabilities

```python
from ai_utilities.providers import ProviderCapabilities

# OpenAI capabilities
openai_caps = ProviderCapabilities.openai()
print(f"OpenAI supports images: {openai_caps.supports_images}")
print(f"OpenAI supports files: {openai_caps.supports_files_upload}")

# OpenAI-compatible capabilities
compatible_caps = ProviderCapabilities.openai_compatible()
print(f"Compatible supports images: {compatible_caps.supports_images}")

# Check current provider capabilities
current_caps = client.provider.capabilities
print(f"Current provider supports files: {current_caps.supports_files_upload}")
```

### Switch Providers

```python
# Use OpenAI provider
from ai_utilities.providers import OpenAIProvider
openai_provider = OpenAIProvider(api_key="your-key")
client = AiClient(provider=openai_provider)

# Use OpenAI-compatible provider
from ai_utilities.providers import OpenAICompatibleProvider
compatible_provider = OpenAICompatibleProvider(
    base_url="http://localhost:11434/v1",
    api_key="dummy-key"
)
client = AiClient(provider=compatible_provider)

# Check provider type
print(f"Provider: {client.provider.__class__.__name__}")
```

### Provider Configuration

```python
# OpenAI with custom settings
openai_provider = OpenAIProvider(
    api_key="your-key",
    model="gpt-4-turbo",
    timeout=60
)

# OpenAI-compatible with custom settings
compatible_provider = OpenAICompatibleProvider(
    base_url="http://localhost:1234/v1",
    api_key="your-key",
    model="llama3.2",
    timeout=30
)
```

---

## Configuration

### Environment Variables

```bash
# Set API key
export AI_API_KEY="your-openai-key"

# Set model
export AI_MODEL="gpt-4"

# Set base URL for OpenAI-compatible
export AI_BASE_URL="http://localhost:11434/v1"

# Set timeout
export AI_TIMEOUT="60"

# Set temperature
export AI_TEMPERATURE="0.7"
```

### Programmatic Configuration

```python
from ai_utilities import AiSettings, AiClient

# Create settings manually
settings = AiSettings(
    api_key="your-key",
    model="gpt-4",
    base_url="http://localhost:11434/v1",
    temperature=0.7,
    timeout=60
)

# Use settings with client
client = AiClient(settings=settings)
```

### Configuration File (.env)

```bash
# .env file
AI_API_KEY=your-openai-key
AI_MODEL=gpt-4
AI_BASE_URL=http://localhost:11434/v1
AI_TEMPERATURE=0.7
AI_TIMEOUT=60
```

---

## Error Handling

### Handle Specific Errors

```python
from ai_utilities.providers.provider_exceptions import (
    FileTransferError,
    ProviderCapabilityError
)

try:
    # File operations
    uploaded_file = client.upload_file("document.pdf")
except FileTransferError as e:
    print(f"File operation failed: {e}")
    print(f"Operation: {e.operation}")
    print(f"Provider: {e.provider}")

try:
    # Provider-specific operations
    images = client.generate_image("A dog")
except ProviderCapabilityError as e:
    print(f"Provider doesn't support: {e.capability}")
    print(f"Provider: {e.provider}")

# General error handling
try:
    response = client.ask("Some prompt")
except Exception as e:
    print(f"General error: {e}")
```

### Validation Errors

```python
try:
    # Empty prompt
    client.ask("")
except ValueError as e:
    print(f"Validation error: {e}")

try:
    # Invalid image count
    client.generate_image("A cat", n=15)  # Max is 10
except ValueError as e:
    print(f"Validation error: {e}")

try:
    # Nonexistent file
    client.upload_file("nonexistent.txt")
except ValueError as e:
    print(f"Validation error: {e}")
```

### Retry Logic

```python
import time

def ask_with_retry(client, prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            return client.ask(prompt)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            print(f"Attempt {attempt + 1} failed, retrying...")
            time.sleep(2 ** attempt)  # Exponential backoff

# Usage
response = ask_with_retry(client, "Complex question")
```

---

## Utility Functions

### Text Processing

```python
# Ask text (always returns string)
text_response = client.ask_text("What is AI?")

# JSON parsing
from ai_utilities import parse_json_from_text

response = client.ask("List 3 AI models as JSON", return_format="text")
data = parse_json_from_text(response)
```

### Usage Tracking

```python
# Enable usage tracking
client = AiClient(track_usage=True)

# Get usage statistics
stats = client.get_usage_stats()
print(f"Total requests: {stats.total_requests}")
print(f"Total tokens: {stats.total_tokens}")

# Print usage summary
client.print_usage_summary()

# Save usage to file
client = AiClient(track_usage=True, usage_file="usage.json")
```

### Progress Indication

```python
# Show progress for long operations
client = AiClient(show_progress=True)

# Disable progress
client = AiClient(show_progress=False)
```

### Model Information

```python
# Get current model
current_model = client.settings.model
print(f"Current model: {current_model}")

# Get provider info
provider_name = client.provider.__class__.__name__
print(f"Provider: {provider_name}")

# Get capabilities
caps = client.provider.capabilities
print(f"Supports images: {caps.supports_images}")
print(f"Supports files: {caps.supports_files_upload}")
```

---

## Complete Examples

### Document Analysis Pipeline

```python
def analyze_document_pipeline(document_path):
    """Complete document analysis workflow."""
    
    # 1. Upload document
    doc = client.upload_file(document_path, purpose="assistants")
    
    # 2. Extract summary
    summary = client.ask(f"Summarize {doc.file_id}")
    
    # 3. Extract key points
    key_points = client.ask(f"Extract key points from {doc.file_id}")
    
    # 4. Generate insights
    insights = client.ask(f"Provide insights from {doc.file_id}")
    
    # 5. Create recommendations
    recommendations = client.ask(f"Recommendations based on {doc.file_id}")
    
    return {
        'document_id': doc.file_id,
        'summary': summary,
        'key_points': key_points,
        'insights': insights,
        'recommendations': recommendations
    }
```

### Content Creation Pipeline

```python
def create_content_package(topic, num_images=3):
    """Create complete content package with text and images."""
    
    # 1. Generate main content
    content = client.ask(f"Write comprehensive article about {topic}")
    
    # 2. Generate social media snippets
    social = client.ask(f"Create social media posts about {topic}")
    
    # 3. Generate images
    image_prompt = f"Professional illustration about {topic}"
    images = client.generate_image(
        image_prompt,
        size="1792x1024",
        quality="hd",
        n=num_images
    )
    
    # 4. Create call-to-action
    cta = client.ask(f"Create compelling call-to-action for {topic}")
    
    return {
        'topic': topic,
        'content': content,
        'social_media': social,
        'images': images,
        'call_to_action': cta
    }
```

### Batch Processing Pipeline

```python
async def batch_process_documents(document_paths):
    """Process multiple documents concurrently."""
    
    client = AsyncAiClient()
    
    # Upload all documents
    upload_tasks = [
        client.upload_file(path, purpose="assistants")
        for path in document_paths
    ]
    
    uploaded_docs = await asyncio.gather(*upload_tasks)
    
    # Analyze all documents
    analysis_tasks = [
        client.ask(f"Analyze {doc.file_id}")
        for doc in uploaded_docs
    ]
    
    analyses = await asyncio.gather(*analysis_tasks)
    
    # Create summary
    all_analyses = "\n\n".join(analyses)
    summary = await client.ask(
        f"Create executive summary from: {all_analyses}"
    )
    
    return {
        'documents': uploaded_docs,
        'analyses': analyses,
        'summary': summary
    }
```

---

## Quick Reference Card

### Essential Commands

```python
# Initialize
client = AiClient()

# Text generation
response = client.ask("Your prompt")
data = client.ask("Your prompt", return_format="json")

# Batch text
responses = client.ask_many(["prompt1", "prompt2"])

# File operations
uploaded = client.upload_file("file.pdf")
content = client.download_file(uploaded.file_id)

# Image generation
images = client.generate_image("A dog playing fetch")

# Async operations
async def main():
    client = AsyncAiClient()
    response = await client.ask("Your prompt")
    images = await client.generate_image("A cat")
```

### Common Parameters

```python
# Text generation parameters
client.ask(
    "prompt",
    temperature=0.7,      # 0.0-2.0, creativity
    max_tokens=1000,      # Response length
    top_p=1.0,           # Nucleus sampling
    frequency_penalty=0,  # -2.0 to 2.0
    presence_penalty=0    # -2.0 to 2.0
)

# Image generation parameters
client.generate_image(
    "prompt",
    size="1024x1024",     # 256x256, 512x512, 1024x1024, 1792x1024, 1024x1792
    quality="standard",    # "standard" or "hd"
    n=1                   # 1-10 images
)

# File upload parameters
client.upload_file(
    "file.pdf",
    purpose="assistants", # "assistants", "fine-tune"
    filename="custom.pdf", # Custom filename
    mime_type="application/pdf"  # MIME type
)
```

---

This comprehensive reference covers all available commands and methods in the ai_utilities library. Use it as a guide for building powerful AI-powered applications!
