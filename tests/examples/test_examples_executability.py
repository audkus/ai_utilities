"""
Contract-first tests for examples.

Tests validate:
- Scripts can execute from any location
- Exit codes are correct for offline-safe vs provider-required scripts
- Output directories are created and used properly
- Graceful failure when configuration is missing
- No network calls or API dependencies in tests
"""

import subprocess
import tempfile
import time
from pathlib import Path
from typing import List, Dict, Any
import pytest
import os
import sys


# Get the examples directory
EXAMPLES_DIR = Path(__file__).parent.parent.parent / "examples"


def discover_example_scripts() -> List[Path]:
    """Discover all example scripts, excluding common files."""
    scripts = []
    for script_path in EXAMPLES_DIR.rglob("*.py"):
        # Skip common files and test files
        if any(name in script_path.name for name in ["_common.py", "_bootstrap_template.py", "__init__.py", "test_"]):
            continue
        scripts.append(script_path)
    return sorted(scripts)


# Classify scripts by their expected behavior
OFFLINE_SAFE_SCRIPTS = {
    "metrics_monitoring_basic.py",
    "usage_tracking_basic.py",
}

REQUIRES_AI_PROVIDER_SCRIPTS = {
    "text_generate_basic.py",
    "audio_transcribe_basic.py", 
    "audio_tts_basic.py",
    "document_basic.py",
    "files_upload_basic.py",
    "image_generate_basic.py",
    "document_step_01_extract.py",
    "document_step_02_summarize.py", 
    "document_step_03_transform.py",
    "files_operations.py",
    "image_generate_multiple.py",
    "metrics_monitoring_advanced.py",
}

OPTIONAL_ASSET_REQUIRED_SCRIPTS = {
    "fastchat_basic.py",
    "text_generation_webui_basic.py",
}


def get_script_classification(script_path: Path) -> str:
    """Get the classification of a script based on its filename."""
    script_name = script_path.name
    
    if script_name in OFFLINE_SAFE_SCRIPTS:
        return "OFFLINE_SAFE"
    elif script_name in REQUIRES_AI_PROVIDER_SCRIPTS:
        return "REQUIRES_AI_PROVIDER"
    elif script_name in OPTIONAL_ASSET_REQUIRED_SCRIPTS:
        return "OPTIONAL_ASSET_REQUIRED"
    else:
        return "UNKNOWN"


def run_script_as_subprocess(script_path: Path, env_overrides: Dict[str, str] = None) -> subprocess.CompletedProcess:
    """Run a script as a subprocess with controlled environment."""
    # Create a clean environment
    env = os.environ.copy()
    
    # Remove any AI-related environment variables to ensure offline behavior
    ai_vars = [k for k in env.keys() if any(term in k.upper() for term in ["OPENAI", "AI_", "API_KEY", "PROVIDER"])]
    for var in ai_vars:
        del env[var]
    
    # Add test-specific overrides
    if env_overrides:
        env.update(env_overrides)
    
    # Set output directory override for tests
    with tempfile.TemporaryDirectory() as temp_dir:
        env["AI_UTILITIES_EXAMPLES_OUTPUT_DIR"] = temp_dir
        
        # Run the script
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            env=env,
            timeout=30,  # Prevent hanging
            cwd=EXAMPLES_DIR  # Run from examples directory
        )
        
        return result


@pytest.mark.parametrize("script_path", discover_example_scripts())
def test_script_executability(script_path: Path):
    """Test that scripts can execute from any location."""
    classification = get_script_classification(script_path)
    
    # Run the script
    result = run_script_as_subprocess(script_path)
    
    # All scripts should be executable (not crash on import)
    assert result.returncode in [0, 1], f"Script {script_path.name} crashed with return code {result.returncode}"
    
    # Check that it doesn't have import errors
    assert "ModuleNotFoundError" not in result.stderr, f"Script {script_path.name} has import errors"
    assert "ImportError" not in result.stderr, f"Script {script_path.name} has import errors"


@pytest.mark.parametrize("script_path", discover_example_scripts())
def test_offline_safe_scripts(script_path: Path):
    """Test that offline-safe scripts run successfully without API keys."""
    classification = get_script_classification(script_path)
    
    if classification != "OFFLINE_SAFE":
        pytest.skip(f"Script {script_path.name} is not classified as OFFLINE_SAFE")
    
    # Run the script without any API keys
    result = run_script_as_subprocess(script_path)
    
    # Should succeed (exit code 0)
    assert result.returncode == 0, f"OFFLINE_SAFE script {script_path.name} failed with exit code {result.returncode}"
    
    # Should not contain error messages about missing configuration
    assert "❌ CONFIGURATION REQUIRED" not in result.stdout, f"OFFLINE_SAFE script {script_path.name} should not require configuration"
    
    # Should create output directory
    assert "📁" in result.stdout or "outputs" in result.stdout.lower(), f"OFFLINE_SAFE script {script_path.name} should show output location"


@pytest.mark.parametrize("script_path", discover_example_scripts())
def test_provider_required_scripts_graceful_failure(script_path: Path):
    """Test that provider-required scripts fail gracefully without API keys."""
    classification = get_script_classification(script_path)
    
    if classification != "REQUIRES_AI_PROVIDER":
        pytest.skip(f"Script {script_path.name} is not classified as REQUIRES_AI_PROVIDER")
    
    # Run the script without any API keys
    result = run_script_as_subprocess(script_path)
    
    # Should fail with non-zero exit code
    assert result.returncode != 0, f"REQUIRES_AI_PROVIDER script {script_path.name} should fail without API keys"
    
    # Should contain the standard configuration required message
    assert "❌ CONFIGURATION REQUIRED" in result.stdout, f"Script {script_path.name} should show configuration required message"
    
    # Should mention OPENAI_API_KEY
    assert "OPENAI_API_KEY" in result.stdout, f"Script {script_path.name} should mention OPENAI_API_KEY"
    
    # Should not crash with exception
    assert "Traceback" not in result.stderr, f"Script {script_path.name} should not crash with exception"


@pytest.mark.parametrize("script_path", discover_example_scripts())
def test_output_directory_creation(script_path: Path):
    """Test that scripts create and use output directories correctly."""
    classification = get_script_classification(script_path)
    
    # Skip provider-required scripts since they'll fail before creating outputs
    if classification == "REQUIRES_AI_PROVIDER":
        pytest.skip(f"Script {script_path.name} requires provider and won't create outputs")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Run with output directory override
        result = run_script_as_subprocess(script_path, {"AI_UTILITIES_EXAMPLES_OUTPUT_DIR": temp_dir})
        
        if result.returncode == 0:  # Only check if script succeeded
            # Check that output directory was created
            script_output_dir = Path(temp_dir) / script_path.stem
            assert script_output_dir.exists(), f"Script {script_path.name} should create output directory"
            
            # Check that script mentions output location
            assert "📁" in result.stdout or "output" in result.stdout.lower(), f"Script {script_path.name} should mention output location"


def test_bootstrap_system():
    """Test that the bootstrap system works correctly."""
    # Test running from different directories
    script_path = EXAMPLES_DIR / "quickstarts" / "metrics_monitoring_basic.py"
    
    # Test 1: Run from examples directory
    result1 = run_script_as_subprocess(script_path)
    assert result1.returncode == 0, "Script should run from examples directory"
    
    # Test 2: Run from repo root (simulate)
    repo_root = EXAMPLES_DIR.parent
    result2 = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        env={k: v for k, v in os.environ.items() if not any(term in k.upper() for term in ["OPENAI", "AI_", "API_KEY"])},
        timeout=30,
        cwd=repo_root
    )
    assert result2.returncode == 0, "Script should run from repo root"


def test_no_network_calls():
    """Test that examples don't make network calls in offline mode."""
    # This is a meta-test - we run all offline-safe scripts and ensure they complete quickly
    offline_scripts = [
        script for script in discover_example_scripts()
        if get_script_classification(script) == "OFFLINE_SAFE"
    ]
    
    for script_path in offline_scripts:
        start_time = time.time()
        result = run_script_as_subprocess(script_path)
        end_time = time.time()
        
        # Should complete quickly (no network calls)
        duration = end_time - start_time
        assert duration < 10, f"Script {script_path.name} took too long ({duration}s), may be making network calls"
        assert result.returncode == 0, f"Script {script_path.name} should succeed offline"


def test_contract_first_validation():
    """Test that we're not asserting on model-generated content."""
    script_path = EXAMPLES_DIR / "quickstarts" / "text_generate_basic.py"
    
    # Run without API keys - should fail gracefully
    result = run_script_as_subprocess(script_path)
    
    # Should NOT contain any model-generated content assertions
    # (We're checking the test itself, not the script output)
    assert "Explain dependency injection" not in result.stdout or result.returncode != 0, "Tests should not assert on model-generated content"
    
    # Should contain deterministic assertions (exit codes, messages, etc.)
    assert "❌ CONFIGURATION REQUIRED" in result.stdout, "Tests should assert on deterministic messages"


if __name__ == "__main__":
    # Run a quick manual test
    print("Discovered example scripts:")
    for script in discover_example_scripts():
        classification = get_script_classification(script)
        print(f"  {script.name} - {classification}")
