"""Tests for ask_json and ask_typed methods."""

import pytest
import sys
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, ValidationError

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_utilities import AiClient
from ai_utilities.json_parsing import JsonParseError
from tests.fake_provider import FakeProvider


class PersonModel(BaseModel):
    """Simple test model for typed responses."""
    name: str
    age: int
    email: Optional[str] = None


class TestAskJson:
    """Test the ask_json method with robust parsing."""
    
    def test_ask_json_with_valid_json(self):
        """Test ask_json with valid JSON response."""
        fake_provider = FakeProvider([
            '{"name": "Alice", "age": 30}',
            "This is text response"
        ])
        client = AiClient(provider=fake_provider)
        
        result = client.ask_json("Create a person")
        assert isinstance(result, dict)
        assert result["name"] == "Alice"
        assert result["age"] == 30
    
    def test_ask_json_with_json_in_code_fences(self):
        """Test ask_json with JSON wrapped in code fences."""
        fake_provider = FakeProvider([
            '```json\n{"name": "Bob", "age": 25}\n```',
            "Text response"
        ])
        client = AiClient(provider=fake_provider)
        
        result = client.ask_json("Create a person")
        assert isinstance(result, dict)
        assert result["name"] == "Bob"
        assert result["age"] == 25
    
    def test_ask_json_with_surrounding_text(self):
        """Test ask_json with JSON surrounded by text."""
        fake_provider = FakeProvider([
            'Here is the result: {"name": "Charlie", "age": 35} - End of response.',
            "Text response"
        ])
        client = AiClient(provider=fake_provider)
        
        result = client.ask_json("Create a person")
        assert isinstance(result, dict)
        assert result["name"] == "Charlie"
        assert result["age"] == 35
    
    def test_ask_json_with_array_response(self):
        """Test ask_json with JSON array response."""
        fake_provider = FakeProvider([
            '["red", "blue", "green"]',
            "Text response"
        ])
        client = AiClient(provider=fake_provider)
        
        result = client.ask_json("List colors")
        assert isinstance(result, list)
        assert result == ["red", "blue", "green"]
    
    def test_ask_json_repair_success(self):
        """Test ask_json repair mechanism succeeds on second attempt."""
        fake_provider = FakeProvider([
            '{"name": "Alice", "age": 30',  # Missing closing brace
            '{"name": "Alice", "age": 30}'  # Fixed JSON
        ])
        client = AiClient(provider=fake_provider)
        
        result = client.ask_json("Create a person", max_repairs=1)
        assert isinstance(result, dict)
        assert result["name"] == "Alice"
        assert result["age"] == 30
    
    def test_ask_json_repair_failure(self):
        """Test ask_json repair mechanism fails after max attempts."""
        fake_provider = FakeProvider([
            '{"name": "Alice", "age": 30',  # Missing closing brace
            '{"name": "Alice", "age": 30',  # Still broken
            '{"name": "Alice", "age": 30'   # Still broken
        ])
        client = AiClient(provider=fake_provider)
        
        with pytest.raises(JsonParseError) as exc_info:
            client.ask_json("Create a person", max_repairs=2)
        
        assert "Failed to parse JSON after 3 attempts" in str(exc_info.value)
    
    def test_ask_json_no_repairs(self):
        """Test ask_json with max_repairs=0 fails immediately."""
        fake_provider = FakeProvider([
            '{"name": "Alice", "age": 30'  # Broken JSON
        ])
        client = AiClient(provider=fake_provider)
        
        with pytest.raises(JsonParseError):
            client.ask_json("Create a person", max_repairs=0)


class TestAskTyped:
    """Test the ask_typed method with Pydantic validation."""
    
    def test_ask_typed_success(self):
        """Test ask_typed with valid response matching schema."""
        fake_provider = FakeProvider([
            '{"name": "Alice", "age": 30, "email": "alice@example.com"}',
            "Text response"
        ])
        client = AiClient(provider=fake_provider)
        
        result = client.ask_typed("Create a person", PersonModel)
        assert isinstance(result, PersonModel)
        assert result.name == "Alice"
        assert result.age == 30
        assert result.email == "alice@example.com"
    
    def test_ask_typed_with_optional_field_missing(self):
        """Test ask_typed with optional field not provided."""
        fake_provider = FakeProvider([
            '{"name": "Bob", "age": 25}',
            "Text response"
        ])
        client = AiClient(provider=fake_provider)
        
        result = client.ask_typed("Create a person", PersonModel)
        assert isinstance(result, PersonModel)
        assert result.name == "Bob"
        assert result.age == 25
        assert result.email is None
    
    def test_ask_typed_validation_error(self):
        """Test ask_typed raises ValidationError for invalid schema."""
        fake_provider = FakeProvider([
            '{"name": "Charlie", "age": "not_a_number"}',  # Invalid age type
            "Text response"
        ])
        client = AiClient(provider=fake_provider)
        
        with pytest.raises(ValidationError):
            client.ask_typed("Create a person", PersonModel)
    
    def test_ask_typed_missing_required_field(self):
        """Test ask_typed raises ValidationError for missing required field."""
        fake_provider = FakeProvider([
            '{"name": "David"}',  # Missing required age field
            "Text response"
        ])
        client = AiClient(provider=fake_provider)
        
        with pytest.raises(ValidationError):
            client.ask_typed("Create a person", PersonModel)
    
    def test_ask_typed_with_repair_success(self):
        """Test ask_typed succeeds after JSON repair."""
        fake_provider = FakeProvider([
            '{"name": "Eve", "age": 28',  # Missing closing brace
            '{"name": "Eve", "age": 28}',  # Fixed JSON
            "Text response"
        ])
        client = AiClient(provider=fake_provider)
        
        result = client.ask_typed("Create a person", PersonModel, max_repairs=1)
        assert isinstance(result, PersonModel)
        assert result.name == "Eve"
        assert result.age == 28
    
    def test_ask_typed_with_kwargs(self):
        """Test ask_typed passes through kwargs correctly."""
        fake_provider = FakeProvider([
            '{"name": "Frank", "age": 32}',
            "Text response"
        ])
        client = AiClient(provider=fake_provider)
        
        result = client.ask_typed(
            "Create a person", 
            PersonModel, 
            temperature=0.5,
            model="test-model"
        )
        
        # Check that kwargs were passed to provider
        assert fake_provider.last_kwargs["temperature"] == 0.5
        assert fake_provider.last_kwargs["model"] == "test-model"
        
        # Check result
        assert isinstance(result, PersonModel)
        assert result.name == "Frank"
        assert result.age == 32


class TestComplexModels:
    """Test ask_typed with more complex Pydantic models."""
    
    class Address(BaseModel):
        street: str
        city: str
        zipcode: str
    
    class PersonWithAddress(BaseModel):
        name: str
        age: int
        address: "TestComplexModels.Address"
    
    def test_nested_model_validation(self):
        """Test ask_typed with nested Pydantic models."""
        fake_provider = FakeProvider([
            '{"name": "Grace", "age": 30, "address": {"street": "123 Main St", "city": "Springfield", "zipcode": "12345"}}',
            "Text response"
        ])
        client = AiClient(provider=fake_provider)
        
        result = client.ask_typed("Create a person with address", self.PersonWithAddress)
        assert isinstance(result, self.PersonWithAddress)
        assert result.name == "Grace"
        assert result.age == 30
        assert isinstance(result.address, self.Address)
        assert result.address.city == "Springfield"
