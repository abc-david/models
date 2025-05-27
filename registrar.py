"""
MODULE: services/models/registrar.py
PURPOSE: Handles registration, retrieval and management of model definitions in the database.
DEPENDENCIES:
    - services.database.db_operator: For database operations
"""

import logging
import uuid
from typing import Dict, List, Any, Optional, Union, TypedDict

from services.database.db_operator import DBOperator
from services.database.helpers.constants import ModelTableColumns
import config.settings


logger = logging.getLogger(__name__)


class ModelDefinition(TypedDict):
    """Type definition for a model definition."""
    name: str
    fields: Dict[str, Dict[str, Any]]
    description: Optional[str]
    object_type: Optional[str]
    version: Optional[str]


class ModelRegistrar:
    """Handles registration, retrieval and management of model definitions in the database."""
    
    def __init__(self, test_mode: Optional[str] = None):
        """
        Initialize the ModelRegistrar with an optional test mode.
        
        Args:
            test_mode: Optional mode for testing ('mock', 'e2e', or None for production)
        """
        # Store the previous test mode so we can restore it later
        self._previous_test_mode = config.settings.TEST_MODE
        
        # Set the test mode in the global settings if specified
        if test_mode:
            config.settings.TEST_MODE = test_mode
        
        # Create the DB operator which will use the global test mode
        self.db = DBOperator()
        self.test_mode = test_mode
        
    async def register_model_in_db(
        self,
        model_name: str,
        model_definition: Dict[str, Any],
        description: Optional[str] = None,
        model_type: Optional[str] = None,
        version: Optional[str] = None
    ) -> str:
        """
        Register a model definition in the database.
        
        Args:
            model_name: The name of the model
            model_definition: The model definition as a dictionary
            description: Optional description of the model
            model_type: Optional type of model (e.g., 'prompt', 'document', etc.)
            version: Optional version of the model
            
        Returns:
            The UUID of the registered model
        """
        model_id = str(uuid.uuid4())
        
        # Prepare the model record
        model_record = {
            ModelTableColumns.ID: model_id,
            ModelTableColumns.NAME: model_name,
            ModelTableColumns.DEFINITION: model_definition,
            ModelTableColumns.DESCRIPTION: description,
            ModelTableColumns.OBJECT_TYPE: model_type,
            ModelTableColumns.VERSION: version
        }
        
        # Insert the model record into the database
        await self.db.insert("models", model_record)
        
        logger.info(f"Registered model {model_name} with ID {model_id}")
        return model_id
    
    async def get_model_definition_from_db(self, model_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a model definition from the database by name.
        
        Args:
            model_name: The name of the model to retrieve
            
        Returns:
            The model definition or None if not found
        """
        # Query the database for the model by name
        model_record = await self.db.get_by_name(
            "models", 
            model_name
        )
        
        if not model_record:
            logger.warning(f"Model {model_name} not found in database")
            return None
        
        # Return the model definition with additional metadata
        return {
            "id": model_record[ModelTableColumns.ID],
            "name": model_record[ModelTableColumns.NAME],
            "definition": model_record[ModelTableColumns.DEFINITION],
            "description": model_record[ModelTableColumns.DESCRIPTION],
            "object_type": model_record[ModelTableColumns.OBJECT_TYPE],
            "version": model_record[ModelTableColumns.VERSION]
        }
    
    async def list_models_in_db(self) -> List[Dict[str, Any]]:
        """
        List all models in the database.
        
        Returns:
            List of model records
        """
        # Query all models in the database
        model_records = await self.db.fetch("models")
        
        # Format the records
        formatted_models = [
            {
                "id": record[ModelTableColumns.ID],
                "name": record[ModelTableColumns.NAME],
                "description": record[ModelTableColumns.DESCRIPTION],
                "object_type": record[ModelTableColumns.OBJECT_TYPE],
                "version": record[ModelTableColumns.VERSION]
            }
            for record in model_records
        ]
        
        return formatted_models
    
    async def delete_model_from_db(self, model_id: str) -> bool:
        """
        Delete a model from the database.
        
        Args:
            model_id: The UUID of the model to delete
            
        Returns:
            True if the model was deleted, False otherwise
        """
        # Delete the model from the database
        delete_count = await self.db.delete("models", {ModelTableColumns.ID: model_id})
        
        if delete_count > 0:
            logger.info(f"Deleted model with ID {model_id}")
            return True
        else:
            logger.warning(f"Model with ID {model_id} not found for deletion")
            return False
    
    async def update_model_in_db(
        self,
        model_id: str,
        model_definition: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
        model_type: Optional[str] = None,
        version: Optional[str] = None
    ) -> bool:
        """
        Update a model definition in the database.
        
        Args:
            model_id: The UUID of the model to update
            model_definition: Optional updated model definition
            description: Optional updated description
            model_type: Optional updated model type
            version: Optional updated version
            
        Returns:
            True if the model was updated, False otherwise
        """
        # Prepare update data with only non-None values
        update_data = {}
        if model_definition is not None:
            update_data[ModelTableColumns.DEFINITION] = model_definition
        if description is not None:
            update_data[ModelTableColumns.DESCRIPTION] = description
        if model_type is not None:
            update_data[ModelTableColumns.OBJECT_TYPE] = model_type
        if version is not None:
            update_data[ModelTableColumns.VERSION] = version
            
        if not update_data:
            logger.warning("No update data provided for model update")
            return False
        
        # Update the model in the database
        update_count = await self.db.update(
            "models", 
            update_data, 
            {ModelTableColumns.ID: model_id}
        )
        
        if update_count > 0:
            logger.info(f"Updated model with ID {model_id}")
            return True
        else:
            logger.warning(f"Model with ID {model_id} not found for update")
            return False
    
    async def close(self) -> None:
        """Close the database connection and restore original test mode."""
        await self.db.close()
        
        # Restore the original test mode
        config.settings.TEST_MODE = self._previous_test_mode 