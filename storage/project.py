"""
MODULE: services/models/storage/project.py
PURPOSE: Defines the Project model for storing project data
CLASSES:
    - Project: Model for storing project data in PostgreSQL
DEPENDENCIES:
    - tortoise-orm: For ORM functionality
    - uuid: For UUID generation
"""

from tortoise import fields, models
from uuid import uuid4
from datetime import datetime
from typing import Dict, Any, Optional

class Project(models.Model):
    """
    Model for storing project data in PostgreSQL.
    
    This model stores project information and metadata.
    It includes timestamps for tracking creation and updates.
    """
    
    id = fields.UUIDField(pk=True, default=uuid4)
    name = fields.CharField(max_length=255, description="Project name")
    description = fields.TextField(null=True, description="Project description")
    metadata = fields.JSONField(default=dict, description="Project metadata")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "projects"
        table_description = "Stores project information and metadata"
    
    @classmethod
    async def create(
        cls,
        name: str,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "Project":
        """
        Create a new project.
        
        Args:
            name: Project name
            description: Optional project description
            metadata: Optional project metadata
            
        Returns:
            Created Project instance
        """
        return await super().create(
            name=name,
            description=description,
            metadata=metadata or {}
        )
    
    @classmethod
    async def get_by_id(cls, project_id: str) -> Optional["Project"]:
        """
        Get project by ID.
        
        Args:
            project_id: Project ID
            
        Returns:
            Project instance if found, None otherwise
        """
        return await cls.get_or_none(id=project_id)
    
    @classmethod
    async def get_by_name(cls, name: str) -> Optional["Project"]:
        """
        Get project by name.
        
        Args:
            name: Project name
            
        Returns:
            Project instance if found, None otherwise
        """
        return await cls.get_or_none(name=name) 