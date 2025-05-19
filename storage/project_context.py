"""
MODULE: services/models/storage/project_context.py
PURPOSE: Storage operations for project context
CLASSES:
    - ProjectContextStorage: Database operations for project context
DEPENDENCIES:
    - services.database.db_connector: For database operations
    - uuid: For ID generation
    - datetime: For timestamp management
"""

import logging
import uuid
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from services.database.db_connector import DBConnector

logger = logging.getLogger(__name__)

class ProjectContextStorage:
    """
    Storage operations for project context.
    
    This class handles database operations for storing, retrieving,
    updating, and deleting project context data.
    """
    
    def __init__(self, schema: str = "public"):
        """
        Initialize project context storage.
        
        Args:
            schema: Database schema name
        """
        self.schema = schema
        self.db = DBConnector()
    
    async def store_context(
        self,
        context: Dict[str, Any],
        context_params: Dict[str, Any],
        project_uuid: Optional[str] = None
    ) -> str:
        """
        Store context in database.
        
        Args:
            context: Context data to store
            context_params: Parameters used to retrieve the context
            project_uuid: Optional project UUID for project-scoped context
            
        Returns:
            ID of stored context
        """
        try:
            # Generate a new context ID
            context_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            # Convert dictionaries to JSON strings
            context_json = json.dumps(context)
            params_json = json.dumps(context_params)
            
            # Insert into database
            query = f"""
                INSERT INTO {self.schema}.context (
                    id, context, params, project_id, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
            """
            
            params = [context_id, context_json, params_json, project_uuid, now, now]
            result = await self.db.fetch_one(query, params)
            
            return result['id'] if result else context_id
            
        except Exception as e:
            logger.error(f"Failed to store context: {str(e)}")
            raise
    
    async def get_context(
        self,
        context_id: Optional[str] = None,
        context_params: Optional[Dict[str, Any]] = None,
        project_uuid: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get context from database.
        
        Args:
            context_id: Optional ID of context to retrieve
            context_params: Optional parameters to match
            project_uuid: Optional project UUID for project-scoped context
            
        Returns:
            Context if found, None otherwise
        """
        try:
            # Query by ID or params
            if context_id:
                query = f"""
                    SELECT context FROM {self.schema}.context
                    WHERE id = $1
                    AND (project_id = $2 OR project_id IS NULL)
                """
                
                result = await self.db.fetch_one(query, [context_id, project_uuid])
                
            elif context_params:
                # Convert params to JSON for comparison
                params_json = json.dumps(context_params)
                
                query = f"""
                    SELECT context FROM {self.schema}.context
                    WHERE params = $1
                    AND (project_id = $2 OR project_id IS NULL)
                    ORDER BY updated_at DESC
                    LIMIT 1
                """
                
                result = await self.db.fetch_one(query, [params_json, project_uuid])
                
            else:
                logger.error("Either context_id or context_params must be provided")
                return None
            
            # Parse context from JSON
            if result and 'context' in result:
                return json.loads(result['context'])
                
            return None
            
        except Exception as e:
            logger.error(f"Failed to get context: {str(e)}")
            return None
    
    async def update_context(
        self,
        context_id: str,
        context: Dict[str, Any],
        project_uuid: Optional[str] = None
    ) -> bool:
        """
        Update stored context.
        
        Args:
            context_id: ID of context to update
            context: Updated context
            project_uuid: Optional project UUID for project-scoped context
            
        Returns:
            True if update succeeded, False otherwise
        """
        try:
            # Convert context to JSON
            context_json = json.dumps(context)
            now = datetime.utcnow()
            
            # Update in database
            query = f"""
                UPDATE {self.schema}.context
                SET context = $1, updated_at = $2
                WHERE id = $3
                AND (project_id = $4 OR project_id IS NULL)
            """
            
            params = [context_json, now, context_id, project_uuid]
            result = await self.db.update(query, params)
            
            # Check if any rows were affected
            return result > 0
            
        except Exception as e:
            logger.error(f"Failed to update context: {str(e)}")
            return False
    
    async def delete_context(
        self,
        context_id: str,
        project_uuid: Optional[str] = None
    ) -> bool:
        """
        Delete stored context.
        
        Args:
            context_id: ID of context to delete
            project_uuid: Optional project UUID for project-scoped context
            
        Returns:
            True if deletion succeeded, False otherwise
        """
        try:
            # Delete from database
            query = f"""
                DELETE FROM {self.schema}.context
                WHERE id = $1
                AND (project_id = $2 OR project_id IS NULL)
            """
            
            params = [context_id, project_uuid]
            result = await self.db.delete(query, params)
            
            # Check if any rows were affected
            return result > 0
            
        except Exception as e:
            logger.error(f"Failed to delete context: {str(e)}")
            return False 