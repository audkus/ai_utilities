"""Tests for ai_utilities.demo module."""

import pytest

from ai_utilities.demo import DemoModel, DemoModelDiscovery


class TestDemoModel:
    """Test DemoModel dataclass."""

    def test_demo_model_creation_minimal(self):
        """Test creating DemoModel with minimal required fields."""
        demo_model = DemoModel(
            id="gpt-4o",
            name="GPT-4o",
            provider="openai",
            capabilities=["text", "json"]
        )
        
        assert demo_model.id == "gpt-4o"
        assert demo_model.name == "GPT-4o"
        assert demo_model.provider == "openai"
        assert demo_model.capabilities == ["text", "json"]
        assert demo_model.context_length is None
        assert demo_model.pricing is None

    def test_demo_model_creation_with_all_fields(self):
        """Test creating DemoModel with all fields."""
        pricing = {"prompt": 0.005, "completion": 0.015}
        demo_model = DemoModel(
            id="gpt-4o",
            name="GPT-4o",
            provider="openai",
            capabilities=["text", "json", "function_calling", "vision"],
            context_length=128000,
            pricing=pricing
        )
        
        assert demo_model.id == "gpt-4o"
        assert demo_model.name == "GPT-4o"
        assert demo_model.provider == "openai"
        assert demo_model.capabilities == ["text", "json", "function_calling", "vision"]
        assert demo_model.context_length == 128000
        assert demo_model.pricing == pricing

    def test_demo_model_equality(self):
        """Test DemoModel equality comparison."""
        model1 = DemoModel(
            id="gpt-4o",
            name="GPT-4o",
            provider="openai",
            capabilities=["text", "json"]
        )
        
        model2 = DemoModel(
            id="gpt-4o",
            name="GPT-4o",
            provider="openai",
            capabilities=["text", "json"]
        )
        
        model3 = DemoModel(
            id="gpt-3.5-turbo",
            name="GPT-3.5 Turbo",
            provider="openai",
            capabilities=["text", "json"]
        )
        
        assert model1 == model2
        assert model1 != model3

    def test_demo_model_immutability(self):
        """Test that DemoModel instances can be modified (dataclasses are mutable by default)."""
        demo_model = DemoModel(
            id="gpt-4o",
            name="GPT-4o",
            provider="openai",
            capabilities=["text"]
        )
        
        # Dataclasses are mutable by default
        demo_model.context_length = 128000
        demo_model.pricing = {"prompt": 0.01}
        
        assert demo_model.context_length == 128000
        assert demo_model.pricing == {"prompt": 0.01}

    def test_demo_model_string_representation(self):
        """Test DemoModel string representation."""
        demo_model = DemoModel(
            id="gpt-4o",
            name="GPT-4o",
            provider="openai",
            capabilities=["text", "json"]
        )
        
        repr_str = repr(demo_model)
        assert "DemoModel" in repr_str
        assert "gpt-4o" in repr_str
        assert "GPT-4o" in repr_str


class TestDemoModelDiscovery:
    """Test DemoModelDiscovery class."""

    def test_demo_model_discovery_initialization(self):
        """Test DemoModelDiscovery initialization."""
        discovery = DemoModelDiscovery()
        
        assert discovery is not None
        assert hasattr(discovery, '_demo_models')
        assert isinstance(discovery._demo_models, dict)

    def test_demo_model_discovery_has_models(self):
        """Test that DemoModelDiscovery has demo models."""
        discovery = DemoModelDiscovery()
        
        # Should have models for at least openai
        assert "openai" in discovery._demo_models
        assert len(discovery._demo_models["openai"]) > 0
        
        # Check that models are DemoModel instances
        for model in discovery._demo_models["openai"]:
            assert isinstance(model, DemoModel)

    def test_demo_model_discovery_openai_models(self):
        """Test OpenAI demo models structure."""
        discovery = DemoModelDiscovery()
        openai_models = discovery._demo_models["openai"]
        
        # Should have expected models
        model_ids = [model.id for model in openai_models]
        expected_ids = ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"]
        
        for expected_id in expected_ids:
            assert expected_id in model_ids
        
        # Check model structure
        gpt4_model = next(m for m in openai_models if m.id == "gpt-4o")
        assert gpt4_model.name == "GPT-4o"
        assert gpt4_model.provider == "openai"
        assert "text" in gpt4_model.capabilities
        assert "json" in gpt4_model.capabilities
        assert "function_calling" in gpt4_model.capabilities
        assert "vision" in gpt4_model.capabilities
        assert gpt4_model.context_length == 128000
        assert gpt4_model.pricing is not None
        assert "prompt" in gpt4_model.pricing
        assert "completion" in gpt4_model.pricing

    def test_demo_model_discovery_gpt35_model(self):
        """Test GPT-3.5 Turbo demo model."""
        discovery = DemoModelDiscovery()
        openai_models = discovery._demo_models["openai"]
        
        gpt35_model = next(m for m in openai_models if m.id == "gpt-3.5-turbo")
        assert gpt35_model.name == "GPT-3.5 Turbo"
        assert gpt35_model.provider == "openai"
        assert "text" in gpt35_model.capabilities
        assert "json" in gpt35_model.capabilities
        assert "function_calling" in gpt35_model.capabilities
        assert "vision" not in gpt35_model.capabilities  # GPT-3.5 doesn't have vision
        assert gpt35_model.context_length == 16384
        assert gpt35_model.pricing is not None

    def test_demo_model_discovery_gpt4_mini_model(self):
        """Test GPT-4o Mini demo model."""
        discovery = DemoModelDiscovery()
        openai_models = discovery._demo_models["openai"]
        
        gpt4_mini_model = next(m for m in openai_models if m.id == "gpt-4o-mini")
        assert gpt4_mini_model.name == "GPT-4o Mini"
        assert gpt4_mini_model.provider == "openai"
        assert "text" in gpt4_mini_model.capabilities
        assert "json" in gpt4_mini_model.capabilities
        assert "function_calling" in gpt4_mini_model.capabilities
        assert "vision" not in gpt4_mini_model.capabilities  # Mini doesn't have vision
        assert gpt4_mini_model.context_length == 128000
        assert gpt4_mini_model.pricing is not None

    def test_demo_model_discovery_pricing_structure(self):
        """Test that pricing information is properly structured."""
        discovery = DemoModelDiscovery()
        openai_models = discovery._demo_models["openai"]
        
        for model in openai_models:
            assert model.pricing is not None
            assert isinstance(model.pricing, dict)
            assert "prompt" in model.pricing
            assert "completion" in model.pricing
            assert isinstance(model.pricing["prompt"], (int, float))
            assert isinstance(model.pricing["completion"], (int, float))
            assert model.pricing["prompt"] >= 0
            assert model.pricing["completion"] >= 0

    def test_demo_model_discovery_capabilities_structure(self):
        """Test that capabilities are properly structured."""
        discovery = DemoModelDiscovery()
        openai_models = discovery._demo_models["openai"]
        
        for model in openai_models:
            assert isinstance(model.capabilities, list)
            assert len(model.capabilities) > 0
            assert all(isinstance(cap, str) for cap in model.capabilities)
            
            # Check for expected capabilities
            common_capabilities = ["text", "json", "function_calling"]
            for cap in common_capabilities:
                if cap in ["text", "json"]:  # All models should have these
                    assert cap in model.capabilities

    def test_demo_model_discovery_context_lengths(self):
        """Test that context lengths are reasonable."""
        discovery = DemoModelDiscovery()
        openai_models = discovery._demo_models["openai"]
        
        for model in openai_models:
            if model.context_length is not None:
                assert isinstance(model.context_length, int)
                assert model.context_length > 0
                assert model.context_length <= 1000000  # Reasonable upper bound

    def test_demo_model_discovery_no_real_api_calls(self):
        """Test that DemoModelDiscovery doesn't make real API calls."""
        # This test ensures the demo module is truly demo-only
        discovery = DemoModelDiscovery()
        
        # Should work without any network calls or API keys
        assert discovery._demo_models is not None
        assert len(discovery._demo_models["openai"]) == 3
        
        # All data should be static/demo data
        for model in discovery._demo_models["openai"]:
            assert isinstance(model, DemoModel)
            assert model.provider == "openai"

    def test_demo_module_import_smoke_test(self):
        """Test that demo module can be imported without errors."""
        # This is a smoke test to ensure the demo module doesn't have import issues
        import ai_utilities.demo
        
        assert hasattr(ai_utilities.demo, 'DemoModel')
        assert hasattr(ai_utilities.demo, 'DemoModelDiscovery')
        
        # Should be able to create instances
        demo_model = ai_utilities.demo.DemoModel(
            id="test",
            name="Test Model",
            provider="test",
            capabilities=["text"]
        )
        assert demo_model.id == "test"
        
        discovery = ai_utilities.demo.DemoModelDiscovery()
        assert discovery is not None
