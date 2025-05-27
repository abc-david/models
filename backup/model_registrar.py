"""
File: services/models/utils/model_registrar.py
Module: Model Registration Utility
Purpose: Register and validate model definitions in the database
Dependencies:
    - Database for model storage
    - JSON Schema validation
    - Model pattern verification

This module provides utilities for registering model definitions in the
database, ensuring they comply with expected patterns and validating
the JSONB structure against legacy models.
"""

import logging
import json
import uuid
from typing import Dict, Any, List, Optional, Union

from services.database.db_connector import DBConnector
from services.models.core.model_registry import ModelRegistry

logger = logging.getLogger(__name__)


class ModelRegistrar:
    """
    Utility class for registering model definitions in the database.
    
    This class handles:
    1. Validating model structure against expected patterns
    2. Inserting validated models into the database
    3. Optionally syncing with the in-memory model registry
    """
    
    # Required keys for the definition JSONB field
    REQUIRED_DEFINITION_KEYS = ['name', 'fields']
    
    # Optional keys for the definition JSONB field
    OPTIONAL_DEFINITION_KEYS = ['metadata_schema', 'validators', 'description']
    
    # Required keys for each field definition
    REQUIRED_FIELD_KEYS = ['type']
    
    # Valid model types
    VALID_MODEL_TYPES = ['alpha', 'beta', 'gamma', 'qualifier', 'organizer', 'prompt_template', 'prompt_chain']
    
    def __init__(self, db_connector: Optional[DBConnector] = None, test_mode: Optional[str] = None):
        """
        Initialize the model registrar.
        
        Args:
            db_connector: Optional database connector. If not provided, a new one will be created.
            test_mode: Test mode to use ('mock', 'e2e', or None for production)
        """
        self.test_mode = test_mode
        self.db_connector = db_connector or DBConnector(test_mode=test_mode)
    
    async def register_model(
        self,
        name: str,
        definition: Dict[str, Any],
        description: str,
        model_type: str = "alpha",
        version: str = "1.0",
        sync_with_registry: bool = False
    ) -> str:
        """
        Register a model definition in the database.
        
        Args:
            name: Model name
            definition: Model definition dictionary
            description: Model description
            model_type: Type of model (alpha, beta, gamma, qualifier, organizer)
            version: Model version
            sync_with_registry: Whether to sync with the in-memory registry
            
        Returns:
            ID of the registered model
            
        Raises:
            ValueError: If the model definition is invalid
        """
        # Validate model type
        if model_type not in self.VALID_MODEL_TYPES:
            valid_types = ", ".join(self.VALID_MODEL_TYPES)
            raise ValueError(f"Invalid model type: {model_type}. Valid types are: {valid_types}")
        
        # Validate model definition structure
        self._validate_model_definition(definition)
        
        # Check if model already exists
        existing_model_id = await self._check_existing_model(name)
        
        if existing_model_id:
            # Update existing model
            model_id = await self._update_existing_model(
                existing_model_id, name, definition, description, model_type, version
            )
        else:
            # Insert new model
            model_id = await self._insert_new_model(
                name, definition, description, model_type, version
            )
        
        # Optionally sync with in-memory registry
        if sync_with_registry:
            await self._sync_with_registry(name, definition)
        
        return model_id
    
    def _validate_model_definition(self, definition: Dict[str, Any]) -> None:
        """
        Validate the model definition structure.
        
        Args:
            definition: Model definition dictionary
            
        Raises:
            ValueError: If the definition is invalid
        """
        # Check required keys
        missing_keys = [key for key in self.REQUIRED_DEFINITION_KEYS if key not in definition]
        if missing_keys:
            raise ValueError(f"Missing required keys in model definition: {', '.join(missing_keys)}")
        
        # Check fields structure
        fields = definition.get('fields', {})
        if not isinstance(fields, dict):
            raise ValueError("'fields' must be a dictionary")
        
        # Validate each field
        for field_name, field_def in fields.items():
            if not isinstance(field_def, dict):
                raise ValueError(f"Field definition for '{field_name}' must be a dictionary")
            
            missing_field_keys = [key for key in self.REQUIRED_FIELD_KEYS if key not in field_def]
            if missing_field_keys:
                raise ValueError(f"Missing required keys in field '{field_name}': {', '.join(missing_field_keys)}")
        
        # Validate validators if present
        validators = definition.get('validators', [])
        if not isinstance(validators, list):
            raise ValueError("'validators' must be a list")
        
        for validator in validators:
            if not isinstance(validator, dict):
                raise ValueError("Each validator must be a dictionary")
            
            if 'name' not in validator:
                raise ValueError("Each validator must have a 'name' key")
            
            if 'fields' not in validator:
                raise ValueError("Each validator must have a 'fields' key")
            
            if 'code' not in validator:
                raise ValueError("Each validator must have a 'code' key")
        
        # Validate metadata_schema if present
        metadata_schema = definition.get('metadata_schema', {})
        if not isinstance(metadata_schema, dict):
            raise ValueError("'metadata_schema' must be a dictionary")
    
    async def _check_existing_model(self, name: str) -> Optional[str]:
        """
        Check if a model with the given name already exists.
        
        Args:
            name: Model name
            
        Returns:
            Model ID if found, None otherwise
        """
        query = "SELECT id FROM public.object_models WHERE name = $1"
        result = await self.db_connector.execute(query, (name,), fetch_row=True)
        return result['id'] if result else None
    
    async def _update_existing_model(
        self,
        model_id: str,
        name: str,
        definition: Dict[str, Any],
        description: str,
        model_type: str,
        version: str
    ) -> str:
        """
        Update an existing model in the database.
        
        Args:
            model_id: ID of the model to update
            name: Model name
            definition: Model definition dictionary
            description: Model description
            model_type: Type of model
            version: Model version
            
        Returns:
            Model ID
        """
        query = """
            UPDATE public.object_models
            SET definition = $1, description = $2, object_type = $3, version = $4, updated_at = NOW()
            WHERE id = $5
            RETURNING id
        """
        
        result = await self.db_connector.execute(
            query,
            (json.dumps(definition), description, model_type, version, model_id),
            fetch_row=True
        )
        
        logger.info(f"Updated existing model {name} with ID {model_id}")
        return result['id']
    
    async def _insert_new_model(
        self,
        name: str,
        definition: Dict[str, Any],
        description: str,
        model_type: str,
        version: str
    ) -> str:
        """
        Insert a new model into the database.
        
        Args:
            name: Model name
            definition: Model definition dictionary
            description: Model description
            model_type: Type of model
            version: Model version
            
        Returns:
            Model ID
        """
        model_id = str(uuid.uuid4())
        
        query = """
            INSERT INTO public.object_models
            (id, name, object_type, version, definition, description, use_cases, related_templates, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW(), NOW())
            RETURNING id
        """
        
        # Default empty arrays for use_cases and related_templates
        use_cases = []
        related_templates = []
        
        result = await self.db_connector.execute(
            query,
            (model_id, name, model_type, version, json.dumps(definition), description, json.dumps(use_cases), json.dumps(related_templates)),
            fetch_row=True
        )
        
        logger.info(f"Inserted new model {name} with ID {model_id}")
        return result['id']
    
    async def _sync_with_registry(self, name: str, definition: Dict[str, Any]) -> None:
        """
        Sync model with in-memory registry.
        
        Args:
            name: Model name
            definition: Model definition dictionary
        """
        # Implementation depends on how the in-memory registry is managed
        logger.info(f"Syncing model {name} with in-memory registry")
        # For now, just notify that syncing would occur
        pass
    
    async def list_registered_models(self) -> List[Dict[str, Any]]:
        """
        List all registered models in the database.
        
        Returns:
            List of model dictionaries
        """
        query = "SELECT id, name, object_type, version, description, created_at, updated_at FROM public.object_models"
        results = await self.db_connector.execute(query, fetch_all=True)
        
        # Convert datetime objects to strings and return
        models = []
        for row in results:
            # Make a copy to avoid modifying the original
            model = dict(row)
            model['created_at'] = str(model['created_at'])
            model['updated_at'] = str(model['updated_at'])
            models.append(model)
            
        return models
    
    async def get_model_definition(self, model_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a model definition from the database by name.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Model definition dictionary, or None if not found
        """
        query = "SELECT definition FROM public.object_models WHERE name = $1"
        result = await self.db_connector.execute(query, (model_name,), fetch_row=True)
        
        if result and 'definition' in result:
            # Convert from JSON string to dictionary if necessary
            definition = result['definition']
            if isinstance(definition, str):
                try:
                    definition = json.loads(definition)
                except json.JSONDecodeError:
                    logger.error(f"Failed to decode definition JSON for model {model_name}")
                    return None
            
            return definition
        
        return None
    
    async def close(self) -> None:
        """Close the database connector."""
        await self.db_connector.close() 