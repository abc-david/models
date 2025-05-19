"""
Test module for the ModelRegistrar utility.
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.models.utils.model_registrar import ModelRegistrar


@pytest.fixture
def valid_model_definition():
    """Return a valid model definition for testing."""
    return {
        "name": "TestModel",
        "fields": {
            "title": {
                "type": "str",
                "args": {
                    "description": "The test title"
                }
            },
            "content": {
                "type": "str",
                "args": {
                    "description": "Main test content"
                }
            }
        },
        "metadata_schema": {
            "required": ["content_type", "tags"],
            "recommended": ["difficulty_level"]
        },
        "validators": [
            {
                "name": "title_not_empty",
                "fields": ["title"],
                "pre": True,
                "code": "def title_not_empty(cls, v):\n    if not v.strip():\n        raise ValueError('Title cannot be empty')\n    return v"
            }
        ]
    }


@pytest.fixture
def invalid_model_definition():
    """Return an invalid model definition missing required keys."""
    return {
        "fields": {}  # Missing "name" key
    }


class TestModelRegistrar:
    """Test cases for the ModelRegistrar class."""
    
    @pytest.fixture
    def mock_db_connector(self):
        """Create a mock DB connector."""
        mock = MagicMock()
        mock.fetchone = AsyncMock()
        mock.fetch = AsyncMock()
        return mock
    
    @pytest.fixture
    def registrar(self, mock_db_connector):
        """Create a ModelRegistrar instance with mocked DB connector."""
        return ModelRegistrar(db_connector=mock_db_connector)
    
    def test_init(self):
        """Test initializing the registrar."""
        with patch('services.models.utils.model_registrar.DBConnector') as mock_connector:
            registrar = ModelRegistrar()
            assert registrar.db_connector == mock_connector.return_value
    
    def test_validate_model_definition_valid(self, registrar, valid_model_definition):
        """Test validating a valid model definition."""
        # This should not raise an exception
        registrar._validate_model_definition(valid_model_definition)
    
    def test_validate_model_definition_invalid(self, registrar, invalid_model_definition):
        """Test validating an invalid model definition."""
        with pytest.raises(ValueError) as excinfo:
            registrar._validate_model_definition(invalid_model_definition)
        assert "Missing required keys" in str(excinfo.value)
    
    def test_validate_model_definition_invalid_fields(self, registrar):
        """Test validating a definition with invalid fields."""
        invalid_def = {
            "name": "TestModel",
            "fields": {
                "title": "string"  # Not a dictionary
            }
        }
        with pytest.raises(ValueError) as excinfo:
            registrar._validate_model_definition(invalid_def)
        assert "must be a dictionary" in str(excinfo.value)
    
    def test_validate_model_definition_missing_field_keys(self, registrar):
        """Test validating a definition with fields missing required keys."""
        invalid_def = {
            "name": "TestModel",
            "fields": {
                "title": {
                    # Missing "type" key
                    "args": {
                        "description": "The test title"
                    }
                }
            }
        }
        with pytest.raises(ValueError) as excinfo:
            registrar._validate_model_definition(invalid_def)
        assert "Missing required keys in field" in str(excinfo.value)
    
    def test_validate_model_definition_invalid_validators(self, registrar):
        """Test validating a definition with invalid validators."""
        invalid_def = {
            "name": "TestModel",
            "fields": {
                "title": {
                    "type": "str"
                }
            },
            "validators": "not a list"  # Not a list
        }
        with pytest.raises(ValueError) as excinfo:
            registrar._validate_model_definition(invalid_def)
        assert "'validators' must be a list" in str(excinfo.value)
    
    def test_validate_model_definition_invalid_validator_entry(self, registrar):
        """Test validating a definition with an invalid validator entry."""
        invalid_def = {
            "name": "TestModel",
            "fields": {
                "title": {
                    "type": "str"
                }
            },
            "validators": [
                "not a dict"  # Not a dictionary
            ]
        }
        with pytest.raises(ValueError) as excinfo:
            registrar._validate_model_definition(invalid_def)
        assert "Each validator must be a dictionary" in str(excinfo.value)
    
    def test_validate_model_definition_missing_validator_keys(self, registrar):
        """Test validating a definition with validators missing required keys."""
        invalid_def = {
            "name": "TestModel",
            "fields": {
                "title": {
                    "type": "str"
                }
            },
            "validators": [
                {
                    "name": "title_not_empty",
                    # Missing "fields" and "code" keys
                }
            ]
        }
        with pytest.raises(ValueError) as excinfo:
            registrar._validate_model_definition(invalid_def)
        assert "Each validator must have a 'fields' key" in str(excinfo.value)
    
    def test_validate_model_definition_invalid_metadata_schema(self, registrar):
        """Test validating a definition with an invalid metadata schema."""
        invalid_def = {
            "name": "TestModel",
            "fields": {
                "title": {
                    "type": "str"
                }
            },
            "metadata_schema": "not a dict"  # Not a dictionary
        }
        with pytest.raises(ValueError) as excinfo:
            registrar._validate_model_definition(invalid_def)
        assert "'metadata_schema' must be a dictionary" in str(excinfo.value)
    
    @pytest.mark.asyncio
    async def test_check_existing_model_exists(self, registrar, mock_db_connector):
        """Test checking for an existing model that exists."""
        model_id = "123e4567-e89b-12d3-a456-426614174000"
        mock_db_connector.fetchone.return_value = {"id": model_id}
        
        result = await registrar._check_existing_model("TestModel")
        
        assert result == model_id
        mock_db_connector.fetchone.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_existing_model_not_exists(self, registrar, mock_db_connector):
        """Test checking for an existing model that doesn't exist."""
        mock_db_connector.fetchone.return_value = None
        
        result = await registrar._check_existing_model("TestModel")
        
        assert result is None
        mock_db_connector.fetchone.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_existing_model(self, registrar, mock_db_connector, valid_model_definition):
        """Test updating an existing model."""
        model_id = "123e4567-e89b-12d3-a456-426614174000"
        mock_db_connector.fetchone.return_value = {"id": model_id}
        
        result = await registrar._update_existing_model(
            model_id,
            "TestModel",
            valid_model_definition,
            "Test description",
            "alpha",
            "1.0"
        )
        
        assert result == model_id
        mock_db_connector.fetchone.assert_called_once()
        # Verify that the definition was properly JSON encoded
        call_args = mock_db_connector.fetchone.call_args[0]
        assert json.loads(call_args[1]) == valid_model_definition
    
    @pytest.mark.asyncio
    async def test_insert_new_model(self, registrar, mock_db_connector, valid_model_definition):
        """Test inserting a new model."""
        model_id = "123e4567-e89b-12d3-a456-426614174000"
        mock_db_connector.fetchone.return_value = {"id": model_id}
        
        with patch('uuid.uuid4', return_value=model_id):
            result = await registrar._insert_new_model(
                "TestModel",
                valid_model_definition,
                "Test description",
                "alpha",
                "1.0"
            )
        
        assert result == model_id
        mock_db_connector.fetchone.assert_called_once()
        # Verify that the definition was properly JSON encoded
        call_args = mock_db_connector.fetchone.call_args[0]
        assert json.loads(call_args[4]) == valid_model_definition
    
    @pytest.mark.asyncio
    async def test_register_model_new(self, registrar, mock_db_connector, valid_model_definition):
        """Test registering a new model."""
        model_id = "123e4567-e89b-12d3-a456-426614174000"
        
        # First call is to check if model exists (None means it doesn't)
        # Second call is to insert new model
        mock_db_connector.fetchone.side_effect = [None, {"id": model_id}]
        
        with patch('uuid.uuid4', return_value=model_id):
            result = await registrar.register_model(
                "TestModel",
                valid_model_definition,
                "Test description",
                "alpha",
                "1.0"
            )
        
        assert result == model_id
        assert mock_db_connector.fetchone.call_count == 2
    
    @pytest.mark.asyncio
    async def test_register_model_update(self, registrar, mock_db_connector, valid_model_definition):
        """Test registering a model that already exists (update)."""
        model_id = "123e4567-e89b-12d3-a456-426614174000"
        
        # First call is to check if model exists
        # Second call is to update existing model
        mock_db_connector.fetchone.side_effect = [{"id": model_id}, {"id": model_id}]
        
        result = await registrar.register_model(
            "TestModel",
            valid_model_definition,
            "Test description",
            "alpha",
            "1.0"
        )
        
        assert result == model_id
        assert mock_db_connector.fetchone.call_count == 2
    
    @pytest.mark.asyncio
    async def test_register_model_invalid_type(self, registrar, valid_model_definition):
        """Test registering a model with an invalid type."""
        with pytest.raises(ValueError) as excinfo:
            await registrar.register_model(
                "TestModel",
                valid_model_definition,
                "Test description",
                "invalid_type",  # Invalid model type
                "1.0"
            )
        assert "Invalid model type" in str(excinfo.value)
    
    @pytest.mark.asyncio
    async def test_list_registered_models(self, registrar, mock_db_connector):
        """Test listing registered models."""
        mock_db_connector.fetch.return_value = [
            {"id": "123", "name": "Model1"},
            {"id": "456", "name": "Model2"}
        ]
        
        result = await registrar.list_registered_models()
        
        assert len(result) == 2
        assert result[0]["id"] == "123"
        assert result[1]["name"] == "Model2"
        mock_db_connector.fetch.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_model_definition_exists(self, registrar, mock_db_connector, valid_model_definition):
        """Test getting a model definition that exists."""
        model_id = "123e4567-e89b-12d3-a456-426614174000"
        mock_db_connector.fetchone.return_value = {
            "id": model_id,
            "name": "TestModel",
            "definition": json.dumps(valid_model_definition),
            "description": "Test description",
            "object_type": "alpha",
            "version": "1.0",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z"
        }
        
        result = await registrar.get_model_definition("TestModel")
        
        assert result["id"] == model_id
        assert result["name"] == "TestModel"
        assert result["definition"] == valid_model_definition
        mock_db_connector.fetchone.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_model_definition_not_exists(self, registrar, mock_db_connector):
        """Test getting a model definition that doesn't exist."""
        mock_db_connector.fetchone.return_value = None
        
        result = await registrar.get_model_definition("NonExistentModel")
        
        assert result is None
        mock_db_connector.fetchone.assert_called_once() 