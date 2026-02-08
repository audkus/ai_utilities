"""Comprehensive CLI tests for Phase 4 - CLI and Setup functionality."""

import os
import sys
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, call
from io import StringIO

import pytest

from ai_utilities.cli import create_parser, main
from ai_utilities.setup.wizard import SetupMode, run_setup_wizard, SetupResult, SetupWizard

# Compute repo root dynamically
REPO_ROOT = Path(__file__).resolve().parents[3]


class TestCLIArgumentParsing:
    """Test CLI argument parsing functionality."""
    
    def test_create_parser_basic(self):
        """Test basic parser creation."""
        parser = create_parser()
        
        assert parser.prog == "ai-utilities"
        assert "AI Utilities - Setup and configuration tool" in parser.description
        assert "setup" in parser._subparsers._group_actions[0].choices
    
    def test_parse_setup_command_default(self):
        """Test parsing setup command with defaults."""
        parser = create_parser()
        args = parser.parse_args(["setup"])
        
        assert args.command == "setup"
        assert args.mode is None
        assert args.dotenv_path == ".env"
        assert args.dry_run is False
        assert args.non_interactive is False
    
    def test_parse_setup_command_with_options(self):
        """Test parsing setup command with all options."""
        parser = create_parser()
        args = parser.parse_args([
            "setup",
            "--mode", "enhanced",
            "--dotenv-path", "custom.env",
            "--dry-run",
            "--non-interactive"
        ])
        
        assert args.command == "setup"
        assert args.mode == "enhanced"
        assert args.dotenv_path == "custom.env"
        assert args.dry_run is True
        assert args.non_interactive is True
    
    def test_parse_invalid_mode(self):
        """Test parsing with invalid mode."""
        parser = create_parser()
        
        with pytest.raises(SystemExit):
            parser.parse_args(["setup", "--mode", "invalid"])
    
    def test_parse_no_command_defaults_to_setup(self):
        """Test that no command defaults to setup."""
        parser = create_parser()
        args = parser.parse_args([])
        
        # This would be handled in main() function
        assert hasattr(args, 'command')
    
    def test_help_output_contains_expected_content(self):
        """Test that help output contains expected information."""
        parser = create_parser()
        
        # Capture help output
        import contextlib
        f = StringIO()
        with contextlib.redirect_stdout(f):
            try:
                parser.parse_args(["--help"])
            except SystemExit:
                pass
        
        help_text = f.getvalue()
        assert "AI Utilities" in help_text
        assert "setup" in help_text
        assert "Run interactive setup wizard" in help_text


class TestCLIMainFunction:
    """Test CLI main function behavior."""
    
    def test_main_setup_success(self):
        """Test main function with successful setup."""
        mock_result = SetupResult(
            provider="openai",
            api_key="test-key-1234",
            base_url="https://api.openai.com/v1",
            model="gpt-3.5-turbo",
            dotenv_lines=["AI_PROVIDER=openai", "AI_API_KEY=test-key-1234"]
        )
        
        with patch("ai_utilities.cli.run_setup_wizard", return_value=mock_result) as mock_wizard:
            with patch("builtins.print") as mock_print:
                result = main(["setup", "--mode", "normal", "--dry-run"])
                
                assert result == 0
                mock_wizard.assert_called_once_with(
                    mode=SetupMode.NORMAL,
                    dotenv_path=".env",
                    dry_run=True,
                    non_interactive=False
                )
                
                # Check that success message was printed
                print_calls = [str(call) for call in mock_print.call_args_list]
                assert any("Setup completed successfully!" in call for call in print_calls)
    
    def test_main_setup_with_custom_dotenv_path(self):
        """Test main function with custom .env path."""
        mock_result = SetupResult(
            provider="openai",
            api_key="test-key",
            base_url=None,
            model=None,
            dotenv_lines=[]
        )
        
        with patch("ai_utilities.cli.run_setup_wizard", return_value=mock_result) as mock_wizard:
            result = main(["setup", "--dotenv-path", "custom.env"])
            
            assert result == 0
            # Check that custom path was passed through
            mock_wizard.assert_called_once()
            call_args = mock_wizard.call_args[1]
            assert call_args["dotenv_path"] == "custom.env"
    
    def test_main_setup_keyboard_interrupt(self):
        """Test main function handles KeyboardInterrupt."""
        with patch("ai_utilities.cli.run_setup_wizard", side_effect=KeyboardInterrupt()):
            with patch("builtins.print") as mock_print:
                result = main(["setup"])
                
                assert result == 1
                # Check that cancellation message was printed
                print_calls = [str(call) for call in mock_print.call_args_list]
                assert any("Setup cancelled by user" in call for call in print_calls)
    
    def test_main_setup_general_exception(self):
        """Test main function handles general exceptions."""
        with patch("ai_utilities.cli.run_setup_wizard", side_effect=Exception("Test error")):
            with patch("builtins.print") as mock_print:
                result = main(["setup"])
                
                assert result == 1
                # Check that error message was printed
                print_calls = [str(call) for call in mock_print.call_args_list]
                assert any("Error: Test error" in call for call in print_calls)
    
    def test_main_invalid_command(self):
        """Test main function with invalid command."""
        with patch("ai_utilities.cli.create_parser") as mock_parser:
            mock_parser_instance = MagicMock()
            mock_parser_instance.parse_args.return_value = MagicMock(command="invalid")
            mock_parser.return_value = mock_parser_instance
            
            with patch("builtins.print"):  # Suppress help output
                result = main(["invalid"])
                
                assert result == 1
    
    def test_main_no_args_defaults_to_setup(self):
        """Test main function with no arguments defaults to setup."""
        mock_result = SetupResult(
            provider="openai",
            api_key=None,
            base_url=None,
            model=None,
            dotenv_lines=[]
        )
        
        with patch("ai_utilities.cli.run_setup_wizard", return_value=mock_result) as mock_wizard:
            result = main([])
            
            assert result == 0
            mock_wizard.assert_called_once_with(
                mode=None,
                dotenv_path=".env",
                dry_run=False,
                non_interactive=False
            )
    
    def test_main_mode_string_to_enum_conversion(self):
        """Test that mode strings are properly converted to enums."""
        mock_result = SetupResult(
            provider="openai",
            api_key=None,
            base_url=None,
            model=None,
            dotenv_lines=[]
        )
        
        test_cases = [
            ("normal", SetupMode.NORMAL),
            ("enhanced", SetupMode.ENHANCED),
            ("improved", SetupMode.IMPROVED)
        ]
        
        for mode_str, expected_enum in test_cases:
            with patch("ai_utilities.cli.run_setup_wizard", return_value=mock_result) as mock_wizard:
                main(["setup", "--mode", mode_str])
                
                call_args = mock_wizard.call_args[1]
                assert call_args["mode"] == expected_enum


class TestCLIIntegration:
    """Test CLI integration scenarios."""
    
    def test_cli_subprocess_integration(self):
        """Test CLI integration via subprocess."""
        result = subprocess.run(
            [sys.executable, "-m", "ai_utilities.cli", "--help"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            env={**os.environ, "PYTHONPATH": "src"}
        )
        
        assert result.returncode == 0
        assert "AI Utilities" in result.stdout
        assert "setup" in result.stdout
    
    def test_cli_setup_subprocess_help(self):
        """Test setup command help via subprocess."""
        result = subprocess.run(
            [sys.executable, "-m", "ai_utilities.cli", "setup", "--help"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            env={**os.environ, "PYTHONPATH": "src"}
        )
        
        assert result.returncode == 0
        assert "--mode" in result.stdout
        assert "--dry-run" in result.stdout
        assert "--non-interactive" in result.stdout
    
    def test_cli_setup_dry_run_via_subprocess(self):
        """Test setup dry run via subprocess."""
        env = {**os.environ, "PYTHONPATH": "src", "AI_API_KEY": "test-key-12345"}
        
        result = subprocess.run(
            [sys.executable, "-m", "ai_utilities.cli", "setup", "--mode", "normal", "--dry-run", "--non-interactive"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            env=env
        )
        
        assert result.returncode == 0
        assert "Setup completed successfully!" in result.stdout
        assert "Provider: openai" in result.stdout
    
    def test_cli_with_missing_environment(self):
        """Test CLI behavior with missing environment variables."""
        # Remove AI API keys from environment
        clean_env = {k: v for k, v in os.environ.items() 
                    if k not in ["AI_API_KEY", "OPENAI_API_KEY"]}
        clean_env["PYTHONPATH"] = "src"
        
        result = subprocess.run(
            [sys.executable, "-m", "ai_utilities.cli", "setup", "--mode", "normal", "--dry-run", "--non-interactive"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            env=clean_env
        )
        
        assert result.returncode == 0
        # Should still complete but without API key
        assert "Setup completed successfully!" in result.stdout


class TestCLIErrorHandling:
    """Test CLI error handling scenarios."""
    
    def test_cli_invalid_mode_via_subprocess(self):
        """Test CLI with invalid mode via subprocess."""
        result = subprocess.run(
            [sys.executable, "-m", "ai_utilities.cli", "setup", "--mode", "invalid"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            env={**os.environ, "PYTHONPATH": "src"}
        )
        
        assert result.returncode != 0
        # Should show error about invalid choice
    
    def test_cli_file_permission_error(self):
        """Test CLI handling of file permission errors."""
        mock_result = SetupResult(
            provider="openai",
            api_key="test-key",
            base_url=None,
            model=None,
            dotenv_lines=[]
        )
        
        with patch("ai_utilities.cli.run_setup_wizard", return_value=mock_result) as mock_wizard:
            with patch("builtins.open", side_effect=PermissionError("Permission denied")):
                with patch("builtins.print") as mock_print:
                    result = main(["setup", "--dotenv-path", "/root/.env"])
                    
                    # Should still return 0 because the error happens in the wizard, not CLI
                    assert result == 0
                    # Should have called the wizard
                    mock_wizard.assert_called_once()
    
    def test_cli_unicode_handling(self):
        """Test CLI handling of unicode characters."""
        mock_result = SetupResult(
            provider="openai",
            api_key="test-key-ñáéíóú",
            base_url="https://api.openai.com/v1",
            model="gpt-3.5-turbo",
            dotenv_lines=["AI_PROVIDER=openai", "AI_API_KEY=test-key-ñáéíóú"]
        )
        
        with patch("ai_utilities.cli.run_setup_wizard", return_value=mock_result):
            with patch("builtins.print") as mock_print:
                result = main(["setup"])
                
                assert result == 0
                # Should handle unicode characters without error
                assert True  # If we get here, unicode was handled correctly
    
    def test_cli_very_long_api_key(self):
        """Test CLI handling of very long API keys."""
        long_key = "x" * 1000  # Very long API key
        mock_result = SetupResult(
            provider="openai",
            api_key=long_key,
            base_url=None,
            model=None,
            dotenv_lines=[f"AI_API_KEY={long_key}"]
        )
        
        with patch("ai_utilities.cli.run_setup_wizard", return_value=mock_result):
            with patch("builtins.print") as mock_print:
                result = main(["setup"])
                
                assert result == 0
                # Should handle long keys without error
                assert True


class TestCLIConfigurationOptions:
    """Test CLI configuration options and edge cases."""
    
    def test_cli_all_mode_options(self):
        """Test CLI with all available mode options."""
        modes = ["normal", "enhanced", "improved"]
        
        for mode in modes:
            mock_result = SetupResult(
                provider="openai",
                api_key="test-key",
                base_url=None,
                model=None,
                dotenv_lines=[]
            )
            
            with patch("ai_utilities.cli.run_setup_wizard", return_value=mock_result) as mock_wizard:
                result = main(["setup", "--mode", mode, "--dry-run", "--non-interactive"])
                
                assert result == 0
                # Verify mode was passed correctly
                call_args = mock_wizard.call_args[1]
                expected_enum = SetupMode(mode)
                assert call_args["mode"] == expected_enum
    
    def test_cli_custom_dotenv_paths(self):
        """Test CLI with various custom .env paths."""
        test_paths = [
            "custom.env",
            "config/.env",
            "/absolute/path/.env",
            "relative/path/.env"
        ]
        
        for dotenv_path in test_paths:
            mock_result = SetupResult(
                provider="openai",
                api_key="test-key",
                base_url=None,
                model=None,
                dotenv_lines=[]
            )
            
            with patch("ai_utilities.cli.run_setup_wizard", return_value=mock_result) as mock_wizard:
                result = main(["setup", "--dotenv-path", dotenv_path, "--dry-run"])
                
                assert result == 0
                call_args = mock_wizard.call_args[1]
                assert call_args["dotenv_path"] == dotenv_path
    
    def test_cli_dry_run_prevents_file_writes(self):
        """Test that dry-run prevents actual file writes."""
        mock_result = SetupResult(
            provider="openai",
            api_key="test-key",
            base_url=None,
            model=None,
            dotenv_lines=["AI_PROVIDER=openai"]
        )
        
        with patch("ai_utilities.cli.run_setup_wizard", return_value=mock_result) as mock_wizard:
            with patch("builtins.print") as mock_print:
                result = main(["setup", "--dry-run"])
                
                assert result == 0
                # Verify dry-run was passed
                call_args = mock_wizard.call_args[1]
                assert call_args["dry_run"] is True
                
                # Should not mention writing to file
                print_calls = [str(call) for call in mock_print.call_args_list]
                assert not any("Configuration written to:" in call for call in print_calls)
    
    def test_cli_non_interactive_mode(self):
        """Test CLI non-interactive mode behavior."""
        mock_result = SetupResult(
            provider="openai",
            api_key="test-key",
            base_url=None,
            model=None,
            dotenv_lines=[]
        )
        
        with patch("ai_utilities.cli.run_setup_wizard", return_value=mock_result) as mock_wizard:
            result = main(["setup", "--non-interactive"])
            
            assert result == 0
            # Verify non-interactive was passed
            call_args = mock_wizard.call_args[1]
            assert call_args["non_interactive"] is True
    
    def test_cli_combined_options(self):
        """Test CLI with multiple options combined."""
        mock_result = SetupResult(
            provider="openai",
            api_key="test-key",
            base_url="https://custom.url",
            model="custom-model",
            dotenv_lines=[]
        )
        
        with patch("ai_utilities.cli.run_setup_wizard", return_value=mock_result) as mock_wizard:
            with patch("builtins.print") as mock_print:
                result = main([
                    "setup",
                    "--mode", "enhanced",
                    "--dotenv-path", "test.env",
                    "--dry-run",
                    "--non-interactive"
                ])
                
                assert result == 0
                
                # Verify all options were passed correctly
                call_args = mock_wizard.call_args[1]
                assert call_args["mode"] == SetupMode.ENHANCED
                assert call_args["dotenv_path"] == "test.env"
                assert call_args["dry_run"] is True
                assert call_args["non_interactive"] is True
