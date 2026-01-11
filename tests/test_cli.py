"""Tests for CLI functionality."""

import os
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from ai_utilities.cli import main
from ai_utilities.setup.wizard import SetupMode, run_setup_wizard


class TestCLI:
    """Test CLI command line interface."""

    def test_cli_help(self):
        """Test that CLI help works."""
        result = subprocess.run(
            ["python", "-m", "ai_utilities.cli", "--help"],
            capture_output=True,
            text=True,
            cwd="/Users/steffenrasmussen/PycharmProjects/ai_utilities",
            env={**os.environ, "PYTHONPATH": "src"}
        )
        assert result.returncode == 0
        assert "AI Utilities - Setup and configuration tool" in result.stdout

    def test_setup_help(self):
        """Test that setup help works."""
        result = subprocess.run(
            ["python", "-m", "ai_utilities.cli", "setup", "--help"],
            capture_output=True,
            text=True,
            cwd="/Users/steffenrasmussen/PycharmProjects/ai_utilities",
            env={**os.environ, "PYTHONPATH": "src"}
        )
        assert result.returncode == 0
        assert "Run interactive setup wizard" in result.stdout
        assert "--mode" in result.stdout
        assert "--dry-run" in result.stdout

    def test_setup_dry_run_normal_mode(self):
        """Test setup dry run in normal mode."""
        result = subprocess.run(
            ["python", "-m", "ai_utilities.cli", "setup", "--mode", "normal", "--dry-run", "--non-interactive"],
            capture_output=True,
            text=True,
            cwd="/Users/steffenrasmussen/PycharmProjects/ai_utilities",
            env={**os.environ, "PYTHONPATH": "src", "AI_API_KEY": "test-key-12345"}
        )
        assert result.returncode == 0
        assert "=== Dry Run: .env content ===" in result.stdout
        assert "AI_PROVIDER=openai" in result.stdout
        assert "AI_API_KEY=test-key-12345" in result.stdout
        assert "AI_MODEL=gpt-3.5-turbo" in result.stdout

    def test_setup_dry_run_enhanced_mode(self):
        """Test setup dry run in enhanced mode."""
        result = subprocess.run(
            ["python", "-m", "ai_utilities.cli", "setup", "--mode", "enhanced", "--dry-run", "--non-interactive"],
            capture_output=True,
            text=True,
            cwd="/Users/steffenrasmussen/PycharmProjects/ai_utilities",
            env={**os.environ, "PYTHONPATH": "src", "AI_API_KEY": "test-key-12345"}
        )
        assert result.returncode == 0
        assert "Setup completed successfully!" in result.stdout
        assert "Provider: openai" in result.stdout

    def test_setup_non_interactive_missing_api_key(self):
        """Test setup in non-interactive mode without API key."""
        # Clear API key environment
        env = {k: v for k, v in os.environ.items() if k not in ["AI_API_KEY", "OPENAI_API_KEY"]}
        env["PYTHONPATH"] = "src"
        
        result = subprocess.run(
            ["python", "-m", "ai_utilities.cli", "setup", "--mode", "normal", "--dry-run", "--non-interactive"],
            capture_output=True,
            text=True,
            cwd="/Users/steffenrasmussen/PycharmProjects/ai_utilities",
            env=env
        )
        assert result.returncode == 0
        assert "AI_PROVIDER=openai" in result.stdout
        assert "AI_API_KEY" not in result.stdout  # Should not include API key line

    def test_main_function_directly(self):
        """Test main function directly."""
        with patch("ai_utilities.cli.run_setup_wizard") as mock_wizard:
            mock_result = MagicMock()
            mock_result.provider = "openai"
            mock_result.model = "gpt-3.5-turbo"
            mock_result.base_url = "https://api.openai.com/v1"
            mock_result.api_key = "test-key"
            mock_wizard.return_value = mock_result
            
            result = main(["setup", "--mode", "normal", "--dry-run", "--non-interactive"])
            assert result == 0
            mock_wizard.assert_called_once()

    def test_main_function_invalid_command(self):
        """Test main function with invalid command."""
        result = main(["invalid"])
        assert result == 1


class TestSetupWizard:
    """Test setup wizard functionality."""

    def test_run_wizard_normal_mode_non_interactive(self):
        """Test wizard in normal mode non-interactive."""
        # Clear existing API keys and set test key
        env = {k: v for k, v in os.environ.items() if k not in ["AI_API_KEY", "OPENAI_API_KEY"]}
        env["AI_API_KEY"] = "test-key-12345"
        
        with patch.dict(os.environ, env, clear=True):
            result = run_setup_wizard(
                mode=SetupMode.NORMAL,
                dotenv_path=".env",
                dry_run=True,
                non_interactive=True
            )
            
            assert result.provider == "openai"
            assert result.api_key == "test-key-12345"
            assert result.model == "gpt-3.5-turbo"
            assert result.base_url == "https://api.openai.com/v1"
            assert "AI_PROVIDER=openai" in result.dotenv_lines
            assert "AI_API_KEY=test-key-12345" in result.dotenv_lines
            assert "AI_MODEL=gpt-3.5-turbo" in result.dotenv_lines

    def test_run_wizard_enhanced_mode_non_interactive(self):
        """Test wizard in enhanced mode non-interactive."""
        # Clear existing API keys and set test key
        env = {k: v for k, v in os.environ.items() if k not in ["AI_API_KEY", "OPENAI_API_KEY"]}
        env["OPENAI_API_KEY"] = "test-key-67890"
        
        with patch.dict(os.environ, env, clear=True):
            result = run_setup_wizard(
                mode=SetupMode.ENHANCED,
                dotenv_path=".env",
                dry_run=True,
                non_interactive=True
            )
            
            assert result.provider == "openai"
            assert result.api_key == "test-key-67890"
            assert result.model == "gpt-3.5-turbo"

    def test_run_wizard_improved_mode_non_interactive(self):
        """Test wizard in improved mode non-interactive."""
        # Clear existing API keys and set test key
        env = {k: v for k, v in os.environ.items() if k not in ["AI_API_KEY", "OPENAI_API_KEY"]}
        env["AI_API_KEY"] = "test-key-improved"
        
        with patch.dict(os.environ, env, clear=True):
            result = run_setup_wizard(
                mode=SetupMode.IMPROVED,
                dotenv_path=".env",
                dry_run=True,
                non_interactive=True
            )
            
            assert result.provider == "openai"
            assert result.api_key == "test-key-improved"
            assert result.model == "gpt-3.5-turbo"

    def test_run_wizard_non_interactive_no_mode(self):
        """Test wizard in non-interactive mode without specifying mode."""
        with pytest.raises(ValueError, match="Mode must be specified in non-interactive mode"):
            run_setup_wizard(
                mode=None,
                dotenv_path=".env",
                dry_run=True,
                non_interactive=True
            )

    def test_run_wizard_no_api_key(self):
        """Test wizard in non-interactive mode without API key."""
        # Clear all environment variables
        env = {k: v for k, v in os.environ.items() if k not in ["AI_API_KEY", "OPENAI_API_KEY"]}
        
        with patch.dict(os.environ, env, clear=True):
            result = run_setup_wizard(
                mode=SetupMode.NORMAL,
                dotenv_path=".env",
                dry_run=True,
                non_interactive=True
            )
            
            assert result.provider == "openai"
            assert result.api_key is None
            assert result.model == "gpt-3.5-turbo"
            assert "AI_PROVIDER=openai" in result.dotenv_lines
            assert "AI_MODEL=gpt-3.5-turbo" in result.dotenv_lines
            assert "AI_API_KEY" not in "\n".join(result.dotenv_lines)


class TestDotenvUpdate:
    """Test .env file update functionality."""

    def test_dotenv_update_preserves_existing(self):
        """Test that .env update preserves existing unrelated keys."""
        from ai_utilities.setup.wizard import SetupWizard
        
        # Create temporary .env file with existing content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("# Existing configuration\n")
            f.write("EXISTING_KEY=existing_value\n")
            f.write("AI_PROVIDER=old_provider\n")
            f.write("UNRELATED_KEY=unrelated_value\n")
            dotenv_path = f.name
        
        try:
            # Run wizard that should update AI_* keys
            with patch.dict(os.environ, {"AI_API_KEY": "new-key"}):
                wizard = SetupWizard()
                result = run_setup_wizard(
                    mode=SetupMode.NORMAL,
                    dotenv_path=dotenv_path,
                    dry_run=False,
                    non_interactive=True
                )
            
            # Read the updated file
            with open(dotenv_path, 'r') as f:
                content = f.read()
            
            # Check that existing keys are preserved
            assert "EXISTING_KEY=existing_value" in content
            assert "UNRELATED_KEY=unrelated_value" in content
            
            # Check that AI_* keys are updated
            assert "AI_PROVIDER=openai" in content
            assert "AI_API_KEY=new-key" in content
            assert "AI_MODEL=gpt-3.5-turbo" in content
            
            # Check that old provider is replaced
            assert "old_provider" not in content
            
        finally:
            os.unlink(dotenv_path)

    def test_dotenv_create_new_file(self):
        """Test that .env creation works for new files."""
        from ai_utilities.setup.wizard import SetupWizard
        
        with tempfile.TemporaryDirectory() as temp_dir:
            dotenv_path = Path(temp_dir) / "test.env"
            
            # Run wizard that should create new .env
            with patch.dict(os.environ, {"AI_API_KEY": "new-key"}):
                result = run_setup_wizard(
                    mode=SetupMode.NORMAL,
                    dotenv_path=str(dotenv_path),
                    dry_run=False,
                    non_interactive=True
                )
            
            # Check file was created
            assert dotenv_path.exists()
            
            # Check content
            with open(dotenv_path, 'r') as f:
                content = f.read()
            
            assert "AI_PROVIDER=openai" in content
            assert "AI_API_KEY=new-key" in content
            assert "AI_MODEL=gpt-3.5-turbo" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
