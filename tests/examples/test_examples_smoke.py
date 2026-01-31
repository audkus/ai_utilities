"""
Smoke tests for examples/

Runs a small allowlist of example scripts to ensure they start and fail gracefully
when environment variables are missing.
"""

import os
import pathlib
import subprocess
import sys
import tempfile
from typing import List

import pytest


# Smoke-test allowlist - choose 3-6 representative examples
SMOKE_TEST_ALLOWLIST = [
    "examples/quickstarts/audio_tts_basic.py",
    "examples/quickstarts/image_generate_basic.py", 
    "examples/quickstarts/files_upload_basic.py",
    "examples/quickstarts/text_generate_basic.py",
    "examples/quickstarts/usage_tracking_basic.py",
]


def get_example_path(script_name: str) -> pathlib.Path:
    """Get full path to example script."""
    project_root = pathlib.Path(__file__).parent.parent.parent
    return project_root / script_name


def get_file_mtimes(directory: pathlib.Path) -> dict:
    """Get modification times for all files in directory (excluding outputs/)."""
    mtimes = {}
    for file_path in directory.rglob("*"):
        if file_path.is_file() and "outputs" not in file_path.parts and "__pycache__" not in file_path.parts:
            mtimes[file_path] = file_path.stat().st_mtime
    return mtimes


def create_sanitized_env() -> dict:
    """Create a sanitized environment for smoke testing."""
    # Start with current environment
    env = os.environ.copy()
    
    # Add PYTHONPATH to include the src and examples directories for imports
    project_root = pathlib.Path(__file__).parent.parent.parent
    src_path = str(project_root / "src")
    examples_path = str(project_root / "examples")
    env["PYTHONPATH"] = src_path + os.pathsep + examples_path + os.pathsep + env.get("PYTHONPATH", "")
    
    # Remove provider API keys to force graceful failure
    api_keys_to_remove = [
        "OPENAI_API_KEY",
        "GROQ_API_KEY", 
        "TOGETHER_API_KEY",
        "ANTHROPIC_API_KEY",
        "AI_API_KEY",
        "HUGGINGFACE_API_KEY",
        "REPLICATE_API_KEY",
        "COHERE_API_KEY",
    ]
    
    for key in api_keys_to_remove:
        env.pop(key, None)
    
    # Ensure we don't have any unexpected API keys
    for key in list(env.keys()):
        if "API_KEY" in key.upper() or "TOKEN" in key.upper():
            env.pop(key, None)
    
    return env


@pytest.mark.parametrize("script_name", SMOKE_TEST_ALLOWLIST)
def test_example_smoke(script_name: str) -> None:
    """Test that example script starts and fails gracefully without API keys."""
    script_path = get_example_path(script_name)
    examples_dir = pathlib.Path(__file__).parent.parent.parent / "examples"
    
    # Record file modification times before running
    mtimes_before = get_file_mtimes(examples_dir)
    
    # Create sanitized environment
    env = create_sanitized_env()
    
    # Run the script
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(script_path.parent),
        timeout=30,  # Prevent hanging
    )
    
    # Check that script exits with expected code (0, 1, or 2)
    assert result.returncode in (0, 1, 2), f"Script {script_name} exited with unexpected code {result.returncode}\nstdout: {result.stdout}\nstderr: {result.stderr}"
    
    # Check output contains missing env var indication
    output = result.stdout + result.stderr
    missing_env_indicators = [
        "missing",
        "set env", 
        "environment variable",
        "API_KEY",
        "OPENAI_API_KEY",
        "cannot proceed",
        "No providers are configured",
        "ProviderConfigurationError",
        "configuration error",
    ]
    
    has_missing_env_msg = any(indicator.lower() in output.lower() for indicator in missing_env_indicators)
    
    if result.returncode in (1, 2):  # Expected failure due to missing env vars or config
        assert has_missing_env_msg, f"Script {script_name} failed with code {result.returncode} but didn't mention missing environment variables or configuration\nOutput: {output}"
    
    # Check that no files were modified outside outputs/
    mtimes_after = get_file_mtimes(examples_dir)
    
    # Allow outputs/ directory to change (it's gitignored)
    for file_path, mtime_before in mtimes_before.items():
        mtime_after = mtimes_after.get(file_path)
        if mtime_after is not None and mtime_after != mtime_before:
            # File was modified - this should only happen in outputs/
            if "outputs" not in str(file_path):
                pytest.fail(f"Script {script_name} modified file {file_path.relative_to(examples_dir)} outside outputs/ directory")


def test_smoke_test_allowlist_exists() -> None:
    """Verify all scripts in smoke test allowlist exist."""
    project_root = pathlib.Path(__file__).parent.parent.parent
    
    for script_name in SMOKE_TEST_ALLOWLIST:
        script_path = project_root / script_name
        assert script_path.exists(), f"Smoke test script {script_name} does not exist at {script_path}"
        assert script_path.is_file(), f"Smoke test target {script_name} is not a file"


def test_sanitized_env_has_no_api_keys() -> None:
    """Verify our sanitized environment actually removes API keys."""
    env = create_sanitized_env()
    
    # Check that no API keys remain
    for key in env:
        assert "API_KEY" not in key.upper(), f"Environment still contains API key: {key}"
        assert "TOKEN" not in key.upper(), f"Environment still contains token: {key}"
