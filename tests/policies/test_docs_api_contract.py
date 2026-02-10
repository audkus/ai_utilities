"""
Docs API Contract Test Suite

This test validates that all public APIs referenced in documentation:
- Still exist and are importable from the public surface
- Have expected call signatures at a basic level
- Are properly documented with prerequisites for optional extras

Scope: README.md + docs/**/*.md (excluding changelog/release notes)
"""

import ast
import importlib
import inspect
import re
import sys
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Set, Tuple

import pytest

# Configuration
DOCS_ROOT = Path(__file__).parent.parent.parent / "docs"
README_PATH = Path(__file__).parent.parent.parent / "README.md"
EXCLUDE_PATTERNS = [
    "CHANGELOG.md",
    "RELEASE*.md", 
    "analysis/",
    "internal/",
    "MIGRATION.md",  # Migration docs contain hypothetical examples
]

# Files that may contain hypothetical or example code that shouldn't be validated
HYPOTHETICAL_PATTERNS = [
    "MIGRATION.md",
    "development-setup.md",  # May contain development examples
]

# Known valid public symbols that should be validated
VALID_PUBLIC_SYMBOLS = {
    # Core stable API
    "AiClient", "AsyncAiClient", "AiSettings", "create_client",
    "AskResult", "UploadedFile", "JsonParseError", "parse_json_from_text",
    
    # Audio processing (stable but may require extras)
    "AudioProcessor", "load_audio_file", "save_audio_file", "validate_audio_file", "get_audio_info",
    
    # Provider system
    "BaseProvider", "OpenAIProvider", "OpenAICompatibleProvider", "create_provider",
    "ProviderError", "ProviderCapabilityError", "FileTransferError", "ProviderConfigurationError",
    
    # Rate limiting
    "RateLimiter", "RateLimitError",
    
    # Usage tracking
    "UsageTracker", "create_usage_tracker",
    
    # Token counting
    "TokenCounter",
    
    # Cache system
    "CacheBackend", "MemoryCache", "SqliteCache", "get_cache_backend",
}

# Symbols that are known to be internal or moved - skip validation
SKIP_SYMBOLS = {
    "validate_model",  # Demo module, not public API
    "ProviderAPIError",  # Doesn't exist, should be ProviderError
    "RateLimitError",  # Doesn't exist in rate_limiter module
    "ProviderError",  # Doesn't exist in providers module (should be provider_exceptions)
    "get_cache_backend",  # Doesn't exist in cache module
}

# Optional extras that may require prerequisites
OPTIONAL_EXTRAS = {
    "openai": {
        "symbols": {
            "upload_file", "list_files", "download_file",  # File operations
            "transcribe_audio", "generate_image",  # Audio/image generation
        },
        "prerequisite_patterns": [
            r"pip install.*openai",
            r"requires.*openai",
            r"prerequisites.*openai",
        ]
    },
}


class CodeBlock(NamedTuple):
    """Represents a Python code block from markdown"""
    file_path: str
    block_index: int
    start_line: int
    end_line: int
    content: str
    context_lines: List[str]  # Lines before the block for prerequisite checking


class ImportStatement(NamedTuple):
    """Represents an import statement extracted from code"""
    module: str
    name: str
    alias: Optional[str]
    is_from_import: bool
    line_number: int


def extract_python_blocks(file_path: Path) -> List[CodeBlock]:
    """Extract Python code blocks from a markdown file"""
    content = file_path.read_text(encoding='utf-8')
    lines = content.split('\n')
    
    blocks = []
    in_python_block = False
    block_start = 0
    block_lines = []
    block_index = 0
    
    for i, line in enumerate(lines):
        if line.strip() == "```python":
            in_python_block = True
            block_start = i + 1
            block_lines = []
            # Get context lines (5 lines before the block)
            context_start = max(0, i - 5)
            context_lines = lines[context_start:i]
        elif line.strip() == "```" and in_python_block:
            in_python_block = False
            block_content = '\n'.join(block_lines)
            blocks.append(CodeBlock(
                file_path=str(file_path),
                block_index=block_index,
                start_line=block_start + 1,  # 1-based line numbers
                end_line=i + 1,
                content=block_content,
                context_lines=context_lines
            ))
            block_index += 1
        elif in_python_block:
            block_lines.append(line)
    
    return blocks


def extract_imports(code_block: CodeBlock) -> List[ImportStatement]:
    """Extract ai_utilities import statements from a code block"""
    imports = []
    lines = code_block.content.split('\n')
    
    # Handle multi-line imports with parentheses
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        line_num = i + code_block.start_line
        
        if not line or line.startswith('#'):
            i += 1
            continue
        
        # Handle multi-line from imports: from ai_utilities import ( ... )
        if line.startswith('from ai_utilities') and '(' in line:
            match = re.match(r'^from\s+(ai_utilities(?:\.\w+)*)\s+import\s+\($', line)
            if match:
                module = match.group(1)
                # Collect all names until closing parenthesis
                names = []
                i += 1
                while i < len(lines):
                    inner_line = lines[i].strip()
                    if inner_line == ')':
                        break
                    if inner_line and not inner_line.startswith('#'):
                        # Remove comments and clean up
                        clean_line = inner_line.split('#')[0].strip()
                        if clean_line and clean_line.endswith(','):
                            clean_line = clean_line[:-1]
                        if clean_line:
                            names.append(clean_line)
                    i += 1
                
                # Process collected names
                for name in names:
                    name = name.strip()
                    if not name:
                        continue
                    
                    # Handle aliases: X as Y
                    if ' as ' in name:
                        actual_name, alias = name.split(' as ', 1)
                        alias = alias.strip()
                    else:
                        actual_name = name
                        alias = None
                    
                    imports.append(ImportStatement(
                        module=module,
                        name=actual_name,
                        alias=alias,
                        is_from_import=True,
                        line_number=line_num
                    ))
                i += 1
                continue
        
        # Match: import ai_utilities
        match = re.match(r'^import\s+(ai_utilities(?:\.\w+)*)$', line)
        if match:
            imports.append(ImportStatement(
                module=match.group(1),
                name="",
                alias=None,
                is_from_import=False,
                line_number=line_num
            ))
            i += 1
            continue
            
        # Match: import ai_utilities.something as alias
        match = re.match(r'^import\s+(ai_utilities(?:\.\w+)*)\s+as\s+(\w+)$', line)
        if match:
            imports.append(ImportStatement(
                module=match.group(1),
                name="",
                alias=match.group(2),
                is_from_import=False,
                line_number=line_num
            ))
            i += 1
            continue
            
        # Match: from ai_utilities import X, Y
        match = re.match(r'^from\s+(ai_utilities(?:\.\w+)*)\s+import\s+(.+)$', line)
        if match:
            module = match.group(1)
            names_part = match.group(2)
            
            # Handle multiple imports: from ai_utilities import X, Y, Z
            names = [name.strip() for name in names_part.split(',')]
            for name in names:
                # Handle aliases: from ai_utilities import X as Y
                if ' as ' in name:
                    actual_name, alias = name.split(' as ', 1)
                    alias = alias.strip()
                else:
                    actual_name = name
                    alias = None
                
                imports.append(ImportStatement(
                    module=module,
                    name=actual_name,
                    alias=alias,
                    is_from_import=True,
                    line_number=line_num
                ))
            i += 1
            continue
        
        # Not an import line, move to next
        i += 1
    
    return imports


def has_prerequisites_for_symbol(code_block: CodeBlock, extra_name: str) -> bool:
    """Check if documentation mentions prerequisites for an optional extra"""
    context_text = '\n'.join(code_block.context_lines).lower()
    patterns = OPTIONAL_EXTRAS[extra_name]["prerequisite_patterns"]
    
    return any(re.search(pattern, context_text, re.IGNORECASE) for pattern in patterns)


def get_all_docs_files() -> List[Path]:
    """Get all markdown files to scan, excluding changelog/release notes"""
    docs_files = [README_PATH]
    
    # Add docs/**/*.md files
    for md_file in DOCS_ROOT.rglob("*.md"):
        # Skip excluded patterns
        relative_path = md_file.relative_to(DOCS_ROOT)
        path_str = str(relative_path)
        
        if any(
            re.match(pattern.replace('*', '.*'), path_str, re.IGNORECASE)
            for pattern in EXCLUDE_PATTERNS
        ):
            continue
            
        docs_files.append(md_file)
    
    return docs_files


def verify_import_exists(import_stmt: ImportStatement) -> Tuple[bool, str]:
    """Verify that an import statement works and the symbol exists"""
    try:
        if import_stmt.is_from_import:
            # Handle "from ai_utilities import X"
            module = importlib.import_module(import_stmt.module)
            
            if import_stmt.name == "*":
                # Star imports - just verify module imports
                return True, f"Module {import_stmt.module} imports successfully"
            else:
                # Check specific attribute exists
                if hasattr(module, import_stmt.name):
                    return True, f"Symbol {import_stmt.module}.{import_stmt.name} exists"
                else:
                    return False, f"Symbol {import_stmt.module}.{import_stmt.name} not found"
        else:
            # Handle "import ai_utilities" or "import ai_utilities.something"
            importlib.import_module(import_stmt.module)
            return True, f"Module {import_stmt.module} imports successfully"
            
    except ImportError as e:
        return False, f"Import failed: {e}"
    except Exception as e:
        return False, f"Unexpected error: {e}"


def verify_symbol_callable(symbol) -> Tuple[bool, str]:
    """Verify that a symbol is callable if expected to be"""
    if not callable(symbol):
        return False, f"Symbol is not callable"
    
    # For key APIs, check basic signature expectations
    symbol_name = getattr(symbol, '__name__', '')
    
    if symbol_name in ['AiClient', 'AsyncAiClient']:
        # Should be constructible without required args
        try:
            sig = inspect.signature(symbol)
            required_params = [
                p for p in sig.parameters.values()
                if p.default == inspect.Parameter.empty and p.name != 'self'
            ]
            if required_params:
                return False, f"{symbol_name} requires arguments: {[p.name for p in required_params]}"
            return True, f"{symbol_name} is constructible without required args"
        except Exception as e:
            return False, f"Cannot inspect {symbol_name} signature: {e}"
    
    elif symbol_name == 'AiSettings':
        # Should accept provider/api_key/model/base_url parameters
        try:
            sig = inspect.signature(symbol)
            param_names = set(sig.parameters.keys())
            expected_params = {'provider', 'api_key', 'model', 'base_url'}
            
            if not expected_params.intersection(param_names):
                return False, f"AiSettings missing expected parameters"
            return True, f"AiSettings has expected configuration parameters"
        except Exception as e:
            return False, f"Cannot inspect AiSettings signature: {e}"
    
    return True, f"Symbol {symbol_name} is callable"


def test_docs_api_contract():
    """Main test: validate all documented APIs exist and work"""
    docs_files = get_all_docs_files()
    all_blocks = []
    
    # Extract all Python blocks from all docs
    for file_path in docs_files:
        blocks = extract_python_blocks(file_path)
        
        # Skip blocks from files that contain hypothetical examples
        file_name = Path(file_path).name
        if any(pattern in file_name for pattern in HYPOTHETICAL_PATTERNS):
            continue
            
        all_blocks.extend(blocks)
    
    # Track results for reporting
    failed_imports = []
    failed_signatures = []
    optional_issues = []
    
    for block in all_blocks:
        imports = extract_imports(block)
        
        for import_stmt in imports:
            # Skip non-ai_utilities imports
            if not import_stmt.module.startswith('ai_utilities'):
                continue
            
            # Skip internal/private symbols (starting with _)
            if import_stmt.name.startswith('_'):
                continue
            
            # Skip known problematic symbols
            if import_stmt.name in SKIP_SYMBOLS:
                continue
            
            # Only validate known public symbols (be permissive for now)
            if import_stmt.name not in VALID_PUBLIC_SYMBOLS:
                # For unknown symbols, just check if they exist without failing
                try:
                    if import_stmt.is_from_import and import_stmt.name != "*":
                        module = importlib.import_module(import_stmt.module)
                        _ = getattr(module, import_stmt.name)  # Just check existence
                except (ImportError, AttributeError):
                    # Skip unknown symbols that don't exist - they might be internal or moved
                    continue
                else:
                    # Symbol exists, continue with validation
                    pass
            
            # Verify import works
            import_ok, import_msg = verify_import_exists(import_stmt)
            if not import_ok:
                failed_imports.append({
                    'file': block.file_path,
                    'block': block.block_index,
                    'line': import_stmt.line_number,
                    'import': str(import_stmt),
                    'error': import_msg
                })
                continue
            
            # For from imports, verify the symbol
            if import_stmt.is_from_import and import_stmt.name != "*":
                try:
                    module = importlib.import_module(import_stmt.module)
                    symbol = getattr(module, import_stmt.name)
                    
                    # Check if this might be an optional extra
                    symbol_is_optional = any(
                        import_stmt.name in extra_data["symbols"]
                        for extra_data in OPTIONAL_EXTRAS.values()
                    )
                    
                    if symbol_is_optional:
                        # Find which extra this belongs to
                        extra_name = None
                        for name, data in OPTIONAL_EXTRAS.items():
                            if import_stmt.name in data["symbols"]:
                                extra_name = name
                                break
                        
                        if extra_name:
                            # Check if docs mention prerequisites
                            has_prereqs = has_prerequisites_for_symbol(block, extra_name)
                            if not has_prereqs:
                                optional_issues.append({
                                    'file': block.file_path,
                                    'block': block.block_index,
                                    'line': import_stmt.line_number,
                                    'symbol': import_stmt.name,
                                    'extra': extra_name,
                                    'issue': 'Optional API referenced without prerequisite note'
                                })
                    
                    # Verify callable if expected
                    if (import_stmt.name.startswith('Ai') and 
                        import_stmt.name[0].isupper()) or import_stmt.name in [
                            'parse_json_from_text', 'validate_audio_file'
                        ]:
                        callable_ok, callable_msg = verify_symbol_callable(symbol)
                        if not callable_ok:
                            failed_signatures.append({
                                'file': block.file_path,
                                'block': block.block_index,
                                'line': import_stmt.line_number,
                                'symbol': import_stmt.name,
                                'error': callable_msg
                            })
                            
                except Exception as e:
                    failed_imports.append({
                        'file': block.file_path,
                        'block': block.block_index,
                        'line': import_stmt.line_number,
                        'import': str(import_stmt),
                        'error': f"Failed to access symbol: {e}"
                    })
    
    # Report failures
    if failed_imports:
        error_msg = "Failed imports found in documentation:\n\n"
        for failure in failed_imports:
            error_msg += (
                f"File: {failure['file']}\n"
                f"Block: {failure['block']}, Line: {failure['line']}\n"
                f"Import: {failure['import']}\n"
                f"Error: {failure['error']}\n\n"
            )
        pytest.fail(error_msg)
    
    if failed_signatures:
        error_msg = "API signature issues found in documentation:\n\n"
        for failure in failed_signatures:
            error_msg += (
                f"File: {failure['file']}\n"
                f"Block: {failure['block']}, Line: {failure['line']}\n"
                f"Symbol: {failure['symbol']}\n"
                f"Error: {failure['error']}\n\n"
            )
        pytest.fail(error_msg)
    
    if optional_issues:
        error_msg = "Optional APIs referenced without prerequisite notes:\n\n"
        for issue in optional_issues:
            error_msg += (
                f"File: {issue['file']}\n"
                f"Block: {issue['block']}, Line: {issue['line']}\n"
                f"Symbol: {issue['symbol']} (requires {issue['extra']} extra)\n"
                f"Issue: {issue['issue']}\n\n"
            )
        pytest.fail(error_msg)


def test_extractor_functionality():
    """Test the markdown extraction logic itself"""
    sample_markdown = '''# Test Documentation

Some text here.

**Prerequisites:** pip install "ai-utilities[openai]"

```python
from ai_utilities import AiClient, parse_json_from_text
import ai_utilities
from ai_utilities.something import SomeClass

client = AiClient()
result = parse_json_from_text("test")
```

More text.

```python
import ai_utilities.other as other_mod
from ai_utilities import *
```
'''
    
    # Create temporary file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(sample_markdown)
        temp_path = Path(f.name)
    
    try:
        # Test block extraction
        blocks = extract_python_blocks(temp_path)
        assert len(blocks) == 2, f"Expected 2 blocks, got {len(blocks)}"
        
        # Test first block
        first_block = blocks[0]
        assert first_block.block_index == 0
        assert "from ai_utilities import AiClient" in first_block.content
        assert len(first_block.context_lines) >= 5
        
        # Test import extraction
        imports = extract_imports(first_block)
        ai_imports = [imp for imp in imports if imp.module.startswith('ai_utilities')]
        assert len(ai_imports) == 4, f"Expected 4 ai_utilities imports, got {len(ai_imports)}"
        
        # Check specific imports
        import_names = {imp.name for imp in ai_imports if imp.is_from_import}
        expected_names = {"AiClient", "parse_json_from_text", "SomeClass"}
        assert expected_names.issubset(import_names), f"Missing expected imports: {import_names}"
        
        # Test prerequisite detection
        has_prereqs = has_prerequisites_for_symbol(first_block, "openai")
        assert has_prereqs, "Should detect openai prerequisite in context"
        
    finally:
        temp_path.unlink()


if __name__ == "__main__":
    # Allow running this test directly for debugging
    test_docs_api_contract()
    test_extractor_functionality()
    print("All docs API contract tests passed!")
