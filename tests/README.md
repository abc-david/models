# Models Service Tests

This directory contains tests for the Models Service, which is responsible for centralizing model definitions, validation, and schema handling across the Content Generator application.

## Running the Tests

Tests use the pytest framework. To run all tests:

```bash
pytest services/models/tests/
```

To run a specific test file:

```bash
pytest services/models/tests/test_model_validator.py
```

## Test Organization

- `test_base_model.py` - Tests for base model classes
- `test_model_registry.py` - Tests for model registry
- `test_model_validator.py` - Tests for model validation
- `test_db_schema_inspector.py` - Tests for database schema inspection
- `test_model_registrar.py` - Tests for the model registrar (database integration)

## Model Registrar Tests

The `test_model_registrar.py` file includes tests for the `ModelRegistrar` class, which is responsible for:

1. Validating model definitions against expected patterns
2. Registering models in the database
3. Retrieving model definitions from the database
4. Checking for existing models before inserting new ones
5. Updating existing models

The tests cover validation of model definitions, checking for the presence of required keys, validating field structures, and ensuring proper database operations for inserting and updating models.

## Test Fixtures

Common test fixtures are defined at the module level, including:

- `valid_model_definition` - A sample valid model definition for testing
- `invalid_model_definition` - An invalid model definition for negative testing
- `mock_db_connector` - A mock database connector for testing database operations

## Mock Database Connector

Database operations are tested using mock objects to avoid requiring an actual database connection. The `mock_db_connector` fixture creates an `AsyncMock` for database methods, allowing tests to verify that correct SQL queries are being executed without actually connecting to a database.

## Test Coverage

The test suite currently covers:

- Type validation for basic types (string, int, float, boolean, etc.)
- Type validation for complex types (List, Dict, Union, Optional)
- Model validation against schema definitions
- Partial validation of data against schemas
- Schema conversion between different formats

## Writing New Tests

When writing new tests for the Models Service, follow these guidelines:

1. Create a new test file with a descriptive name (e.g., `test_model_registry.py`)
2. Use appropriate test class and function names that describe what is being tested
3. Include docstrings that explain what each test is checking
4. Use assertions that verify both valid and invalid cases
5. Mock external dependencies as needed

### Example Test

Here's an example of a test for the `ModelRegistry` class:

```python
import pytest
from services.models.core import ModelRegistry, BaseModel, FieldDefinition

class TestModel(BaseModel):
    """Test model implementation."""
    
    model_name = "test_model"
    
    @classmethod
    def get_fields(cls):
        return {
            "name": FieldDefinition("name", "str", True),
            "age": FieldDefinition("age", "int", True)
        }

class TestModelRegistry:
    """Tests for the ModelRegistry class."""
    
    def test_register_model(self):
        """Test registering a model with the registry."""
        # Clear registry for testing
        ModelRegistry._models = {}
        ModelRegistry._schemas = {}
        
        # Register a model
        ModelRegistry.register_model(TestModel)
        
        # Verify model is registered
        assert "test_model" in ModelRegistry._models
        assert ModelRegistry._models["test_model"] == TestModel
        
    def test_get_model(self):
        """Test retrieving a model from the registry."""
        # Clear registry for testing
        ModelRegistry._models = {}
        ModelRegistry._schemas = {}
        
        # Register a model
        ModelRegistry.register_model(TestModel)
        
        # Get the model
        model = ModelRegistry.get_model("test_model")
        
        # Verify model is correct
        assert model == TestModel
        assert model.model_name == "test_model"
``` 