# Files API Documentation

The Files API allows you to upload and download files through AI providers that support file operations, currently OpenAI and OpenAI-compatible providers.

## Overview

- **Supported Providers**: OpenAI (full support), OpenAI-compatible (capability errors)
- **Operations**: Upload files, download files, manage file metadata
- **File Types**: Any file type supported by the provider (PDFs, images, documents, etc.)
- **Purposes**: `assistants`, `fine-tune`, and other provider-specific purposes

## Quick Start

```python
from ai_utilities import AiClient
from pathlib import Path

# Initialize client
client = AiClient()

# Upload a file
file = client.upload_file("document.pdf", purpose="assistants")
print(f"Uploaded: {file.file_id}")

# Download file content
content = client.download_file(file.file_id)

# Download file to disk
path = client.download_file(file.file_id, to_path="downloaded.pdf")
```

## Supported Providers

### OpenAI Provider
- ✅ **File Upload**: Full support with automatic MIME type detection
- ✅ **File Download**: Full support with content retrieval
- ✅ **File Purposes**: `assistants`, `fine-tune`, `vision`, `batch`
- ✅ **File Metadata**: Complete metadata including creation timestamps

### OpenAI-Compatible Providers
- ❌ **File Upload**: Raises `ProviderCapabilityError`
- ❌ **File Download**: Raises `ProviderCapabilityError`
- ✅ **Error Handling**: Clear error messages indicating lack of support

## API Reference

### AiClient Methods

#### `upload_file(path, *, purpose="assistants", filename=None, mime_type=None)`

Upload a file to the AI provider.

**Parameters:**
- `path` (str|Path): Path to the file to upload
- `purpose` (str): Purpose of the upload (default: "assistants")
- `filename` (str|None): Custom filename (default: uses original filename)
- `mime_type` (str|None): MIME type (default: auto-detected)

**Returns:** `UploadedFile` object with file metadata

**Raises:**
- `ValueError`: File doesn't exist or is not a file
- `FileTransferError`: Upload operation failed
- `ProviderCapabilityError`: Provider doesn't support file uploads

**Example:**
```python
# Basic upload
file = client.upload_file("report.pdf")

# Custom purpose and filename
file = client.upload_file(
    "data.csv",
    purpose="fine-tune",
    filename="training-data.csv"
)

# Explicit MIME type
file = client.upload_file(
    "custom-file",
    mime_type="application/json"
)
```

#### `download_file(file_id, *, to_path=None)`

Download file content from the AI provider.

**Parameters:**
- `file_id` (str): ID of the file to download
- `to_path` (str|Path|None): Path to save the file (default: returns bytes)

**Returns:** `bytes` if `to_path` is None, otherwise `Path` to saved file

**Raises:**
- `ValueError`: Invalid file_id
- `FileTransferError`: Download operation failed
- `ProviderCapabilityError`: Provider doesn't support file downloads

**Example:**
```python
# Download as bytes
content = client.download_file("file-123")

# Download to file
path = client.download_file("file-123", to_path="downloaded.pdf")

# Download with directory creation
path = client.download_file("file-123", to_path="downloads/report.pdf")
```

### AsyncAiClient Methods

The async client provides the same interface with `async/await` support:

```python
import asyncio
from ai_utilities import AsyncAiClient

async def main():
    client = AsyncAiClient()
    
    # Upload file asynchronously
    file = await client.upload_file("document.pdf")
    
    # Download file asynchronously
    content = await client.download_file(file.file_id)
    
    # Download to file asynchronously
    path = await client.download_file(file.file_id, to_path="saved.pdf")

asyncio.run(main())
```

## Data Models

### UploadedFile

Represents a file uploaded to an AI provider.

**Fields:**
- `file_id` (str): Unique identifier for the uploaded file
- `filename` (str): Original filename of the uploaded file
- `bytes` (int): Size of the file in bytes
- `provider` (str): Name of the provider that stores the file
- `purpose` (str|None): Purpose of the uploaded file
- `created_at` (datetime|None): When the file was uploaded

**Example:**
```python
file = UploadedFile(
    file_id="file-abc123",
    filename="document.pdf",
    bytes=1024,
    provider="openai",
    purpose="assistants",
    created_at=datetime.now()
)

print(f"File {file.filename} ({file.bytes} bytes) uploaded to {file.provider}")
```

## Error Handling

### Exception Types

#### `FileTransferError`
Raised when file operations fail due to provider issues.

```python
from ai_utilities.providers.provider_exceptions import FileTransferError

try:
    file = client.upload_file("large-file.zip")
except FileTransferError as e:
    print(f"Upload failed: {e}")
    print(f"Operation: {e.operation}")
    print(f"Provider: {e.provider}")
```

#### `ProviderCapabilityError`
Raised when the provider doesn't support the requested operation.

```python
from ai_utilities.providers.provider_exceptions import ProviderCapabilityError

try:
    # This will fail with OpenAI-compatible providers
    file = client.upload_file("test.txt")
except ProviderCapabilityError as e:
    print(f"Capability not supported: {e.capability}")
    print(f"Provider: {e.provider}")
```

#### `ValueError`
Raised for invalid input parameters.

```python
try:
    client.upload_file("nonexistent.txt")
except ValueError as e:
    print(f"Validation error: {e}")
```

## Usage Examples

### Basic File Operations

```python
from ai_utilities import AiClient
from pathlib import Path

client = AiClient()

# Upload multiple files
files = []
for file_path in Path("documents").glob("*.pdf"):
    uploaded_file = client.upload_file(file_path, purpose="assistants")
    files.append(uploaded_file)
    print(f"Uploaded {file_path.name} as {uploaded_file.file_id}")

# Download all files
for file in files:
    content = client.download_file(file.file_id)
    print(f"Downloaded {file.filename}: {len(content)} bytes")
```

### Batch Processing with Async Client

```python
import asyncio
from ai_utilities import AsyncAiClient
from pathlib import Path

async def process_documents():
    client = AsyncAiClient()
    
    # Upload files concurrently
    upload_tasks = []
    for file_path in Path("documents").glob("*.pdf"):
        task = client.upload_file(file_path, purpose="assistants")
        upload_tasks.append(task)
    
    uploaded_files = await asyncio.gather(*upload_tasks)
    
    # Process files concurrently
    download_tasks = []
    for file in uploaded_files:
        task = client.download_file(file.file_id)
        download_tasks.append(task)
    
    contents = await asyncio.gather(*download_tasks)
    
    return uploaded_files, contents

# Run batch processing
files, contents = asyncio.run(process_documents())
print(f"Processed {len(files)} files")
```

### File Management System

```python
from ai_utilities import AiClient
from pathlib import Path
import json

class FileManager:
    def __init__(self, client):
        self.client = client
        self.metadata_file = Path("file_metadata.json")
        self.files = self._load_metadata()
    
    def _load_metadata(self):
        """Load file metadata from disk."""
        if self.metadata_file.exists():
            with open(self.metadata_file) as f:
                return json.load(f)
        return {}
    
    def _save_metadata(self):
        """Save file metadata to disk."""
        with open(self.metadata_file, "w") as f:
            json.dump(self.files, f, indent=2, default=str)
    
    def upload_file(self, path, purpose="assistants", **kwargs):
        """Upload file and track metadata."""
        uploaded_file = self.client.upload_file(path, purpose=purpose, **kwargs)
        
        # Store metadata
        self.files[uploaded_file.file_id] = {
            "filename": uploaded_file.filename,
            "purpose": uploaded_file.purpose,
            "created_at": uploaded_file.created_at.isoformat() if uploaded_file.created_at else None,
            "local_path": str(path)
        }
        self._save_metadata()
        
        return uploaded_file
    
    def download_file(self, file_id, to_path=None):
        """Download file using tracked metadata."""
        if file_id not in self.files:
            raise ValueError(f"Unknown file ID: {file_id}")
        
        metadata = self.files[file_id]
        
        if to_path is None:
            # Use original filename
            to_path = Path("downloads") / metadata["filename"]
        
        return self.client.download_file(file_id, to_path=to_path)
    
    def list_files(self, purpose=None):
        """List uploaded files, optionally filtered by purpose."""
        files = self.files.copy()
        if purpose:
            files = {fid: meta for fid, meta in files.items() if meta.get("purpose") == purpose}
        return files

# Usage
client = AiClient()
manager = FileManager(client)

# Upload and track files
file1 = manager.upload_file("report.pdf", purpose="assistants")
file2 = manager.upload_file("training-data.json", purpose="fine-tune")

# List files by purpose
assistant_files = manager.list_files(purpose="assistants")
print(f"Assistant files: {list(assistant_files.keys())}")

# Download tracked files
content = manager.download_file(file1.file_id)
```

### Error Recovery and Retry Logic

```python
import time
from ai_utilities import AiClient
from ai_utilities.providers.provider_exceptions import FileTransferError

def upload_with_retry(client, path, max_retries=3, delay=1):
    """Upload file with retry logic."""
    for attempt in range(max_retries):
        try:
            return client.upload_file(path)
        except FileTransferError as e:
            if attempt == max_retries - 1:
                raise
            print(f"Upload failed (attempt {attempt + 1}), retrying in {delay}s...")
            time.sleep(delay)
            delay *= 2  # Exponential backoff

# Usage
client = AiClient()
try:
    file = upload_with_retry(client, "important-document.pdf")
    print(f"Successfully uploaded: {file.file_id}")
except FileTransferError as e:
    print(f"Upload failed after retries: {e}")
```

## Best Practices

### 1. File Validation

```python
from pathlib import Path

def validate_file(path):
    """Validate file before upload."""
    path = Path(path)
    
    if not path.exists():
        raise ValueError(f"File does not exist: {path}")
    
    if not path.is_file():
        raise ValueError(f"Path is not a file: {path}")
    
    # Check file size (example: 100MB limit)
    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > 100:
        raise ValueError(f"File too large: {size_mb:.1f}MB (max 100MB)")
    
    return path

# Usage
try:
    validated_path = validate_file("document.pdf")
    file = client.upload_file(validated_path)
except ValueError as e:
    print(f"Validation failed: {e}")
```

### 2. Purpose Selection

```python
def get_purpose_for_file(filename):
    """Determine appropriate purpose based on filename."""
    filename = filename.lower()
    
    if filename.endswith('.json') and 'training' in filename:
        return "fine-tune"
    elif filename.endswith(('.jpg', '.jpeg', '.png', '.gif')):
        return "vision"
    else:
        return "assistants"

# Usage
purpose = get_purpose_for_file("training-data.json")
file = client.upload_file("data.json", purpose=purpose)
```

### 3. Async Error Handling

```python
import asyncio
from ai_utilities import AsyncAiClient
from ai_utilities.providers.provider_exceptions import FileTransferError, ProviderCapabilityError

async def safe_upload(client, path):
    """Upload file with comprehensive error handling."""
    try:
        return await client.upload_file(path)
    except ProviderCapabilityError as e:
        print(f"Provider doesn't support file uploads: {e}")
        return None
    except FileTransferError as e:
        print(f"Upload failed: {e}")
        return None
    except ValueError as e:
        print(f"Invalid file: {e}")
        return None

async def batch_upload(files):
    """Upload multiple files safely."""
    client = AsyncAiClient()
    
    tasks = [safe_upload(client, path) for path in files]
    results = await asyncio.gather(*tasks)
    
    # Filter out failed uploads
    successful = [r for r in results if r is not None]
    print(f"Successfully uploaded {len(successful)}/{len(files)} files")
    
    return successful
```

## Document AI Workflow

The Files API enables powerful document analysis workflows where you can upload documents and ask AI to analyze, summarize, or extract information from them.

### Basic Workflow

```python
from ai_utilities import AiClient

# 1. Upload document
client = AiClient()
uploaded_file = client.upload_file("report.pdf", purpose="assistants")

# 2. Ask AI to analyze the document
summary = client.ask(
    f"Please summarize document {uploaded_file.file_id} and extract key insights."
)

# 3. Ask follow-up questions
recommendations = client.ask(
    f"Based on document {uploaded_file.file_id}, what are your recommendations?"
)
```

### Advanced Document Analysis

```python
# Upload multiple documents for comparative analysis
docs = [
    client.upload_file("q1_report.pdf", purpose="assistants"),
    client.upload_file("q2_report.pdf", purpose="assistants"),
    client.upload_file("q3_report.pdf", purpose="assistants")
]

# Analyze trends across documents
trend_analysis = client.ask(
    f"Compare these quarterly reports: {[d.file_id for d in docs]}. "
    "Identify trends, patterns, and key changes over time."
)

# Extract specific data
financial_metrics = client.ask(
    f"From document {docs[-1].file_id}, extract all financial metrics "
    "and present them in a structured format."
)
```

### Document Templates

```python
# Financial analysis template
def analyze_financial_document(file_id):
    return client.ask(
        f"Analyze financial document {file_id} and provide:\n"
        "1. Revenue and profit metrics\n"
        "2. Expense breakdown\n"
        "3. Cash flow analysis\n"
        "4. Key financial ratios\n"
        "5. Investment recommendations"
    )

# Legal review template
def review_legal_document(file_id):
    return client.ask(
        f"Review legal document {file_id} and identify:\n"
        "1. Key obligations and responsibilities\n"
        "2. Risk factors and liabilities\n"
        "3. Important dates and deadlines\n"
        "4. Compliance requirements"
    )

# Usage
uploaded_file = client.upload_file("contract.pdf", purpose="assistants")
legal_review = review_legal_document(uploaded_file.file_id)
```

### Async Document Processing

```python
import asyncio
from ai_utilities import AsyncAiClient

async def process_documents_concurrently():
    client = AsyncAiClient()
    
    # Upload documents concurrently
    upload_tasks = [
        client.upload_file("doc1.pdf", purpose="assistants"),
        client.upload_file("doc2.pdf", purpose="assistants"),
        client.upload_file("doc3.pdf", purpose="assistants")
    ]
    
    uploaded_files = await asyncio.gather(*upload_tasks)
    
    # Analyze documents concurrently
    analysis_tasks = [
        client.ask(f"Summarize {file.file_id}") for file in uploaded_files
    ]
    
    summaries = await asyncio.gather(*analysis_tasks)
    return summaries

# Run async processing
results = asyncio.run(process_documents_concurrently())
```

### Use Cases

#### **Financial Analysis**
```python
# Upload financial statements
income_statement = client.upload_file("income_statement.pdf", purpose="assistants")
balance_sheet = client.upload_file("balance_sheet.pdf", purpose="assistants")

# Get financial insights
analysis = client.ask(
    f"Analyze the financial health based on {income_statement.file_id} "
    f"and {balance_sheet.file_id}. Provide profitability ratios, "
    "liquidity analysis, and investment recommendations."
)
```

#### **Legal Document Review**
```python
# Upload legal documents
contract = client.upload_file("service_agreement.pdf", purpose="assistants")

# Extract key legal information
legal_summary = client.ask(
    f"From contract {contract.file_id}, extract:\n"
    "- Key obligations\n"
    "- Termination clauses\n"
    "- Liability limitations\n"
    "- Important dates"
)
```

#### **Research Paper Analysis**
```python
# Upload research papers
paper = client.upload_file("research_paper.pdf", purpose="assistants")

# Academic analysis
academic_review = client.ask(
    f"Analyze research paper {paper.file_id} and provide:\n"
    "1. Research methodology\n"
    "2. Key findings\n"
    "3. Limitations\n"
    "4. Future research directions"
)
```

#### **Business Intelligence**
```python
# Upload business reports
market_report = client.upload_file("market_analysis.pdf", purpose="assistants")
competitor_analysis = client.upload_file("competitor_data.pdf", purpose="assistants")

# Strategic insights
strategy_insights = client.ask(
    f"Based on {market_report.file_id} and {competitor_analysis.file_id}, "
    "provide strategic recommendations for market positioning "
    "and competitive advantages."
)
```

---

## Integration Examples

### With Document Processing

```python
from ai_utilities import AiClient
from pathlib import Path

class DocumentProcessor:
    def __init__(self):
        self.client = AiClient()
    
    def process_document(self, file_path):
        """Upload and process a document."""
        # Upload file
        uploaded_file = self.client.upload_file(
            file_path, 
            purpose="assistants"
        )
        
        # Use file in AI conversation
        response = self.client.ask(
            f"Please analyze the document {uploaded_file.file_id} "
            "and provide a summary."
        )
        
        return {
            "file_id": uploaded_file.file_id,
            "summary": response
        }

# Usage
processor = DocumentProcessor()
result = processor.process_document("annual-report.pdf")
print(f"Summary: {result['summary']}")
```

### With Data Analysis

```python
from ai_utilities import AiClient
import pandas as pd
from pathlib import Path

class DataAnalyzer:
    def __init__(self):
        self.client = AiClient()
    
    def analyze_dataset(self, csv_path):
        """Upload CSV dataset and get insights."""
        # Upload data file
        uploaded_file = self.client.upload_file(
            csv_path,
            purpose="assistants"
        )
        
        # Get analysis
        analysis = self.client.ask(
            f"Analyze the dataset in file {uploaded_file.file_id}. "
            "Provide insights about patterns, correlations, and recommendations."
        )
        
        return {
            "file_id": uploaded_file.file_id,
            "analysis": analysis
        }

# Usage
analyzer = DataAnalyzer()
result = analyzer.analyze_dataset("sales-data.csv")
print(f"Analysis: {result['analysis']}")
```

## Troubleshooting

### Common Issues

1. **File Not Found**
   ```
   ValueError: File does not exist: path/to/file.txt
   ```
   - Ensure the file path is correct
   - Use absolute paths or check current working directory

2. **Provider Not Supported**
   ```
   ProviderCapabilityError: Provider 'openai_compatible' does not support capability: Files API (upload)
   ```
   - Use OpenAI provider for file operations
   - OpenAI-compatible providers don't support Files API

3. **Upload Failed**
   ```
   FileTransferError: File upload failed for provider 'openai': [OpenAI error details]
   ```
   - Check file size limits
   - Verify API key has file upload permissions
   - Ensure file format is supported

### Debug Tips

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Test with small file first
test_file = client.upload_file("test.txt")
print(f"Test upload successful: {test_file.file_id}")

# Check provider capabilities
from ai_utilities.providers import ProviderCapabilities
caps = ProviderCapabilities.openai()
print(f"Upload supported: {caps.supports_files_upload}")
print(f"Download supported: {caps.supports_files_download}")
```

## Migration Guide

### From Direct OpenAI SDK

```python
# Before (direct OpenAI SDK)
from openai import OpenAI

client = OpenAI(api_key="your-key")
response = client.files.create(
    file=open("document.pdf", "rb"),
    purpose="assistants"
)

# After (ai_utilities)
from ai_utilities import AiClient

client = AiClient()
file = client.upload_file("document.pdf", purpose="assistants")
```

The ai_utilities approach provides:
- ✅ Consistent error handling
- ✅ Provider abstraction
- ✅ Built-in validation
- ✅ Async support
- ✅ Type safety
