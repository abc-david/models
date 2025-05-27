"""
Test module for the ModelRegistrar's test_mode functionality.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, ANY

from services.models.registrar import ModelRegistrar


class TestModelRegistrarTestMode:
    """Test cases for the ModelRegistrar with different test modes."""
    
    def test_init_default_mode(self):
        """Test initializing the registrar with default mode (production)."""
        with patch('services.models.registrar.DBOperator') as mock_db_operator, \
             patch('config.settings.TEST_MODE', None):
            registrar = ModelRegistrar()
            assert registrar.test_mode is None
            mock_db_operator.assert_called_once()
    
    def test_init_e2e_mode(self):
        """Test initializing the registrar with e2e test mode."""
        with patch('services.models.registrar.DBOperator') as mock_db_operator, \
             patch('config.settings.TEST_MODE', 'e2e'):
            registrar = ModelRegistrar(test_mode='e2e')
            assert registrar.test_mode == 'e2e'
            mock_db_operator.assert_called_once()
    
    def test_init_mock_mode(self):
        """Test initializing the registrar with mock test mode."""
        with patch('services.models.registrar.DBOperator') as mock_db_operator, \
             patch('config.settings.TEST_MODE', 'mock'):
            registrar = ModelRegistrar(test_mode='mock')
            assert registrar.test_mode == 'mock'
            mock_db_operator.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_close_with_test_mode(self):
        """Test that close method calls close on the db operator."""
        with patch('services.models.registrar.DBOperator') as mock_db_operator_class, \
             patch('config.settings.TEST_MODE', 'e2e'):
            # Set up mock db operator
            mock_db_operator = AsyncMock()
            mock_db_operator_class.return_value = mock_db_operator
            
            # Create registrar with test mode
            registrar = ModelRegistrar(test_mode='e2e')
            
            # Call close
            await registrar.close()
            
            # Assert close was called on db operator
            mock_db_operator.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_register_model_in_db_with_test_mode(self):
        """Test that register_model_in_db uses test_mode correctly."""
        with patch('services.models.registrar.DBOperator') as mock_db_operator_class, \
             patch('config.settings.TEST_MODE', 'e2e'), \
             patch('uuid.uuid4', return_value="test_id"):
            # Set up mock db operator
            mock_db_operator = AsyncMock()
            mock_db_operator.insert = AsyncMock(return_value={"id": "test_id"})
            mock_db_operator_class.return_value = mock_db_operator
            
            # Create registrar with test mode
            registrar = ModelRegistrar(test_mode='e2e')
            
            # Test data
            name = "test_model"
            definition = {"fields": {"name": {"type": "str"}}}
            description = "Test description"
            model_type = "alpha"
            version = "1.0"
            
            # Call register_model_in_db
            model_id = await registrar.register_model_in_db(
                name, definition, description, model_type, version
            )
            
            # Assert result is correct
            assert model_id == "test_id"
            
            # Assert insert was called with correct parameters
            mock_db_operator.insert.assert_called_once()
            
            # Get the first positional argument (table name)
            args, _ = mock_db_operator.insert.call_args
            assert args[0] == "models"
    
    @pytest.mark.asyncio
    async def test_list_models_in_db_with_test_mode(self):
        """Test that list_models_in_db uses test_mode correctly."""
        with patch('services.models.registrar.DBOperator') as mock_db_operator_class, \
             patch('config.settings.TEST_MODE', 'mock'):
            # Set up mock db operator
            mock_db_operator = AsyncMock()
            mock_db_operator.fetch = AsyncMock(return_value=[
                {"id": "id1", "name": "model1", "description": "desc1", "object_type": "alpha", "version": "1.0"},
                {"id": "id2", "name": "model2", "description": "desc2", "object_type": "beta", "version": "2.0"}
            ])
            mock_db_operator_class.return_value = mock_db_operator
            
            # Create registrar with test mode
            registrar = ModelRegistrar(test_mode='mock')
            
            # Call list_models_in_db
            models = await registrar.list_models_in_db()
            
            # Assert result has correct length
            assert len(models) == 2
            
            # Assert fetch was called with correct parameters
            mock_db_operator.fetch.assert_called_once()
            
            # Get the first positional argument (table name)
            args, _ = mock_db_operator.fetch.call_args
            assert args[0] == "models"
    
    @pytest.mark.asyncio
    async def test_get_model_definition_from_db_with_test_mode(self):
        """Test that get_model_definition_from_db uses test_mode correctly."""
        with patch('services.models.registrar.DBOperator') as mock_db_operator_class, \
             patch('config.settings.TEST_MODE', 'e2e'):
            # Set up mock db operator
            mock_db_operator = AsyncMock()
            mock_db_operator.get_by_name = AsyncMock(return_value={
                "id": "id1", 
                "name": "test_model", 
                "definition": {"fields": {}}, 
                "description": "desc", 
                "object_type": "alpha", 
                "version": "1.0"
            })
            mock_db_operator_class.return_value = mock_db_operator
            
            # Create registrar with test mode
            registrar = ModelRegistrar(test_mode='e2e')
            
            # Call get_model_definition_from_db
            model = await registrar.get_model_definition_from_db("test_model")
            
            # Assert result is not None
            assert model is not None
            
            # Assert model data is correct
            assert model["name"] == "test_model"
            assert model["description"] == "desc"
            
            # Assert get_by_name was called with correct parameters
            mock_db_operator.get_by_name.assert_called_once_with("models", "test_model") 