"""
Common utilities for examples.

Provides shared functionality for all example scripts including:
- Bootstrap system for running from any location
- Output directory management
- Safe file writing with error detection
- Environment variable validation
- Audio/image format validation
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import List


# === BOOTSTRAP SYSTEM ===
def _bootstrap_ai_utilities():
    """Ensure ai_utilities is importable from any location."""
    # Get the script's file path
    script_path = Path(__file__).resolve()
    
    # Find repo root (examples/_common.py -> examples/ -> repo root)
    repo_root = script_path.parent.parent
    
    # Add src directory to sys.path if not already there
    src_dir = repo_root / "src"
    src_dir_str = str(src_dir)
    if src_dir_str not in sys.path:
        sys.path.insert(0, src_dir_str)
    
    # Add repo root to sys.path for examples import
    repo_root_str = str(repo_root)
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)
    
    return repo_root


# Execute bootstrap immediately
_repo_root = _bootstrap_ai_utilities()


def repo_root() -> Path:
    """Get the repository root directory."""
    return _repo_root


def assets_dir() -> Path:
    """Get the examples assets directory."""
    return repo_root() / "examples" / "assets"


def output_dir(script_path: Path) -> Path:
    """Get output directory for a specific script.
    
    Args:
        script_path: Path to the script file
        
    Returns:
        Path to the script's output directory
    """
    # Allow override for tests
    override_dir = os.getenv("AI_UTILITIES_EXAMPLES_OUTPUT_DIR")
    if override_dir:
        base_dir = Path(override_dir)
    else:
        base_dir = repo_root() / "examples" / "_output"
    
    # Use script name as subdirectory
    script_name = script_path.stem
    script_output_dir = base_dir / script_name
    script_output_dir.mkdir(parents=True, exist_ok=True)
    return script_output_dir


def print_header(title: str) -> None:
    """Print a formatted header.
    
    Args:
        title: Header title
    """
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)


def require_env(var_names: List[str]) -> bool:
    """Check for required environment variables and print helpful message.
    
    Args:
        var_names: List of required environment variable names
        
    Returns:
        True if all required variables are present, False otherwise
    """
    missing = [var for var in var_names if not os.getenv(var)]
    
    if missing:
        print("❌ CONFIGURATION REQUIRED")
        print("Missing required environment variables:")
        for var in missing:
            print(f"   {var}")
        
        print("\n💡 To fix this:")
        print("   export OPENAI_API_KEY='your-key-here'")
        print("   # Or create a .env file with these variables")
        return False
    
    return True


def safe_write_bytes(path: Path, data: bytes) -> None:
    """Write bytes to file with atomic-ish behavior.
    
    Args:
        path: Output file path
        data: Bytes to write
    """
    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to temporary file first, then rename
    temp_path = path.with_suffix(path.suffix + ".tmp")
    try:
        temp_path.write_bytes(data)
        temp_path.replace(path)
    except Exception:
        # Clean up temp file if something went wrong
        if temp_path.exists():
            temp_path.unlink()
        raise


# === LEGACY FUNCTIONS (deprecated, use new ones above) ===
def get_outputs_dir() -> Path:
    """Get or create the outputs directory.
    
    Returns:
        Path to the examples/outputs directory
    """
    print("⚠️  get_outputs_dir() is deprecated, use output_dir(__file__) instead")
    examples_dir = Path(__file__).parent
    outputs_dir = examples_dir / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    return outputs_dir


def write_bytes(path: Path, data: bytes) -> None:
    """Write bytes to file with atomic-ish behavior.
    
    Args:
        path: Output file path
        data: Bytes to write
    """
    print("⚠️  write_bytes() is deprecated, use safe_write_bytes() instead")
    safe_write_bytes(path, data)


def looks_like_json_error(data: bytes) -> bool:
    """Check if data looks like a JSON error response.
    
    Args:
        data: Raw bytes to check
        
    Returns:
        True if data appears to be JSON error response
    """
    try:
        text = data.decode('utf-8').strip()
        if text.startswith('{') and text.endswith('}'):
            parsed = json.loads(text)
            # Check for common error indicators
            return any(key in str(parsed).lower() for key in ['error', 'message', 'code'])
    except (UnicodeDecodeError, json.JSONDecodeError):
        pass
    return False


def looks_like_mp3(data: bytes) -> bool:
    """Check if data looks like MP3 audio.
    
    Args:
        data: Raw bytes to check
        
    Returns:
        True if data has MP3 header signatures
    """
    if len(data) < 3:
        return False
    
    # Check for ID3 tag
    if data[:3] == b'ID3':
        return True
    
    # Check for MP3 sync (11 bits set)
    if len(data) >= 2:
        # Look for frame sync pattern (first 11 bits should be 1)
        sync_word = (data[0] << 8) | data[1]
        # MPEG frame sync: 11111111111 (0xFFE or 0xFFF)
        return (sync_word & 0xFFE0) == 0xFFE0
    
    return False


def looks_like_wav(data: bytes) -> bool:
    """Check if data looks like WAV audio.
    
    Args:
        data: Raw bytes to check
        
    Returns:
        True if data has WAV header signature
    """
    if len(data) < 12:
        return False
    
    # Check for RIFF header and WAVE format
    return data[:4] == b'RIFF' and data[8:12] == b'WAVE'


def safe_write_audio(path: Path, data: bytes) -> None:
    """Safely write audio data with error detection.
    
    Args:
        path: Output file path
        data: Raw bytes to write
    """
    # Check for JSON error first
    if looks_like_json_error(data):
        try:
            error_info = json.loads(data.decode('utf-8'))
            print(f"❌ API Error received instead of audio:")
            print(f"   {error_info}")
            print(f"   Not writing to {path.name}")
            return
        except (json.JSONDecodeError, UnicodeDecodeError):
            print("❌ Received data that looks like JSON error but couldn't parse")
            return
    
    # Check if it looks like expected audio format
    expected_format = path.suffix.lower()
    is_audio = False
    
    if expected_format == '.mp3':
        is_audio = looks_like_mp3(data)
    elif expected_format == '.wav':
        is_audio = looks_like_wav(data)
    
    if is_audio:
        safe_write_bytes(path, data)
        print(f"✅ Saved audio to {path}")
    else:
        # Write as .bin file with warning
        bin_path = path.with_suffix('.bin')
        safe_write_bytes(bin_path, data)
        print(f"⚠️  Data doesn't look like {expected_format} audio")
        print(f"   Saved raw bytes to {bin_path}")
        print(f"   Check if this is expected audio format")


def print_env_hint(missing: List[str]) -> None:
    """Print helpful hint about missing environment variables.
    
    Args:
        missing: List of missing environment variable names
    """
    if not missing:
        return
    
    print("🔑 Missing required environment variables:")
    for var in missing:
        print(f"   {var}")
    
    print("\n💡 Set them in your environment:")
    print("   export OPENAI_API_KEY='your-key-here'")
    print("   export AI_PROVIDER='openai'")
    print("   # Or create a .env file with these variables")


def check_env_vars(required: List[str]) -> List[str]:
    """Check for required environment variables.
    
    Args:
        required: List of required environment variable names
        
    Returns:
        List of missing environment variable names
    """
    print("⚠️  check_env_vars() is deprecated, use require_env() instead")
    missing = [var for var in required if not os.getenv(var)]
    if missing:
        print_env_hint(missing)
    return missing
