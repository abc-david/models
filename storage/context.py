"""
MODULE: services/models/storage/context.py
PURPOSE: Defines the Context model for storing context data
CLASSES:
    - Context: Model for storing context data in PostgreSQL
DEPENDENCIES:
    - tortoise-orm: For ORM functionality
    - uuid: For UUID generation
"""

from tortoise import fields, models
from uuid import uuid4
from datetime import datetime
from typing import Dict, Any, Optional

class Context(models.Model):
    """
    Model for storing context data in PostgreSQL.
    
    This model stores context data with associated metadata and parameters.
    It supports project-scoped context and includes timestamps for tracking
    creation and updates.
    """
    
    id = fields.UUIDField(pk=True, default=uuid4)
    type = fields.CharField(max_length=255, description="Type of context")
    data = fields.JSONField(description="Context data and metadata")
    project_uuid = fields.UUIDField(null=True, description="Optional project UUID for project-scoped context")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "contexts"
        table_description = "Stores context data with associated metadata"
    
    @classmethod
    async def create(
        cls,
        type: str,
        data: Dict[str, Any],
        project_uuid: Optional[str] = None
    ) -> "Context":
        """
        Create a new context entry.
        
        Args:
            type: Type of context
            data: Context data and metadata
            project_uuid: Optional project UUID
            
        Returns:
            Created Context instance
        """
        return await super().create(
            type=type,
            data=data,
            project_uuid=project_uuid
        )
    
    @classmethod
    async def get_by_id(cls, context_id: str) -> Optional["Context"]:
        """
        Get context by ID.
        
        Args:
            context_id: Context ID
            
        Returns:
            Context instance if found, None otherwise
        """
        return await cls.get_or_none(id=context_id)
    
    @classmethod
    async def get_by_project(cls, project_uuid: str) -> list["Context"]:
        """
        Get all contexts for a project.
        
        Args:
            project_uuid: Project UUID
            
        Returns:
            List of Context instances
        """
        return await cls.filter(project_uuid=project_uuid)
    
    @classmethod
    async def get_by_type(cls, type: str, project_uuid: Optional[str] = None) -> list["Context"]:
        """
        Get contexts by type.
        
        Args:
            type: Context type
            project_uuid: Optional project UUID
            
        Returns:
            List of Context instances
        """
        query = cls.filter(type=type)
        if project_uuid:
            query = query.filter(project_uuid=project_uuid)
        return await query 