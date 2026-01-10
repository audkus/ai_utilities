#!/usr/bin/env python3
"""
Focused Integration Tests for Tiered Setup System
Tests core functionality without complex mocking
"""

import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, 'src')

from ai_utilities.improved_setup import ImprovedSetupSystem, SetupLevel

class FocusedIntegrationTest:
    """Focused integration tests for tiered setup system"""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        self.setup = ImprovedSetupSystem()
    
    def setUp(self):
        """Set up test environment"""
        os.chdir(self.temp_dir)
        print(f"🧪 Test environment: {self.temp_dir}")
    
    def tearDown(self):
        """Clean up test environment"""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_parameter_categorization_integration(self):
        """Test parameter categorization works correctly"""
        print("🧪 Testing Parameter Categorization...")
        
        # Test Basic Setup parameters
        basic_params = self.setup._get_parameters_by_level(SetupLevel.BASIC)
        expected_basic = ["model", "temperature", "max_tokens", "timeout", "base_url", "update_check_days"]
        
        assert len(basic_params) == 6, f"Expected 6 basic params, got {len(basic_params)}"
        assert set(basic_params) == set(expected_basic), f"Basic params mismatch: {basic_params}"
        
        # Test Standard Setup includes Basic + Standard
        standard_params = self.setup._get_parameters_by_level(SetupLevel.STANDARD)
        expected_standard = expected_basic + ["cache_enabled", "cache_backend", "cache_ttl_s", "usage_scope"]
        
        assert len(standard_params) == 10, f"Expected 10 standard params, got {len(standard_params)}"
        assert set(standard_params) == set(expected_standard), f"Standard params mismatch"
        
        # Test Expert Setup includes all
        expert_params = self.setup._get_parameters_by_level(SetupLevel.EXPERT)
        assert len(expert_params) >= 10, f"Expected at least 10 expert params, got {len(expert_params)}"
        
        # Verify hierarchy
        assert set(basic_params).issubset(set(standard_params))
        assert set(standard_params).issubset(set(expert_params))
        
        print("✅ Parameter Categorization: PASSED")
    
    def test_update_check_days_parameter_integration(self):
        """Test update_check_days parameter is properly configured"""
        print("🧪 Testing update_check_days Parameter...")
        
        param = self.setup.param_registry.get_parameter("update_check_days")
        
        assert param is not None, "update_check_days parameter not found"
        assert param.name == "Update Check Frequency"
        assert param.env_var == "AI_UPDATE_CHECK_DAYS"
        assert param.default_value == 30
        assert param.value_type == int
        assert "7" in param.examples
        assert "30" in param.examples
        assert "90" in param.examples
        assert "" in param.examples  # Disable option
        
        print("✅ update_check_days Parameter: PASSED")
    
    def test_env_file_generation_integration(self):
        """Test .env file generation with setup level"""
        print("🧪 Testing .env File Generation...")
        
        # Create test data
        from ai_utilities.improved_setup import AIProvider
        providers = [self.setup.provider_registry.get_provider("openai")]
        env_vars = {"OPENAI_API_KEY": "test-key"}
        config = {
            "provider": "openai",
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 1000,
            "timeout": 60,
            "update_check_days": 30,
            "setup_level": "basic"
        }
        
        # Generate .env file
        self.setup._generate_multi_provider_env_file(providers, env_vars, config)
        
        # Verify file exists and content
        env_file = Path(self.temp_dir) / ".env"
        assert env_file.exists(), ".env file was not created"
        
        content = env_file.read_text()
        assert "# Setup Level: Basic" in content, "Setup level not found in .env file"
        assert "AI_UPDATE_CHECK_DAYS=30" in content, "update_check_days not found in .env file"
        assert "OPENAI_API_KEY=test-key" in content, "API key not found in .env file"
        assert "AI_MODEL=gpt-4" in content, "Model not found in .env file"
        
        # Verify file permissions
        file_stat = env_file.stat()
        if hasattr(file_stat, 'st_mode'):
            permissions = oct(file_stat.st_mode)[-3:]
            assert permissions == "600", f"Expected 600 permissions, got {permissions}"
        
        print("✅ .env File Generation: PASSED")
    
    def test_setup_level_enum_integration(self):
        """Test SetupLevel enum functionality"""
        print("🧪 Testing SetupLevel Enum...")
        
        # Test enum values
        assert SetupLevel.BASIC.value == "basic"
        assert SetupLevel.STANDARD.value == "standard"
        assert SetupLevel.EXPERT.value == "expert"
        
        # Test all levels exist
        levels = list(SetupLevel)
        assert len(levels) == 3
        
        # Test parameter categorization with enum
        basic_params = self.setup._get_parameters_by_level(SetupLevel.BASIC)
        standard_params = self.setup._get_parameters_by_level(SetupLevel.STANDARD)
        expert_params = self.setup._get_parameters_by_level(SetupLevel.EXPERT)
        
        assert len(basic_params) < len(standard_params) < len(expert_params)
        
        print("✅ SetupLevel Enum: PASSED")
    
    def test_provider_registry_integration(self):
        """Test provider registry functionality"""
        print("🧪 Testing Provider Registry...")
        
        registry = self.setup.provider_registry
        
        # Test provider retrieval
        openai_provider = registry.get_provider("openai")
        assert openai_provider is not None, "OpenAI provider not found"
        assert openai_provider.name == "OpenAI"
        assert openai_provider.provider_id == "openai"
        
        groq_provider = registry.get_provider("groq")
        assert groq_provider is not None, "Groq provider not found"
        assert groq_provider.name == "Groq"
        
        # Test provider list
        providers = registry.list_providers()
        assert len(providers) >= 2, "Expected at least 2 providers"
        
        # Test provider menu generation
        menu = registry.get_provider_menu()
        assert "OpenAI" in menu
        assert "Groq" in menu
        
        print("✅ Provider Registry: PASSED")
    
    def test_parameter_registry_integration(self):
        """Test parameter registry functionality"""
        print("🧪 Testing Parameter Registry...")
        
        registry = self.setup.param_registry
        
        # Test parameter retrieval
        model_param = registry.get_parameter("model")
        assert model_param is not None, "Model parameter not found"
        assert model_param.name == "AI Model"
        assert model_param.env_var == "AI_MODEL"
        
        temp_param = registry.get_parameter("temperature")
        assert temp_param is not None, "Temperature parameter not found"
        assert temp_param.value_type == float
        
        # Test parameter list
        params = registry.list_parameters()
        assert len(params) >= 6, "Expected at least 6 parameters"
        
        # Test update_check_days specifically
        update_param = registry.get_parameter("update_check_days")
        assert update_param is not None
        assert "Days between automatic checks" in update_param.description
        
        print("✅ Parameter Registry: PASSED")
    
    def test_access_functions_integration(self):
        """Test the access functions work correctly"""
        print("🧪 Testing Access Functions...")
        
        # Test that functions can be imported
        from ai_utilities.improved_setup import run_interactive_setup, run_tiered_setup
        
        # Test that functions are callable
        assert callable(run_interactive_setup)
        assert callable(run_tiered_setup)
        
        # Test setup system creation
        setup = ImprovedSetupSystem()
        assert setup is not None
        assert hasattr(setup, 'interactive_setup_with_existing')
        assert hasattr(setup, 'interactive_tiered_setup')
        assert hasattr(setup, 'load_existing_settings')
        
        print("✅ Access Functions: PASSED")
    
    def test_error_handling_integration(self):
        """Test error handling in various scenarios"""
        print("🧪 Testing Error Handling...")
        
        # Test missing parameter handling
        missing_param = self.setup.param_registry.get_parameter("nonexistent_parameter")
        assert missing_param is None, "Missing parameter should return None"
        
        # Test missing provider handling
        missing_provider = self.setup.provider_registry.get_provider("nonexistent_provider")
        assert missing_provider is None, "Missing provider should return None"
        
        # Test loading non-existent settings
        settings = self.setup.load_existing_settings()
        assert settings is None, "Non-existent settings should return None"
        
        print("✅ Error Handling: PASSED")
    
    def run_all_focused_tests(self):
        """Run all focused integration tests"""
        print("🚀 RUNNING FOCUSED INTEGRATION TESTS")
        print("=" * 50)
        
        self.setUp()
        
        test_methods = [
            self.test_parameter_categorization_integration,
            self.test_update_check_days_parameter_integration,
            self.test_env_file_generation_integration,
            self.test_setup_level_enum_integration,
            self.test_provider_registry_integration,
            self.test_parameter_registry_integration,
            self.test_access_functions_integration,
            self.test_error_handling_integration
        ]
        
        passed = 0
        failed = 0
        
        for test_method in test_methods:
            try:
                test_method()
                passed += 1
            except Exception as e:
                print(f"❌ {test_method.__name__} failed: {e}")
                failed += 1
                # Reset environment for next test
                self.setUp()
        
        self.tearDown()
        
        print(f"\n🎯 FOCUSED TEST RESULTS: {passed} passed, {failed} failed")
        
        if failed == 0:
            print("🎉 ALL FOCUSED INTEGRATION TESTS PASSED!")
            print("✅ Tiered Setup System core functionality is working correctly!")
        else:
            print(f"⚠️  {failed} tests failed - review needed")
        
        return failed == 0

if __name__ == "__main__":
    tester = FocusedIntegrationTest()
    success = tester.run_all_focused_tests()
    sys.exit(0 if success else 1)
