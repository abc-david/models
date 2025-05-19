"""
MODULE: services/models/orchestrator.py
PURPOSE: Central entry point for all model-related functionality
DEPENDENCIES:
    - services.models.model_registry: Model registry
    - services.models.validator: Data validation
    - services.models.db_schema_inspector: Schema inspection and validation
    - services.models.storage: Model storage

This module provides a centralized API for all model-related operations, including
model registration, validation, storage, schema management, and integration with 
the database. It serves as the main entry point for other services to interact
with the models service.
"""

import logging
from typing import Dict, List, Any, Optional, Type, Union

from services.models.core.base_model import BaseModel
from services.models.core.model_registry import ModelRegistry
from services.models.validation.validator import ModelValidator, ValidationResult
from services.models.utils.model_registrar import ModelRegistrar

logger = logging.getLogger(__name__)


class ModelOrchestrator:
    """
    Orchestrator for model-related operations.
    
    This class provides centralized access to all model-related functionality:
    - Model registration and retrieval
    - Data validation against models
    - Schema management and verification
    - Integration with database
    """
    
    def __init__(self):
        """Initialize the model orchestrator."""
        self.validator = ModelValidator()
        self.model_registrar = ModelRegistrar()
        
    async def get_model(self, model_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a model schema by name.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Model schema or None if not found
        """
        return await ModelRegistry.get_schema(model_name)
    
    async def list_models(self) -> List[str]:
        """
        List all available models.
        
        Returns:
            List of model names
        """
        return await ModelRegistry.list_models()
    
    async def validate_data(
        self,
        data: Dict[str, Any],
        model_name: str,
        partial: bool = False
    ) -> ValidationResult:
        """
        Validate data against a model.
        
        Args:
            data: Data to validate
            model_name: Name of the model to validate against
            partial: Allow partial validation (missing fields)
            
        Returns:
            ValidationResult with validation status and errors
            
        Raises:
            ValueError: If the model is not found
        """
        model_schema = await self.get_model(model_name)
        if not model_schema:
            raise ValueError(f"Model '{model_name}' not found")
            
        return self.validator.validate_against_model(data, model_schema, partial)
    
    async def register_model(self, model_class: Type[BaseModel]) -> None:
        """
        Register a model class in the in-memory registry.
        
        Args:
            model_class: Model class to register
        """
        ModelRegistry.register_model(model_class)
    
    async def register_model_in_db(
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
        return await self.model_registrar.register_model(
            name, definition, description, model_type, version, sync_with_registry
        )
    
    async def list_models_in_db(self) -> List[Dict[str, Any]]:
        """
        List all registered models in the database.
        
        Returns:
            List of model dictionaries
        """
        return await self.model_registrar.list_registered_models()
    
    async def get_model_definition_from_db(self, model_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a model definition from the database by name.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Model definition dictionary, or None if not found
        """
        return await self.model_registrar.get_model_definition(model_name)
    
    async def verify_db_schema(
        self,
        db_schema: str,
        model_name: str
    ) -> Dict[str, Any]:
        """
        Verify that a database schema matches a model schema.
        
        Args:
            db_schema: Database schema name
            model_name: Model name
            
        Returns:
            Dict with verification results
        """
        # Will be implemented after moving schema_inspector functionality
        from services.models.db_schema_inspector import SchemaInspector
        
        inspector = SchemaInspector()
        try:
            return await inspector.verify_model_schema(db_schema, model_name)
        finally:
            await inspector.close()
    
    async def verify_all_models(self, db_schema: str = "public") -> Dict[str, Any]:
        """
        Verify all registered models against a database schema.
        
        Args:
            db_schema: Database schema name
            
        Returns:
            Dict mapping model names to verification results
        """
        # Will be implemented after moving schema_inspector functionality
        from services.models.db_schema_inspector import SchemaInspector
        
        inspector = SchemaInspector()
        try:
            models = await self.list_models()
            results = {}
            
            for model_name in models:
                results[model_name] = await inspector.verify_model_schema(db_schema, model_name)
                
            return results
        finally:
            await inspector.close()


# Singleton instance for easy import
orchestrator = ModelOrchestrator() 