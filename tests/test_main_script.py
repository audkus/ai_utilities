#!/usr/bin/env python3
"""
Tests for main.py script.

Tests the main entry point functionality including:
- Command line argument parsing
- Help system
- Version information
- Feature routing
"""

import os
import sys
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

# Add scripts to path for imports
scripts_dir = os.path.join(os.path.dirname(__file__), '..', 'scripts')
sys.path.insert(0, scripts_dir)

# Add src to path for ai_utilities imports
src_dir = os.path.join(os.path.dirname(__file__), '..', 'src')
sys.path.insert(0, src_dir)


class TestMainScript:
    """Test main script functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_file = self.temp_dir / "main_config.json"
        
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_main_script_initialization(self):
        """Test main script initialization."""
        from main import MainApplication
        
        app = MainApplication()
        
        assert hasattr(app, 'version')
        assert hasattr(app, 'features')
        assert hasattr(app, 'command_parser')
        assert hasattr(app, 'help_system')
    
    def test_main_script_with_config(self):
        """Test main script with configuration file."""
        from main import MainApplication
        
        # Create test config
        test_config = {
            "version": "1.0.0",
            "default_features": ["setup", "dashboard", "examples"],
            "logging": {
                "level": "INFO",
                "file": "ai_utilities.log"
            },
            "paths": {
                "examples_dir": "examples",
                "scripts_dir": "scripts",
                "tests_dir": "tests"
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(test_config, f)
        
        app = MainApplication(config_file=str(self.config_file))
        
        assert app.version == "1.0.0"
        assert "setup" in app.default_features
        assert app.logging_config["level"] == "INFO"
    
    def test_version_display(self):
        """Test version display functionality."""
        from main import MainApplication
        
        app = MainApplication()
        version = app.get_version()
        
        assert isinstance(version, str)
        assert len(version) > 0
        assert "." in version  # Should be semantic version like "1.0.0"
    
    def test_feature_list_retrieval(self):
        """Test feature list retrieval."""
        from main import MainApplication
        
        app = MainApplication()
        features = app.get_available_features()
        
        assert isinstance(features, list)
        assert len(features) > 0
        
        for feature in features:
            assert "name" in feature
            assert "description" in feature
            assert "command" in feature
    
    @patch('main.subprocess.run')
    def test_feature_execution_setup(self, mock_run):
        """Test setup feature execution."""
        from main import MainApplication
        
        # Mock successful subprocess run
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Setup completed successfully"
        mock_run.return_value = mock_result
        
        app = MainApplication()
        result = app.execute_feature("setup", [])
        
        assert result["success"] is True
        assert result["output"] == "Setup completed successfully"
        mock_run.assert_called_once()
    
    @patch('main.subprocess.run')
    def test_feature_execution_dashboard(self, mock_run):
        """Test dashboard feature execution."""
        from main import MainApplication
        
        # Mock successful subprocess run
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Dashboard started"
        mock_run.return_value = mock_result
        
        app = MainApplication()
        result = app.execute_feature("dashboard", ["--port", "8080"])
        
        assert result["success"] is True
        assert "port" in result["command"]
        mock_run.assert_called_once()
    
    @patch('main.subprocess.run')
    def test_feature_execution_failure(self, mock_run):
        """Test feature execution with failure."""
        from main import MainApplication
        
        # Mock failed subprocess run
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Command failed"
        mock_run.return_value = mock_result
        
        app = MainApplication()
        result = app.execute_feature("nonexistent", [])
        
        assert result["success"] is False
        assert "error" in result
    
    def test_help_system(self):
        """Test help system functionality."""
        from main import MainApplication
        
        app = MainApplication()
        
        # Test general help
        general_help = app.get_help()
        assert isinstance(general_help, str)
        assert len(general_help) > 0
        assert "AI Utilities" in general_help
        
        # Test specific feature help
        feature_help = app.get_help("setup")
        assert isinstance(feature_help, str)
        assert len(feature_help) > 0
        assert "setup" in feature_help.lower()
    
    def test_command_line_parsing(self):
        """Test command line argument parsing."""
        from main import MainApplication
        
        app = MainApplication()
        
        # Test parsing setup command
        args = app.parse_args(["setup", "--interactive"])
        assert args.command == "setup"
        assert args.interactive is True
        
        # Test parsing dashboard command
        args = app.parse_args(["dashboard", "--port", "8080"])
        assert args.command == "dashboard"
        assert args.port == "8080"
        
        # Test parsing examples command
        args = app.parse_args(["examples", "--list"])
        assert args.command == "examples"
        assert args.list is True
    
    def test_config_validation(self):
        """Test configuration validation."""
        from main import MainApplication
        
        app = MainApplication()
        
        # Valid config
        valid_config = {
            "version": "1.0.0",
            "default_features": ["setup", "dashboard"],
            "logging": {"level": "INFO"}
        }
        
        result = app.validate_config(valid_config)
        assert result["valid"] is True
        assert len(result["errors"]) == 0
        
        # Invalid config
        invalid_config = {
            "version": "",  # Empty version
            "default_features": "not_a_list",  # Should be list
            "logging": {"level": "INVALID"}  # Invalid log level
        }
        
        result = app.validate_config(invalid_config)
        assert result["valid"] is False
        assert len(result["errors"]) > 0
    
    @patch('main.MainApplication.execute_feature')
    def test_run_interactive_mode(self, mock_execute):
        """Test interactive mode execution."""
        from main import MainApplication
        
        # Mock successful feature execution
        mock_execute.return_value = {"success": True, "output": "Feature executed"}
        
        app = MainApplication()
        
        # Mock user input
        with patch('builtins.input', side_effect=["setup", "exit"]):
            with patch('builtins.print') as mock_print:
                app.run_interactive_mode()
        
        mock_execute.assert_called_with("setup", [])
    
    def test_get_examples_list(self):
        """Test getting examples list."""
        from main import MainApplication
        
        app = MainApplication()
        
        # Mock examples directory
        with patch('os.listdir', return_value=[
            "getting_started.py",
            "audio_generation_demo.py",
            "setup_examples.py"
        ]):
            examples = app.get_examples_list()
        
        assert isinstance(examples, list)
        assert len(examples) == 3
        assert "getting_started.py" in examples
    
    @patch('main.subprocess.run')
    def test_run_example(self, mock_run):
        """Test running an example."""
        from main import MainApplication
        
        # Mock successful example execution
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Example output"
        mock_run.return_value = mock_result
        
        app = MainApplication()
        result = app.run_example("getting_started.py")
        
        assert result["success"] is True
        assert "Example output" in result["output"]
        mock_run.assert_called_once()
    
    def test_environment_check(self):
        """Test environment check functionality."""
        from main import MainApplication
        
        app = MainApplication()
        
        # Mock environment checks
        with patch('sys.version_info', (3, 11, 0)):
            with patch('os.path.exists', return_value=True):
                env_check = app.check_environment()
        
        assert "python_version" in env_check
        assert "dependencies" in env_check
        assert "paths" in env_check
        assert env_check["python_version"]["valid"] is True
    
    @patch('main.MainApplication.execute_feature')
    @patch('main.MainApplication.parse_args')
    def test_main_entry_point(self, mock_parse, mock_execute):
        """Test main entry point."""
        from main import main
        
        # Mock argument parsing
        mock_args = Mock()
        mock_args.command = "setup"
        mock_args.interactive = False
        mock_parse.return_value = mock_args
        
        # Mock feature execution
        mock_execute.return_value = {"success": True}
        
        with patch('sys.argv', ['main.py', 'setup']):
            main()
        
        mock_parse.assert_called_once()
        mock_execute.assert_called_once_with("setup", [])
    
    def test_error_handling(self):
        """Test error handling in main application."""
        from main import MainApplication
        
        app = MainApplication()
        
        # Test handling unknown command
        result = app.execute_feature("unknown_command", [])
        assert result["success"] is False
        assert "error" in result
        
        # Test handling invalid arguments
        with patch('builtins.print') as mock_print:
            try:
                app.parse_args(["invalid_command", "--invalid-flag"])
            except SystemExit:
                pass  # argparse exits on invalid args
    
    def test_logging_configuration(self):
        """Test logging configuration."""
        from main import MainApplication
        
        # Test with default logging config
        app = MainApplication()
        app.setup_logging()
        
        # Should not raise an exception
        assert True
        
        # Test with custom logging config
        custom_config = {
            "level": "DEBUG",
            "file": str(self.temp_dir / "test.log"),
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
        
        app = MainApplication()
        app.logging_config = custom_config
        app.setup_logging()
        
        # Check if log file was created
        log_file = self.temp_dir / "test.log"
        assert log_file.exists()
    
    def test_plugin_system(self):
        """Test plugin system functionality."""
        from main import MainApplication
        
        app = MainApplication()
        
        # Test loading plugins (mock)
        with patch('os.listdir', return_value=["plugin1.py", "plugin2.py"]):
            with patch('importlib.import_module') as mock_import:
                mock_plugin = Mock()
                mock_plugin.register = Mock()
                mock_import.return_value = mock_plugin
                
                plugins = app.load_plugins()
        
        assert isinstance(plugins, list)
        assert mock_import.call_count == 2
    
    def test_status_reporting(self):
        """Test status reporting functionality."""
        from main import MainApplication
        
        app = MainApplication()
        
        # Mock status data
        with patch('platform.python_version', return_value="3.11.0"):
            with patch('os.getcwd', return_value="/test/path"):
                status = app.get_status()
        
        assert "version" in status
        assert "environment" in status
        assert "features" in status
        assert "uptime" in status
        
        assert status["environment"]["python_version"] == "3.11.0"
        assert status["environment"]["working_directory"] == "/test/path"


class TestMainCLI:
    """Test main script command line interface."""
    
    @patch('main.MainApplication.run_interactive_mode')
    def test_cli_interactive_mode(self, mock_interactive):
        """Test CLI interactive mode."""
        from main import main
        
        with patch('sys.argv', ['main.py', '--interactive']):
            main()
        
        mock_interactive.assert_called_once()
    
    @patch('main.MainApplication.execute_feature')
    def test_cli_feature_command(self, mock_execute):
        """Test CLI feature command."""
        from main import main
        
        with patch('sys.argv', ['main.py', 'setup']):
            main()
        
        mock_execute.assert_called_once()
    
    @patch('main.MainApplication.get_help')
    def test_cli_help_command(self, mock_help):
        """Test CLI help command."""
        from main import main
        
        mock_help.return_value = "Help content"
        
        with patch('sys.argv', ['main.py', '--help']):
            try:
                main()
            except SystemExit:
                pass  # Help command exits with 0
        
        mock_help.assert_called_once()
    
    @patch('main.MainApplication.get_version')
    def test_cli_version_command(self, mock_version):
        """Test CLI version command."""
        from main import main
        
        mock_version.return_value = "1.0.0"
        
        with patch('sys.argv', ['main.py', '--version']):
            try:
                main()
            except SystemExit:
                pass  # Version command exits with 0
        
        mock_version.assert_called_once()
    
    @patch('main.MainApplication.run_example')
    def test_cli_examples_command(self, mock_run_example):
        """Test CLI examples command."""
        from main import main
        
        with patch('sys.argv', ['main.py', 'examples', '--run', 'getting_started.py']):
            main()
        
        mock_run_example.assert_called_once_with("getting_started.py")
    
    @patch('main.MainApplication.check_environment')
    def test_cli_check_command(self, mock_check):
        """Test CLI environment check command."""
        from main import main
        
        mock_check.return_value = {"python_version": {"valid": True}}
        
        with patch('sys.argv', ['main.py', '--check']):
            main()
        
        mock_check.assert_called_once()
    
    def test_cli_invalid_command(self):
        """Test CLI with invalid command."""
        from main import main
        
        with patch('sys.argv', ['main.py', 'invalid_command']):
            with patch('builtins.print') as mock_print:
                try:
                    main()
                except SystemExit:
                    pass  # Invalid command exits with error
        
        # Should print error message
        mock_print.assert_called()
    
    def test_cli_no_arguments(self):
        """Test CLI with no arguments."""
        from main import main
        
        with patch('sys.argv', ['main.py']):
            with patch('main.MainApplication.run_interactive_mode') as mock_interactive:
                main()
        
        # Should default to interactive mode
        mock_interactive.assert_called_once()
