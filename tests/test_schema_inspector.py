"""
Test module for the SchemaInspector with test_mode support.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.models.db_schema_inspector import SchemaInspector


class TestSchemaInspectorTestMode:
    """Test cases for the SchemaInspector with different test modes."""
    
    def test_init_default_mode(self):
        """Test initializing the inspector with default mode (production)."""
        with patch('services.models.db_schema_inspector.DBConnector') as mock_connector, \
             patch('services.models.db_schema_inspector.SchemaSetup') as mock_setup, \
             patch('config.settings.TEST_MODE', None):
            inspector = SchemaInspector()
            assert inspector.test_mode is None
            mock_connector.assert_called_once()
            mock_setup.assert_called_once()
    
    def test_init_e2e_mode(self):
        """Test initializing the inspector with e2e test mode."""
        with patch('services.models.db_schema_inspector.DBConnector') as mock_connector, \
             patch('services.models.db_schema_inspector.SchemaSetup') as mock_setup, \
             patch('config.settings.TEST_MODE', 'e2e'):
            inspector = SchemaInspector(test_mode='e2e')
            assert inspector.test_mode == 'e2e'
            mock_connector.assert_called_once()
            mock_setup.assert_called_once()
    
    def test_init_mock_mode(self):
        """Test initializing the inspector with mock test mode."""
        with patch('services.models.db_schema_inspector.DBConnector') as mock_connector, \
             patch('services.models.db_schema_inspector.SchemaSetup') as mock_setup, \
             patch('config.settings.TEST_MODE', 'mock'):
            inspector = SchemaInspector(test_mode='mock')
            assert inspector.test_mode == 'mock'
            mock_connector.assert_called_once()
            mock_setup.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_close_with_test_mode(self):
        """Test that close method calls close on all dependencies."""
        with patch('services.models.db_schema_inspector.DBConnector') as mock_connector_class, \
             patch('services.models.db_schema_inspector.SchemaSetup') as mock_setup_class, \
             patch('config.settings.TEST_MODE', 'e2e'):
            # Set up mocks
            mock_connector = AsyncMock()
            mock_setup = AsyncMock()
            
            mock_connector_class.return_value = mock_connector
            mock_setup_class.return_value = mock_setup
            
            # Create inspector with test mode
            inspector = SchemaInspector(test_mode='e2e')
            
            # Call close
            await inspector.close()
            
            # Assert close was called on dependencies
            mock_connector.close.assert_called_once()
            mock_setup.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_inspect_schema_with_test_mode(self):
        """Test that inspect_schema uses test_mode correctly."""
        with patch('services.models.db_schema_inspector.DBConnector') as mock_connector_class, \
             patch('services.models.db_schema_inspector.SchemaSetup') as mock_setup_class, \
             patch('config.settings.TEST_MODE', 'e2e'):
            # Set up mocks
            mock_connector = AsyncMock()
            mock_setup = AsyncMock()
            
            # Configure mock_setup._schema_exists to return True
            mock_setup._schema_exists = AsyncMock(return_value=True)
            
            # Configure mock_setup._get_existing_tables to return a list of tables
            mock_setup._get_existing_tables = AsyncMock(return_value=["table1", "table2"])
            
            # Configure mock_connector.execute to return column info
            mock_connector.execute = AsyncMock(return_value=[])
            
            mock_connector_class.return_value = mock_connector
            mock_setup_class.return_value = mock_setup
            
            # Create inspector with test mode
            inspector = SchemaInspector(test_mode='e2e')
            
            # Call inspect_schema
            result = await inspector.inspect_schema("test_schema")
            
            # Assert _schema_exists was called with correct parameters
            mock_setup._schema_exists.assert_called_once_with("test_schema")
            
            # Assert _get_existing_tables was called with correct parameters
            mock_setup._get_existing_tables.assert_called_once_with("test_schema")
            
            # Assert result contains expected data
            assert result["exists"] is True
            assert result["name"] == "test_schema"
            assert "table1" in result["tables"]
            assert "table2" in result["tables"]
    
    @pytest.mark.asyncio
    async def test_verify_model_schema_with_test_mode(self):
        """Test that verify_model_schema uses test_mode correctly."""
        with patch('services.models.db_schema_inspector.DBConnector') as mock_connector_class, \
             patch('services.models.db_schema_inspector.SchemaSetup') as mock_setup_class, \
             patch('services.models.db_schema_inspector.ModelRegistry') as mock_registry, \
             patch('config.settings.TEST_MODE', 'e2e'):
            # Set up mocks
            mock_connector = AsyncMock()
            mock_setup = AsyncMock()
            
            mock_connector_class.return_value = mock_connector
            mock_setup_class.return_value = mock_setup
            
            # Mock ModelRegistry.get_schema
            model_schema = {
                "model_name": "test_model",
                "table_name": "test_table",
                "fields": {
                    "id": {
                        "type": "UUID",
                        "required": True
                    },
                    "name": {
                        "type": "str",
                        "required": True
                    }
                }
            }
            mock_registry.get_schema = AsyncMock(return_value=model_schema)
            
            # Configure inspect_schema to return table info
            # We'll patch the instance method to avoid circular dependencies
            with patch.object(SchemaInspector, 'inspect_schema', autospec=True) as mock_inspect:
                mock_inspect.return_value = {
                    "exists": True,
                    "name": "test_schema",
                    "tables": ["test_table"],
                    "tables_info": {
                        "test_table": {
                            "columns": [
                                {"column_name": "id", "data_type": "uuid", "is_nullable": "NO", "column_default": None},
                                {"column_name": "name", "data_type": "character varying", "is_nullable": "NO", "column_default": None}
                            ],
                            "primary_keys": ["id"],
                            "indexes": []
                        }
                    }
                }
                
                # Create inspector with test mode
                inspector = SchemaInspector(test_mode='e2e')
                
                # Call verify_model_schema
                result = await inspector.verify_model_schema("test_schema", "test_model")
                
                # Assert get_schema was called with correct parameters
                mock_registry.get_schema.assert_called_once_with("test_model")
                
                # Assert inspect_schema was called with correct parameters
                mock_inspect.assert_called_once()
                
                # Assert result contains expected data
                assert result["model_name"] == "test_model"
                assert result["db_schema"] == "test_schema"
                assert result["table_name"] == "test_table"
                assert result["is_valid"] is True
                assert result["missing_columns"] == []
                assert result["type_mismatches"] == [] 