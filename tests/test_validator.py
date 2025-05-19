"""
Tests for the ModelValidator class.
"""

import pytest
from datetime import datetime
from typing import Dict, Any, List

from services.models.validation import ModelValidator, ValidationResult
from services.models.validation.type_validators import TypeValidator


class TestTypeValidator:
    """Tests for the TypeValidator class."""
    
    def test_validate_string(self):
        """Test string type validation."""
        validator = TypeValidator()
        
        # Valid string
        is_valid, error = validator.validate_type("test", "str")
        assert is_valid is True
        assert error == ""
        
        # Invalid string
        is_valid, error = validator.validate_type(123, "str")
        assert is_valid is False
        assert "expected string" in error
    
    def test_validate_int(self):
        """Test integer type validation."""
        validator = TypeValidator()
        
        # Valid int
        is_valid, error = validator.validate_type(123, "int")
        assert is_valid is True
        assert error == ""
        
        # Invalid int
        is_valid, error = validator.validate_type("test", "int")
        assert is_valid is False
        assert "expected integer" in error
        
        # Boolean is not an int
        is_valid, error = validator.validate_type(True, "int")
        assert is_valid is False
        assert "expected integer" in error
    
    def test_validate_float(self):
        """Test float type validation."""
        validator = TypeValidator()
        
        # Valid float
        is_valid, error = validator.validate_type(123.45, "float")
        assert is_valid is True
        assert error == ""
        
        # Int is also valid
        is_valid, error = validator.validate_type(123, "float")
        assert is_valid is True
        assert error == ""
        
        # Invalid float
        is_valid, error = validator.validate_type("test", "float")
        assert is_valid is False
        assert "expected number" in error
    
    def test_validate_bool(self):
        """Test boolean type validation."""
        validator = TypeValidator()
        
        # Valid boolean
        is_valid, error = validator.validate_type(True, "bool")
        assert is_valid is True
        assert error == ""
        
        # Invalid boolean
        is_valid, error = validator.validate_type(1, "bool")
        assert is_valid is False
        assert "expected boolean" in error
    
    def test_validate_datetime(self):
        """Test datetime type validation."""
        validator = TypeValidator()
        
        # Valid datetime as object
        is_valid, error = validator.validate_type(datetime.now(), "datetime")
        assert is_valid is True
        assert error == ""
        
        # Valid datetime as string
        is_valid, error = validator.validate_type("2023-01-01T12:00:00", "datetime")
        assert is_valid is True
        assert error == ""
        
        # Invalid datetime format
        is_valid, error = validator.validate_type("not a date", "datetime")
        assert is_valid is False
        assert "invalid datetime format" in error
        
        # Invalid datetime type
        is_valid, error = validator.validate_type(123, "datetime")
        assert is_valid is False
        assert "expected datetime" in error
    
    def test_validate_list(self):
        """Test list type validation."""
        validator = TypeValidator()
        
        # Valid list of strings
        is_valid, error = validator.validate_type(["a", "b", "c"], "List[str]")
        assert is_valid is True
        assert error == ""
        
        # Invalid list (not a list)
        is_valid, error = validator.validate_type("not a list", "List[str]")
        assert is_valid is False
        assert "expected list" in error
        
        # Invalid list contents
        is_valid, error = validator.validate_type(["a", 123, "c"], "List[str]")
        assert is_valid is False
        assert "invalid item" in error
    
    def test_validate_dict(self):
        """Test dictionary type validation."""
        validator = TypeValidator()
        
        # Valid dict
        is_valid, error = validator.validate_type({"a": 1, "b": 2}, "Dict[str, int]")
        assert is_valid is True
        assert error == ""
        
        # Invalid dict (not a dict)
        is_valid, error = validator.validate_type("not a dict", "Dict[str, int]")
        assert is_valid is False
        assert "expected dictionary" in error
        
        # Invalid key type
        is_valid, error = validator.validate_type({1: 1, 2: 2}, "Dict[str, int]")
        assert is_valid is False
        assert "invalid key" in error
        
        # Invalid value type
        is_valid, error = validator.validate_type({"a": "1", "b": "2"}, "Dict[str, int]")
        assert is_valid is False
        assert "invalid value" in error
    
    def test_validate_union(self):
        """Test union type validation."""
        validator = TypeValidator()
        
        # Union of str and int
        is_valid, error = validator.validate_type("test", "Union[str, int]")
        assert is_valid is True
        assert error == ""
        
        is_valid, error = validator.validate_type(123, "Union[str, int]")
        assert is_valid is True
        assert error == ""
        
        # Invalid for union
        is_valid, error = validator.validate_type(True, "Union[str, int]")
        assert is_valid is False
        assert "value did not match any of the expected types" in error
    
    def test_validate_optional(self):
        """Test optional type validation."""
        validator = TypeValidator()
        
        # Optional string
        is_valid, error = validator.validate_type("test", "Optional[str]")
        assert is_valid is True
        assert error == ""
        
        is_valid, error = validator.validate_type(None, "Optional[str]")
        assert is_valid is True
        assert error == ""
        
        # Invalid for optional string
        is_valid, error = validator.validate_type(123, "Optional[str]")
        assert is_valid is False
        assert "expected string" in error


class TestModelValidator:
    """Tests for the ModelValidator class."""
    
    def test_validate_against_model(self):
        """Test validation against a model schema."""
        validator = ModelValidator()
        
        # Create a test model schema
        model_schema = {
            "model_name": "TestModel",
            "fields": {
                "name": {
                    "name": "name",
                    "type": "str",
                    "required": True
                },
                "age": {
                    "name": "age",
                    "type": "int",
                    "required": True
                },
                "email": {
                    "name": "email",
                    "type": "str",
                    "required": False,
                    "args": {
                        "default": None
                    }
                }
            }
        }
        
        # Valid data
        data = {
            "name": "Test User",
            "age": 30,
            "email": "test@example.com"
        }
        
        result = validator.validate_against_model(data, model_schema)
        assert result.is_valid is True
        assert result.errors == []
        assert result.validated_data == data
        
        # Missing required field
        data = {
            "name": "Test User"
        }
        
        result = validator.validate_against_model(data, model_schema)
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "Missing required field" in result.errors[0]["message"]
        
        # Wrong type
        data = {
            "name": "Test User",
            "age": "thirty",
            "email": "test@example.com"
        }
        
        result = validator.validate_against_model(data, model_schema)
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "Invalid type for age" in result.errors[0]["message"]
    
    def test_partial_validation(self):
        """Test partial validation (missing fields allowed)."""
        validator = ModelValidator()
        
        # Create a test model schema
        model_schema = {
            "model_name": "TestModel",
            "fields": {
                "name": {
                    "name": "name",
                    "type": "str",
                    "required": True
                },
                "age": {
                    "name": "age",
                    "type": "int",
                    "required": True
                }
            }
        }
        
        # Partial data (missing required field, but partial=True)
        data = {
            "name": "Test User"
        }
        
        result = validator.validate_against_model(data, model_schema, partial=True)
        assert result.is_valid is True
        assert result.errors == []
        assert result.validated_data == data 