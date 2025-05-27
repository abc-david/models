"""
Test module for the ModelOrchestrator with test_mode support.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.models.orchestrator import ModelOrchestrator


class TestModelOrchestratorTestMode:
    """Test cases for the ModelOrchestrator with different test modes."""
    
    def test_init_default_mode(self):
        """Test initializing the orchestrator with default mode (production)."""
        with patch('services.models.orchestrator.ModelRegistrar') as mock_registrar, \
             patch('config.settings.TEST_MODE', None):
            orchestrator = ModelOrchestrator()
            assert orchestrator.test_mode is None
            mock_registrar.assert_called_once_with(test_mode=None)
    
    def test_init_e2e_mode(self):
        """Test initializing the orchestrator with e2e test mode."""
        with patch('services.models.orchestrator.ModelRegistrar') as mock_registrar, \
             patch('config.settings.TEST_MODE', 'e2e'):
            orchestrator = ModelOrchestrator(test_mode='e2e')
            assert orchestrator.test_mode == 'e2e'
            mock_registrar.assert_called_once_with(test_mode='e2e')
    
    def test_init_mock_mode(self):
        """Test initializing the orchestrator with mock test mode."""
        with patch('services.models.orchestrator.ModelRegistrar') as mock_registrar, \
             patch('config.settings.TEST_MODE', 'mock'):
            orchestrator = ModelOrchestrator(test_mode='mock')
            assert orchestrator.test_mode == 'mock'
            mock_registrar.assert_called_once_with(test_mode='mock')
    
    @pytest.mark.asyncio
    async def test_verify_db_schema_propagates_test_mode(self):
        """Test that verify_db_schema passes test_mode to SchemaInspector."""
        with patch('services.models.db_schema_inspector.SchemaInspector') as mock_inspector_class, \
             patch('config.settings.TEST_MODE', 'e2e'):
            # Set up mock inspector instance
            mock_inspector = AsyncMock()
            mock_inspector_class.return_value = mock_inspector
            
            # Set up mock verify_model_schema method
            mock_inspector.verify_model_schema.return_value = {"is_valid": True}
            
            # Create orchestrator with test mode
            orchestrator = ModelOrchestrator(test_mode='e2e')
            
            # Call verify_db_schema
            result = await orchestrator.verify_db_schema("test_schema", "test_model")
            
            # Assert SchemaInspector was initialized with the correct test_mode
            mock_inspector_class.assert_called_once_with(test_mode='e2e')
            
            # Assert verify_model_schema was called correctly
            mock_inspector.verify_model_schema.assert_called_once_with(
                "test_schema", "test_model"
            )
            
            # Assert close was called on the inspector
            mock_inspector.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_verify_all_models_propagates_test_mode(self):
        """Test that verify_all_models passes test_mode to SchemaInspector."""
        with patch('services.models.db_schema_inspector.SchemaInspector') as mock_inspector_class, \
             patch('config.settings.TEST_MODE', 'mock'):
            # Set up mock inspector instance
            mock_inspector = AsyncMock()
            mock_inspector_class.return_value = mock_inspector
            
            # Set up mock verify_model_schema method
            mock_inspector.verify_model_schema.return_value = {"is_valid": True}
            
            # Set up mock list_models method
            with patch('services.models.orchestrator.ModelOrchestrator.list_models') as mock_list_models:
                mock_list_models.return_value = ["model1", "model2"]
                
                # Create orchestrator with test mode
                orchestrator = ModelOrchestrator(test_mode='mock')
                
                # Call verify_all_models
                result = await orchestrator.verify_all_models("test_schema")
                
                # Assert SchemaInspector was initialized with the correct test_mode
                mock_inspector_class.assert_called_once_with(test_mode='mock')
                
                # Assert verify_model_schema was called for each model
                assert mock_inspector.verify_model_schema.call_count == 2
                
                # Assert close was called on the inspector
                mock_inspector.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_close_propagates_to_registrar(self):
        """Test that close method calls close on the registrar."""
        with patch('services.models.orchestrator.ModelRegistrar') as mock_registrar_class, \
             patch('config.settings.TEST_MODE', None):
            # Set up mock registrar instance
            mock_registrar = AsyncMock()
            mock_registrar_class.return_value = mock_registrar
            
            # Create orchestrator
            orchestrator = ModelOrchestrator()
            
            # Call close
            await orchestrator.close()
            
            # Assert close was called on the registrar
            mock_registrar.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_register_model_in_db_with_test_mode(self):
        """Test that register_model_in_db calls registrar with correct parameters."""
        with patch('services.models.orchestrator.ModelRegistrar') as mock_registrar_class, \
             patch('config.settings.TEST_MODE', 'e2e'):
            # Set up mock registrar instance
            mock_registrar = AsyncMock()
            mock_registrar.register_model_in_db.return_value = "test_id"
            mock_registrar_class.return_value = mock_registrar
            
            # Create orchestrator with test mode
            orchestrator = ModelOrchestrator(test_mode='e2e')
            
            # Test data
            name = "test_model"
            definition = {"fields": {"name": {"type": "str"}}}
            description = "Test description"
            
            # Call register_model_in_db
            result = await orchestrator.register_model_in_db(
                name, definition, description
            )
            
            # Assert result is correct
            assert result == "test_id"
            
            # Assert registrar was called with correct parameters
            mock_registrar.register_model_in_db.assert_called_once_with(
                model_name=name,
                model_definition=definition,
                description=description, 
                model_type="alpha",
                version="1.0"  # Default values
            ) 