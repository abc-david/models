"""
MODULE: services/models/cache_init.py
PURPOSE: Initializes cached versions of model service components
DEPENDENCIES:
    - services.models.core.cached_model_registry: For cached model registry
    - services.models.storage.cached_storage: For cached object storage
    - services.models.storage.cached_template_storage: For cached template storage
    - services.cache: For cache configuration

This module provides functions to initialize and configure the cached versions
of model service components for improved performance.
"""

import logging
from typing import Optional, Dict, Any

from services.cache import CacheManager
from services.models.core.cached_model_registry import CachedModelRegistry
from services.models.storage.cached_storage import CachedObjectStorage
from services.models.storage.cached_template_storage import CachedDatabaseTemplateStorage
from services.database.db_operator import DBOperator

logger = logging.getLogger(__name__)


def initialize_cache(cache_config: Optional[Dict[str, Any]] = None) -> CacheManager:
    """
    Initialize the cache manager with the specified configuration.
    
    Args:
        cache_config: Optional cache configuration dictionary
        
    Returns:
        Configured cache manager instance
    """
    # Create cache manager with provided config or defaults
    cache_manager = CacheManager(config=cache_config)
    logger.info("Cache manager initialized")
    return cache_manager


def initialize_cached_model_registry() -> CachedModelRegistry:
    """
    Initialize the cached model registry.
    
    Returns:
        CachedModelRegistry instance
    """
    # Initialize model registry
    registry = CachedModelRegistry()
    logger.info("Cached model registry initialized")
    return registry


def initialize_cached_object_storage(
    db_operator: Optional[DBOperator] = None,
    schema_name: str = "public"
) -> CachedObjectStorage:
    """
    Initialize the cached object storage.
    
    Args:
        db_operator: Database operator instance (creates new one if None)
        schema_name: Database schema name (default: "public")
        
    Returns:
        CachedObjectStorage instance
    """
    # Create DB operator if not provided
    if db_operator is None:
        db_operator = DBOperator()
    
    # Initialize object storage
    storage = CachedObjectStorage(db_operator, schema_name)
    logger.info(f"Cached object storage initialized for schema: {schema_name}")
    return storage


def initialize_cached_template_storage(
    db_operator: Optional[DBOperator] = None,
    schema_name: str = "public"
) -> CachedDatabaseTemplateStorage:
    """
    Initialize the cached template storage.
    
    Args:
        db_operator: Database operator instance (creates new one if None)
        schema_name: Database schema name (default: "public")
        
    Returns:
        CachedDatabaseTemplateStorage instance
    """
    # Create DB operator if not provided
    if db_operator is None:
        db_operator = DBOperator()
    
    # Initialize template storage
    template_storage = CachedDatabaseTemplateStorage(db_operator, schema_name)
    logger.info(f"Cached template storage initialized for schema: {schema_name}")
    return template_storage


def initialize_all_caches(
    cache_config: Optional[Dict[str, Any]] = None,
    db_operator: Optional[DBOperator] = None,
    schema_name: str = "public"
) -> Dict[str, Any]:
    """
    Initialize all cached components at once.
    
    Args:
        cache_config: Optional cache configuration dictionary
        db_operator: Database operator instance (creates new one if None)
        schema_name: Database schema name (default: "public")
        
    Returns:
        Dictionary containing all initialized cached components
    """
    # Initialize cache manager
    cache_manager = initialize_cache(cache_config)
    
    # Create DB operator if not provided
    if db_operator is None:
        db_operator = DBOperator()
    
    # Initialize all components
    model_registry = initialize_cached_model_registry()
    object_storage = initialize_cached_object_storage(db_operator, schema_name)
    template_storage = initialize_cached_template_storage(db_operator, schema_name)
    
    logger.info("All cached model components initialized")
    
    return {
        "cache_manager": cache_manager,
        "model_registry": model_registry,
        "object_storage": object_storage,
        "template_storage": template_storage
    } 