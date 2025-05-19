"""
File: services/models/core/model_registry.py
MODULE: Model Registry
PURPOSE: Central registry for model definitions
DEPENDENCIES:
    - Database for model storage/retrieval
    - Caching for performance

This module provides a central registry for model definitions that can be 
accessed from any service. It includes caching mechanisms to avoid repeated
database lookups and ensures consistent model definitions across the application.
"""

import logging
from typing import Dict, Any, Optional, Type, List, ClassVar
from datetime import datetime, timedelta
import json

from services.models.core.base_model import BaseModel

logger = logging.getLogger(__name__)


class ModelRegistry:
    """
    Central registry for model definitions.
    
    This class provides methods for registering, retrieving, and managing
    model definitions across the application. It includes caching to 
    improve performance.
    """
    
    # Class-level model registry
    _models: ClassVar[Dict[str, Type[BaseModel]]] = {}
    _schemas: ClassVar[Dict[str, Dict[str, Any]]] = {}
    _last_sync: ClassVar[datetime] = None
    _db_operator = None
    
    @classmethod
    def register_model(cls, model_class: Type[BaseModel]) -> None:
        """
        Register a model class with the registry.
        
        Args:
            model_class: Model class to register
        """
        model_name = model_class.model_name
        cls._models[model_name] = model_class
        cls._schemas[model_name] = model_class.to_schema()
        logger.info(f"Registered model: {model_name}")
    
    @classmethod
    def register_models(cls, model_classes: List[Type[BaseModel]]) -> None:
        """
        Register multiple model classes with the registry.
        
        Args:
            model_classes: List of model classes to register
        """
        for model_class in model_classes:
            cls.register_model(model_class)
    
    @classmethod
    async def get_model(cls, model_name: str) -> Optional[Type[BaseModel]]:
        """
        Get a model class by name.
        
        Args:
            model_name: Name of the model to retrieve
            
        Returns:
            Model class or None if not found
        """
        # Lazy load from database if not in registry
        if model_name not in cls._models:
            await cls._load_model_from_db(model_name)
            
        return cls._models.get(model_name)
    
    @classmethod
    async def get_schema(cls, model_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a model schema by name.
        
        Args:
            model_name: Name of the model to retrieve
            
        Returns:
            Model schema or None if not found
        """
        # Lazy load from database if not in registry
        if model_name not in cls._schemas:
            await cls._load_model_from_db(model_name)
            
        return cls._schemas.get(model_name)
    
    @classmethod
    async def list_models(cls) -> List[str]:
        """
        List all registered model names.
        
        Returns:
            List of registered model names
        """
        # Ensure models are synced with database
        await cls._sync_with_db()
        
        return list(cls._models.keys())
    
    @classmethod
    async def _load_model_from_db(cls, model_name: str) -> None:
        """
        Load a model definition from the database.
        
        Args:
            model_name: Name of the model to load
        """
        if cls._db_operator is None:
            # Lazy import to avoid circular dependencies
            from services.database.db_connector import DBConnector
            cls._db_operator = DBConnector()
            
        try:
            # Query for model definition using the correct table
            result = await cls._db_operator.fetch_one(
                """
                SELECT definition FROM public.object_models 
                WHERE name = $1
                """,
                (model_name,)
            )
            
            if result and result.get('definition'):
                # Extract definition from the result
                schema = result.get('definition')
                
                # Parse JSON string if needed
                if isinstance(schema, str):
                    try:
                        schema = json.loads(schema)
                    except json.JSONDecodeError as e:
                        logger.error(f"Error parsing model definition JSON: {str(e)}")
                        logger.debug(f"Raw schema string: {schema[:200]}")
                        return
                    
                cls._schemas[model_name] = schema
                logger.info(f"Loaded model from database: {model_name}")
            else:
                logger.warning(f"Model not found in database: {model_name}")
                
        except Exception as e:
            logger.error(f"Error loading model from database: {str(e)}")
            import traceback
            traceback.print_exc()
    
    @classmethod
    async def _sync_with_db(cls) -> None:
        """
        Synchronize the registry with the database.
        
        This method checks if models have been added to the database
        since the last synchronization and updates the registry accordingly.
        """
        # Only sync if necessary (not too frequent)
        now = datetime.now()
        if cls._last_sync and now - cls._last_sync < timedelta(minutes=5):
            return
            
        if cls._db_operator is None:
            # Lazy import to avoid circular dependencies
            from services.database.db_connector import DBConnector
            cls._db_operator = DBConnector()
            
        try:
            # Query for all model definitions
            result = await cls._db_operator.execute(
                """
                SELECT name, definition FROM public.object_models
                """
            )
            
            if result:
                for row in result:
                    model_name, schema = row
                    
                    # Parse JSON string if needed
                    if isinstance(schema, str):
                        import json
                        schema = json.loads(schema)
                        
                    # Only update if not already in registry
                    if model_name not in cls._schemas:
                        cls._schemas[model_name] = schema
                        logger.info(f"Synced model from database: {model_name}")
                    
            cls._last_sync = now
                
        except Exception as e:
            logger.error(f"Error syncing models from database: {str(e)}") 