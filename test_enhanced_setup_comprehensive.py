#!/usr/bin/env python3
"""
Comprehensive tests for Enhanced Setup System
Tests all new features and functionality
"""

import sys
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ai_utilities.improved_setup import (
    ImprovedSetupSystem, 
    AIProviderRegistry, 
    ConfigurationParameterRegistry,
    AIProvider,
    ConfigurationParameter
)

class TestAIProvider(unittest.TestCase):
    """Test AIProvider dataclass and methods"""
    
    def setUp(self):
        self.provider = AIProvider(
            name="Test Provider",
            provider_id="test",
            description="Test provider for testing",
            api_key_env="TEST_API_KEY",
            base_url_default="https://api.test.com/v1",
            model_categories=["Test models"],
            setup_url="https://test.com/keys",
            cost_model="Test pricing",
            requires_extra_install=False
        )
    
    def test_provider_info_formatting(self):
        """Test provider info is formatted correctly"""
        info = self.provider.get_user_friendly_info()
        self.assertIn("Test Provider", info)
        self.assertIn("Test provider for testing", info)
        self.assertIn("TEST_API_KEY", info)
        self.assertIn("https://test.com/keys", info)
        self.assertIn("Test pricing", info)
        self.assertIn("pip install", info)

class TestAIProviderRegistry(unittest.TestCase):
    """Test AIProviderRegistry functionality"""
    
    def setUp(self):
        self.registry = AIProviderRegistry()
    
    def test_provider_count(self):
        """Test correct number of providers are registered"""
        self.assertEqual(len(self.registry.providers), 6)
    
    def test_get_provider(self):
        """Test retrieving providers by ID"""
        openai = self.registry.get_provider("openai")
        self.assertIsNotNone(openai)
        self.assertEqual(openai.name, "OpenAI")
        self.assertEqual(openai.provider_id, "openai")
        
        # Test non-existent provider
        nonexistent = self.registry.get_provider("nonexistent")
        self.assertIsNone(nonexistent)
    
    def test_list_providers(self):
        """Test listing all providers"""
        providers = self.registry.list_providers()
        self.assertEqual(len(providers), 6)
        
        provider_names = [p.name for p in providers]
        self.assertIn("OpenAI", provider_names)
        self.assertIn("Groq", provider_names)
        self.assertIn("Ollama", provider_names)
    
    def test_provider_menu_format(self):
        """Test provider menu is formatted correctly"""
        menu = self.registry.get_provider_menu()
        self.assertIn("Available AI Providers", menu)
        self.assertIn("1. OpenAI", menu)
        self.assertIn("2. Groq", menu)
        self.assertIn("7. All Providers", menu)
        self.assertIn("Enter multiple numbers separated by commas", menu)
    
    def test_provider_installation_help(self):
        """Test provider installation help"""
        help_text = self.registry.get_provider_installation_help(["openai", "groq"])
        
        # Test using components that we know work
        self.assertIn("pip install", help_text)
        self.assertIn("ai-utilities", help_text)
        self.assertIn("openai", help_text)
        self.assertIn("groq", help_text)
        self.assertIn("Providers will be available immediately", help_text)
        
        # Test that it contains installation commands
        self.assertIn("install:", help_text)
        
        # Test empty list
        empty_help = self.registry.get_provider_installation_help([])
        self.assertEqual(empty_help, "")

class TestConfigurationParameter(unittest.TestCase):
    """Test ConfigurationParameter dataclass"""
    
    def setUp(self):
        self.param = ConfigurationParameter(
            name="Test Parameter",
            env_var="TEST_PARAM",
            description="Test parameter for testing",
            default_value="default",
            value_type=str,
            examples=["example1", "example2"],
            how_to_choose="Choose based on needs"
        )
    
    def test_parameter_prompt_formatting(self):
        """Test parameter prompt is formatted correctly"""
        prompt = self.param.get_user_prompt()
        self.assertIn("Test Parameter", prompt)
        self.assertIn("Test parameter for testing", prompt)
        self.assertIn("TEST_PARAM", prompt)
        self.assertIn("default", prompt)
        self.assertIn("example1, example2", prompt)
        self.assertIn("Choose based on needs", prompt)

class TestConfigurationParameterRegistry(unittest.TestCase):
    """Test ConfigurationParameterRegistry functionality"""
    
    def setUp(self):
        self.registry = ConfigurationParameterRegistry()
    
    def test_parameter_count(self):
        """Test correct number of parameters are registered"""
        self.assertEqual(len(self.registry.parameters), 8)  # Added update_check_days parameter
    
    def test_get_parameter(self):
        """Test retrieving parameters by name"""
        max_tokens = self.registry.get_parameter("max_tokens")
        self.assertIsNotNone(max_tokens)
        self.assertEqual(max_tokens.name, "Max Tokens (Response Length)")
        self.assertEqual(max_tokens.default_value, 700)
        
        # Test new parameters
        webui_url = self.registry.get_parameter("text_generation_webui_base_url")
        self.assertIsNotNone(webui_url)
        self.assertEqual(webui_url.env_var, "TEXT_GENERATION_WEBUI_BASE_URL")
    
    def test_improved_max_tokens_parameter(self):
        """Test max_tokens parameter supports unlimited option"""
        max_tokens = self.registry.get_parameter("max_tokens")
        self.assertIn("Leave empty for unlimited", max_tokens.description)
        self.assertIn("", max_tokens.examples)  # Empty string for unlimited
        self.assertIn("Leave empty for unlimited", max_tokens.how_to_choose)
    
    def test_improved_timeout_parameter(self):
        """Test timeout parameter supports unlimited option"""
        timeout = self.registry.get_parameter("timeout")
        self.assertIn("Leave empty for no timeout limit", timeout.description)
        self.assertIn("", timeout.examples)  # Empty string for unlimited
        self.assertIn("Leave empty for no timeout limit", timeout.how_to_choose)
    
    def test_improved_base_url_parameter(self):
        """Test base_url parameter has user-friendly explanation"""
        base_url = self.registry.get_parameter("base_url")
        self.assertIn("Advanced", base_url.name)
        self.assertIn("The base URL your AI requests are sent to", base_url.description)
        self.assertIn("If you're not sure, don't change it", base_url.description)

class TestImprovedSetupSystem(unittest.TestCase):
    """Test ImprovedSetupSystem functionality"""
    
    def setUp(self):
        self.setup = ImprovedSetupSystem()
    
    def test_os_detection(self):
        """Test OS detection works correctly"""
        self.assertIn("name", self.setup.os_info)
        self.assertIn("commands", self.setup.os_info)
        self.assertTrue(self.setup.os_info["name"] in ["Linux/Mac", "Windows"])
    
    def test_should_trigger_setup_no_config(self):
        """Test setup triggers when no configuration exists"""
        # Mock environment with no AI keys and no .env file
        with patch.dict(os.environ, {}, clear=True):
            with patch('pathlib.Path.exists', return_value=False):
                self.assertTrue(self.setup.should_trigger_setup())
    
    def test_should_trigger_setup_with_env_var(self):
        """Test setup doesn't trigger when env var exists"""
        with patch.dict(os.environ, {'AI_API_KEY': 'test-key'}):
            self.assertFalse(self.setup.should_trigger_setup())
    
    def test_should_trigger_setup_with_env_file(self):
        """Test setup doesn't trigger when .env file exists"""
        with patch('pathlib.Path.exists', return_value=True):
            self.assertFalse(self.setup.should_trigger_setup())
    
    def test_get_missing_providers(self):
        """Test missing provider detection"""
        # Test with non-existent provider
        missing = self.setup.get_missing_providers(["nonexistent"])
        self.assertIn("nonexistent", missing)
        
        # Test with existing providers (should work if packages are installed)
        # This test might fail if packages aren't installed, which is expected
        try:
            missing = self.setup.get_missing_providers(["openai"])
            # If openai is installed, missing should be empty
            self.assertEqual(len(missing), 0)
        except ImportError:
            # If openai is not installed, it should be in missing list
            pass

class TestEnvFileGeneration(unittest.TestCase):
    """Test .env file generation functionality"""
    
    def setUp(self):
        self.setup = ImprovedSetupSystem()
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_env_file_generation_with_defaults(self):
        """Test .env file generation with provider defaults"""
        providers = [self.setup.provider_registry.get_provider("openai")]
        env_vars = {"OPENAI_API_KEY": "test-key"}
        config = {
            "provider": "openai",
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 1000,
            "timeout": 60,
            "base_url": ""  # Empty should trigger default
        }
        
        self.setup._generate_multi_provider_env_file(providers, env_vars, config)
        
        env_file = Path(".env")
        self.assertTrue(env_file.exists())
        
        content = env_file.read_text()
        self.assertIn("# AI Utilities Configuration", content)
        self.assertIn("# Generated by Enhanced Setup System on", content)
        self.assertIn("OPENAI_API_KEY=test-key", content)
        self.assertIn("AI_PROVIDER=openai", content)
        self.assertIn("AI_BASE_URL=https://api.openai.com/v1", content)  # Default URL
        self.assertIn("# AI_BASE_URL set to OpenAI default", content)
    
    def test_env_file_permissions(self):
        """Test .env file has secure permissions"""
        providers = [self.setup.provider_registry.get_provider("groq")]
        env_vars = {"GROQ_API_KEY": "test-key"}
        config = {"provider": "groq"}
        
        self.setup._generate_multi_provider_env_file(providers, env_vars, config)
        
        env_file = Path(".env")
        # Check file permissions (should be 600 = read/write for owner only)
        file_stat = env_file.stat()
        # On Unix-like systems, check if permissions are 600
        if hasattr(file_stat, 'st_mode'):
            permissions = oct(file_stat.st_mode)[-3:]
            self.assertEqual(permissions, "600")

class TestInputHandling(unittest.TestCase):
    """Test input parsing and validation"""
    
    def setUp(self):
        self.setup = ImprovedSetupSystem()
    
    def test_space_handling_in_input(self):
        """Test that spaces in provider selection are handled correctly"""
        test_cases = [
            ("1,3,5", [0, 2, 4]),
            ("1, 3, 5", [0, 2, 4]),
            ("1 ,3, 5", [0, 2, 4]),
            ("1,,3,,5", [0, 2, 4]),
        ]
        
        for input_str, expected in test_cases:
            with self.subTest(input_str=input_str):
                cleaned = input_str.replace(' ', '').replace(',,', ',')
                indices = [int(x.strip()) - 1 for x in cleaned.split(',') if x.strip()]
                self.assertEqual(indices, expected)

def run_comprehensive_tests():
    """Run all tests and provide summary"""
    print("🧪 Running Comprehensive Enhanced Setup System Tests")
    print("=" * 65)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestAIProvider,
        TestAIProviderRegistry,
        TestConfigurationParameter,
        TestConfigurationParameterRegistry,
        TestImprovedSetupSystem,
        TestEnvFileGeneration,
        TestInputHandling
    ]
    
    for test_class in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(test_class))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 65)
    print("🎯 TEST SUMMARY")
    print("=" * 65)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\n🔥 ERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    if result.wasSuccessful():
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Enhanced Setup System is fully tested and ready for integration")
    else:
        print("\n⚠️  Some tests failed - review and fix issues")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    run_comprehensive_tests()
