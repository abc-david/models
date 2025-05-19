"""
MODULE: services/models/storage/cached_storage.py
PURPOSE: Provides cached versions of ObjectStorage methods
DEPENDENCIES:
    - services.models.storage.storage: For base ObjectStorage
    - services.cache: For caching functionality

This module extends the ObjectStorage with cached versions of its retrieval methods
for improved performance when accessing objects from the database.
"""

import logging
from typing import Dict, Any, Optional, List

from services.models.storage.storage import ObjectStorage
from services.cache import with_cache

logger = logging.getLogger(__name__)


class CachedObjectStorage(ObjectStorage):
    """
    Extension of ObjectStorage with caching for improved performance.
    
    This class provides cached versions of the retrieval methods in ObjectStorage
    to reduce database lookups and improve performance for frequently accessed objects.
    """
    
    @with_cache(ttl=1800, prefix="object_storage")  # Cache for 30 minutes
    async def get_object_cached(self, object_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve an object by its ID with caching.
        
        Args:
            object_id: UUID of the object
            
        Returns:
            Optional[Dict[str, Any]]: Object data if found, None otherwise
        """
        return self.get_object(object_id)
    
    @with_cache(ttl=600, prefix="object_storage")  # Cache for 10 minutes
    async def get_objects_by_type_cached(
        self,
        content_type: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Retrieve objects by content type with caching.
        
        Args:
            content_type: Type of content to retrieve
            limit: Maximum number of objects to return
            offset: Number of objects to skip
            
        Returns:
            List[Dict[str, Any]]: List of matching objects
        """
        return self.get_objects_by_type(content_type, limit, offset)
    
    @with_cache(ttl=600, prefix="object_storage")  # Cache for 10 minutes
    async def get_objects_by_parent_cached(
        self,
        parent_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Retrieve objects by parent ID with caching.
        
        Args:
            parent_id: ID of parent object
            limit: Maximum number of objects to return
            offset: Number of objects to skip
            
        Returns:
            List[Dict[str, Any]]: List of child objects
        """
        return self.get_objects_by_parent(parent_id, limit, offset)
    
    @with_cache(ttl=600, prefix="object_storage")  # Cache for 10 minutes
    async def get_objects_by_hierarchy_cached(
        self,
        level: int,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Retrieve objects by hierarchy level with caching.
        
        Args:
            level: Hierarchy level (0 for root, 1 for first level, etc.)
            limit: Maximum number of objects to return
            offset: Number of objects to skip
            
        Returns:
            List[Dict[str, Any]]: List of objects at specified level
        """
        return self.get_objects_by_hierarchy(level, limit, offset)
    
    @with_cache(ttl=300, prefix="object_storage")  # Cache for 5 minutes
    async def search_objects_cached(
        self,
        query: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Search objects by content or metadata with caching.
        
        Args:
            query: Search query
            limit: Maximum number of objects to return
            offset: Number of objects to skip
            
        Returns:
            List[Dict[str, Any]]: List of matching objects
        """
        return self.search_objects(query, limit, offset)
    
    def invalidate_object_cache(self, object_id: str) -> None:
        """
        Invalidate cache for a specific object when it's updated or deleted.
        
        Args:
            object_id: UUID of the object to invalidate in cache
        """
        # This method would use the CacheManager directly to invalidate specific keys
        # In a real implementation, you would need to:
        # 1. Create a key pattern matching the object_id 
        # 2. Use CacheManager.invalidate_pattern() to remove matching keys
        logger.info(f"Cache invalidation for object {object_id} would happen here")
        # Implementation would depend on the specific cache backend and key structure 