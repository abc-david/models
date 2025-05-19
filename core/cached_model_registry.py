"""
MODULE: services/models/core/cached_model_registry.py
PURPOSE: Provides cached versions of ModelRegistry methods
DEPENDENCIES:
    - services.models.core.model_registry: For base ModelRegistry
    - services.cache: For caching functionality

This module extends the ModelRegistry with cached versions of its methods
for improved performance when retrieving models and schemas.
"""

import logging
from typing import Dict, Any, Optional, Type, List

from services.models.core.base_model import BaseModel
from services.models.core.model_registry import ModelRegistry
from services.cache import with_cache

logger = logging.getLogger(__name__)


class CachedModelRegistry(ModelRegistry):
    """
    Extension of ModelRegistry with caching for improved performance.
    
    This class provides cached versions of the core ModelRegistry methods
    to reduce database lookups and improve performance for frequently
    accessed models and schemas.
    """
    
    @classmethod
    @with_cache(ttl=3600, prefix="model_registry")  # Cache for 1 hour
    async def get_model_cached(cls, model_name: str) -> Optional[Type[BaseModel]]:
        """
        Get a model class by name with caching.
        
        Args:
            model_name: Name of the model to retrieve
            
        Returns:
            Model class or None if not found
        """
        return cls.get_model(model_name)
    
    @classmethod
    @with_cache(ttl=3600, prefix="model_registry")  # Cache for 1 hour
    async def get_schema_cached(cls, model_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a model schema by name with caching.
        
        Args:
            model_name: Name of the model to retrieve
            
        Returns:
            Model schema or None if not found
        """
        return cls.get_schema(model_name)
    
    @classmethod
    @with_cache(ttl=300, prefix="model_registry")  # Cache for 5 minutes
    async def list_models_cached(cls) -> List[str]:
        """
        List all registered model names with caching.
        
        Returns:
            List of registered model names
        """
        return cls.list_models() 