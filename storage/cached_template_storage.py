"""
MODULE: services/models/storage/cached_template_storage.py
PURPOSE: Provides cached versions of DatabaseTemplateStorage methods
DEPENDENCIES:
    - services.models.storage.storage: For base DatabaseTemplateStorage
    - services.cache: For caching functionality

This module extends the DatabaseTemplateStorage with cached versions of its retrieval methods
for improved performance when accessing templates from the database.
"""

import logging
from typing import Dict, Any, Optional, List

from services.models.storage.storage import DatabaseTemplateStorage
from services.cache import with_cache

logger = logging.getLogger(__name__)


class CachedDatabaseTemplateStorage(DatabaseTemplateStorage):
    """
    Extension of DatabaseTemplateStorage with caching for improved performance.
    
    This class provides cached versions of the retrieval methods in DatabaseTemplateStorage
    to reduce database lookups and improve performance for frequently accessed templates.
    """
    
    @with_cache(ttl=3600, prefix="template_storage")  # Cache for 1 hour
    async def get_template_by_id_cached(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a template by ID with caching.
        
        Args:
            template_id: ID of the template to retrieve
            
        Returns:
            Optional[Dict[str, Any]]: Template data if found, None otherwise
        """
        return self.get_template_by_id(template_id)
    
    @with_cache(ttl=3600, prefix="template_storage")  # Cache for 1 hour
    async def get_template_by_name_cached(self, template_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a template by name with caching.
        
        Args:
            template_name: Name of the template to retrieve
            
        Returns:
            Optional[Dict[str, Any]]: Template data if found, None otherwise
        """
        return self.get_template_by_name(template_name)
    
    @with_cache(ttl=600, prefix="template_storage")  # Cache for 10 minutes
    async def list_templates_cached(
        self, 
        category: Optional[str] = None, 
        limit: int = 100, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List templates, optionally filtered by category, with caching.
        
        Args:
            category: Optional category filter
            limit: Maximum number of templates to return
            offset: Number of templates to skip
            
        Returns:
            List[Dict[str, Any]]: List of templates
        """
        return self.list_templates(category, limit, offset)
    
    @with_cache(ttl=1800, prefix="template_storage")  # Cache for 30 minutes
    async def get_template_adaptation_cached(
        self,
        template_id: str,
        site_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get an adapted template for a site or project with caching.
        
        Args:
            template_id: ID of the original template
            site_id: Optional site ID
            project_id: Optional project ID
            
        Returns:
            Optional[Dict[str, Any]]: Adapted template if found, None otherwise
        """
        return self.get_template_adaptation(template_id, site_id, project_id)
    
    def invalidate_template_cache(self, template_id: str) -> None:
        """
        Invalidate cache for a specific template when it's updated or deleted.
        
        Args:
            template_id: ID of the template to invalidate in cache
        """
        # This method would use the CacheManager directly to invalidate specific keys
        # In a real implementation, you would need to:
        # 1. Create a key pattern matching the template_id 
        # 2. Use CacheManager.invalidate_pattern() to remove matching keys
        logger.info(f"Cache invalidation for template {template_id} would happen here")
        # Implementation would depend on the specific cache backend and key structure
    
    def invalidate_adaptation_cache(self, template_id: str, site_id: Optional[str] = None, project_id: Optional[str] = None) -> None:
        """
        Invalidate cache for adapted templates when they're updated or deleted.
        
        Args:
            template_id: ID of the original template
            site_id: Optional site ID
            project_id: Optional project ID
        """
        # This method would use the CacheManager directly to invalidate specific keys
        # In a real implementation, you would need to:
        # 1. Create a key pattern matching the template_id, site_id, and project_id
        # 2. Use CacheManager.invalidate_pattern() to remove matching keys
        logger.info(f"Cache invalidation for template adaptation {template_id} would happen here")
        # Implementation would depend on the specific cache backend and key structure 