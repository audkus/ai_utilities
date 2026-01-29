"""
Tests for cli module.

This module tests the command-line interface functionality including
argument parsing, command handling, and error scenarios.
"""

import pytest
from unittest.mock import patch, MagicMock
from argparse import ArgumentParser

from ai_utilities.cli import create_parser, main


class TestCreateParser:
    """Test create_parser function."""
    
    def test_parser_creation(self):
        """Test that parser is created with correct configuration."""
        parser = create_parser()
        
        assert isinstance(parser, ArgumentParser)
        assert parser.prog == "ai-utilities"
        assert "AI Utilities" in parser.description
    
    def test_parser_has_setup_subcommand(self):
        """Test that parser has setup subcommand."""
        parser = create_parser()
        
        # Test parsing setup command
        args = parser.parse_args(["setup"])
        assert args.command == "setup"
        assert args.dotenv_path == ".env"  # default value
        assert args.dry_run is False
        assert args.non_interactive is False
    
    def test_setup_command_with_all_arguments(self):
        """Test setup command with all arguments."""
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
    
    def test_setup_mode_choices(self):
        """Test that setup mode accepts valid choices."""
        parser = create_parser()
        valid_modes = ["normal", "enhanced", "improved"]
        
        for mode in valid_modes:
            args = parser.parse_args(["setup", "--mode", mode])
            assert args.mode == mode
    
    def test_setup_mode_invalid_choice(self):
        """Test that invalid mode choices raise error."""
        parser = create_parser()
        
        with pytest.raises(SystemExit):
            parser.parse_args(["setup", "--mode", "invalid"])
    
    def test_parser_help(self):
        """Test that parser help works correctly."""
        parser = create_parser()
        
        help_text = parser.format_help()
        assert "ai-utilities" in help_text
        assert "setup" in help_text
        assert "Run interactive setup wizard" in help_text


class TestMainFunction:
    """Test main function."""
    
    @patch('ai_utilities.cli.run_setup_wizard')
    def test_main_default_to_setup(self, mock_setup_wizard):
        """Test that main defaults to setup when no arguments provided."""
        # Mock the wizard result
        mock_result = MagicMock()
        mock_result.provider = "openai"
        mock_result.model = "gpt-4"
        mock_result.base_url = None
        mock_result.api_key = "sk-test1234"
        mock_setup_wizard.return_value = mock_result
        
        with patch('builtins.print') as mock_print:
            exit_code = main([])
            
            assert exit_code == 0
            mock_setup_wizard.assert_called_once()
            
            # Check that success message was printed
            mock_print.assert_any_call("\nSetup completed successfully!")
            mock_print.assert_any_call("Provider: openai")
            mock_print.assert_any_call("Model: gpt-4")
    
    @patch('ai_utilities.cli.run_setup_wizard')
    def test_main_with_setup_command(self, mock_setup_wizard):
        """Test main with explicit setup command."""
        mock_result = MagicMock()
        mock_result.provider = "openai"
        mock_result.model = None
        mock_result.base_url = "https://api.openai.com"
        mock_result.api_key = "sk-key12345678"
        mock_setup_wizard.return_value = mock_result
        
        with patch('builtins.print') as mock_print:
            exit_code = main(["setup"])
            
            assert exit_code == 0
            mock_setup_wizard.assert_called_once_with(
                mode=None,
                dotenv_path=".env",
                dry_run=False,
                non_interactive=False
            )
    
    @patch('ai_utilities.cli.run_setup_wizard')
    def test_main_with_enhanced_mode(self, mock_setup_wizard):
        """Test main with enhanced setup mode."""
        from ai_utilities.setup.wizard import SetupMode
        
        mock_result = MagicMock()
        mock_result.provider = "openai"
        mock_result.model = "gpt-4"
        mock_result.base_url = None
        mock_result.api_key = None
        mock_setup_wizard.return_value = mock_result
        
        exit_code = main(["setup", "--mode", "enhanced"])
        
        assert exit_code == 0
        mock_setup_wizard.assert_called_once_with(
            mode=SetupMode.ENHANCED,
            dotenv_path=".env",
            dry_run=False,
            non_interactive=False
        )
    
    @patch('ai_utilities.cli.run_setup_wizard')
    def test_main_with_all_options(self, mock_setup_wizard):
        """Test main with all command line options."""
        from ai_utilities.setup.wizard import SetupMode
        
        mock_result = MagicMock()
        mock_result.provider = "openai"
        mock_result.model = None
        mock_result.base_url = None
        mock_result.api_key = None
        mock_setup_wizard.return_value = mock_result
        
        exit_code = main([
            "setup",
            "--mode", "improved",
            "--dotenv-path", "test.env",
            "--dry-run",
            "--non-interactive"
        ])
        
        assert exit_code == 0
        mock_setup_wizard.assert_called_once_with(
            mode=SetupMode.IMPROVED,
            dotenv_path="test.env",
            dry_run=True,
            non_interactive=True
        )
    
    @patch('ai_utilities.cli.run_setup_wizard')
    def test_main_dry_run_output(self, mock_setup_wizard):
        """Test that dry run doesn't mention file writing."""
        mock_result = MagicMock()
        mock_result.provider = "openai"
        mock_result.model = None
        mock_result.base_url = None
        mock_result.api_key = None
        mock_setup_wizard.return_value = mock_result
        
        with patch('builtins.print') as mock_print:
            exit_code = main(["setup", "--dry-run"])
            
            assert exit_code == 0
            
            # Should not mention writing to file in dry run
            print_calls = [str(call) for call in mock_print.call_args_list]
            assert not any("Configuration written to" in call for call in print_calls)
    
    @patch('ai_utilities.cli.run_setup_wizard')
    def test_main_api_key_masking(self, mock_setup_wizard):
        """Test that API key is properly masked in output."""
        mock_result = MagicMock()
        mock_result.provider = "openai"
        mock_result.model = None
        mock_result.base_url = None
        mock_result.api_key = "sk-1234567890abcdef"
        mock_setup_wizard.return_value = mock_result
        
        with patch('builtins.print') as mock_print:
            exit_code = main(["setup"])
            
            assert exit_code == 0
            
            # Check that API key is masked
            print_calls = [str(call) for call in mock_print.call_args_list]
            api_key_call = next(call for call in print_calls if "API Key:" in call)
            assert "********cdef" in api_key_call  # Should show last 4 chars
            assert "sk-1234567890abcdef" not in api_key_call  # Should not show full key
    
    @patch('ai_utilities.cli.run_setup_wizard')
    def test_main_short_api_key_masking(self, mock_setup_wizard):
        """Test API key masking for short keys."""
        mock_result = MagicMock()
        mock_result.provider = "openai"
        mock_result.model = None
        mock_result.base_url = None
        mock_result.api_key = "sk-12"
        mock_setup_wizard.return_value = mock_result
        
        with patch('builtins.print') as mock_print:
            exit_code = main(["setup"])
            
            assert exit_code == 0
            
            # Short keys should show ****
            print_calls = [str(call) for call in mock_print.call_args_list]
            api_key_call = next(call for call in print_calls if "API Key:" in call)
            assert "****" in api_key_call
    
    @patch('ai_utilities.cli.run_setup_wizard')
    def test_main_keyboard_interrupt(self, mock_setup_wizard):
        """Test handling of KeyboardInterrupt."""
        mock_setup_wizard.side_effect = KeyboardInterrupt()
        
        with patch('builtins.print') as mock_print:
            exit_code = main(["setup"])
            
            assert exit_code == 1
            mock_print.assert_any_call("\nSetup cancelled by user.")
    
    @patch('ai_utilities.cli.run_setup_wizard')
    def test_main_general_exception(self, mock_setup_wizard):
        """Test handling of general exceptions."""
        mock_setup_wizard.side_effect = Exception("Test error")
        
        with patch('builtins.print') as mock_print:
            exit_code = main(["setup"])
            
            assert exit_code == 1
            mock_print.assert_any_call("Error: Test error")
    
    def test_main_unknown_command(self):
        """Test handling of unknown commands."""
        with patch('ai_utilities.cli.create_parser') as mock_create_parser:
            mock_parser = MagicMock()
            mock_parser.parse_args.return_value = MagicMock(command="unknown")
            mock_create_parser.return_value = mock_parser
            
            with patch.object(mock_parser, 'print_help') as mock_help:
                exit_code = main(["unknown"])
                
                assert exit_code == 1
                mock_help.assert_called_once()
    
    def test_main_none_command(self):
        """Test handling when command is None."""
        with patch('ai_utilities.cli.run_setup_wizard') as mock_setup:
            mock_result = MagicMock()
            mock_result.provider = "openai"
            mock_result.model = None
            mock_result.base_url = None
            mock_result.api_key = None
            mock_setup.return_value = mock_result
            
            # Test with empty args (should default to setup)
            exit_code = main([])
            
            assert exit_code == 0
            mock_setup.assert_called_once()


class TestIntegration:
    """Integration tests for CLI functionality."""
    
    @patch('ai_utilities.cli.run_setup_wizard')
    def test_complete_setup_workflow(self, mock_setup_wizard):
        """Test complete setup workflow."""
        from ai_utilities.setup.wizard import SetupMode
        
        mock_result = MagicMock()
        mock_result.provider = "openai"
        mock_result.model = "gpt-4-turbo"
        mock_result.base_url = "https://api.openai.com/v1"
        mock_result.api_key = "sk-proj-1234567890abcdef"
        mock_setup_wizard.return_value = mock_result
        
        with patch('builtins.print') as mock_print:
            exit_code = main([
                "setup",
                "--mode", "enhanced",
                "--dotenv-path", "production.env"
            ])
            
            assert exit_code == 0
            
            # Verify wizard was called with correct parameters
            mock_setup_wizard.assert_called_once_with(
                mode=SetupMode.ENHANCED,
                dotenv_path="production.env",
                dry_run=False,
                non_interactive=False
            )
            
            # Verify output contains expected information
            print_calls = [str(call) for call in mock_print.call_args_list]
            output_text = " ".join(print_calls)
            
            assert "Setup completed successfully" in output_text
            assert "Provider: openai" in output_text
            assert "Model: gpt-4-turbo" in output_text
            assert "Base URL: https://api.openai.com/v1" in output_text
            assert "Configuration written to: production.env" in output_text
    
    def test_argv_parameter_handling(self):
        """Test that argv parameter is handled correctly."""
        with patch('ai_utilities.cli.run_setup_wizard') as mock_setup:
            mock_result = MagicMock()
            mock_result.provider = "test"
            mock_result.model = None
            mock_result.base_url = None
            mock_result.api_key = None
            mock_setup.return_value = mock_result
            
            # Test with explicit argv
            exit_code = main(["setup"])
            assert exit_code == 0
            mock_setup.assert_called_once()
            
            # Test with explicit empty argv (should default to setup)
            mock_setup.reset_mock()
            exit_code = main([])
            assert exit_code == 0
            mock_setup.assert_called_once()
    
    def test_empty_argv_defaults_to_setup(self):
        """Test that empty argv defaults to setup command."""
        with patch('ai_utilities.cli.run_setup_wizard') as mock_setup:
            mock_result = MagicMock()
            mock_result.provider = "test"
            mock_result.model = None
            mock_result.base_url = None
            mock_result.api_key = None
            mock_setup.return_value = mock_result
            
            # Empty list should default to setup
            exit_code = main([])
            assert exit_code == 0
            mock_setup.assert_called_once()
