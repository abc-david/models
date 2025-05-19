"""
File: services/models/core/base_model.py
MODULE: Base Models
PURPOSE: Provides base classes and interfaces for content models
DEPENDENCIES: None

This module defines the core interfaces and base classes for content models
used throughout the Content Generator application. These abstractions ensure
consistent model handling across different services.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional, Union, Type, ClassVar
from abc import ABC, abstractmethod


class ModelType(str, Enum):
    """Enumeration of supported model types."""
    CONTENT = "content"
    TEMPLATE = "template"
    CONFIG = "config"
    SYSTEM = "system"
    CUSTOM = "custom"


class FieldDefinition:
    """Definition of a model field with type and validation information."""
    
    def __init__(
        self,
        name: str,
        field_type: str,
        required: bool = True,
        default: Any = None,
        description: str = "",
        validators: List[Dict[str, Any]] = None
    ):
        """
        Initialize a field definition.
        
        Args:
            name: Field name
            field_type: Data type (e.g., 'str', 'int', 'List[str]')
            required: Whether the field is required
            default: Default value if not provided
            description: Field description
            validators: Custom validators for the field
        """
        self.name = name
        self.field_type = field_type
        self.required = required
        self.default = default
        self.description = description
        self.validators = validators or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert field definition to dictionary."""
        return {
            "name": self.name,
            "type": self.field_type,
            "required": self.required,
            "default": self.default,
            "description": self.description,
            "validators": self.validators
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FieldDefinition':
        """Create field definition from dictionary."""
        return cls(
            name=data["name"],
            field_type=data["type"],
            required=data.get("required", True),
            default=data.get("default"),
            description=data.get("description", ""),
            validators=data.get("validators", [])
        )


class BaseModel(ABC):
    """
    Base abstract class for all content models.
    
    This class defines the interface for model definitions
    and provides common functionality for all models.
    """
    
    model_type: ClassVar[ModelType] = ModelType.CUSTOM
    model_name: ClassVar[str] = "base_model"
    
    @classmethod
    @abstractmethod
    def get_fields(cls) -> Dict[str, FieldDefinition]:
        """Get field definitions for the model."""
        pass
    
    @classmethod
    def get_validators(cls) -> List[Dict[str, Any]]:
        """Get custom validators for the model."""
        return []
    
    @classmethod
    def to_schema(cls) -> Dict[str, Any]:
        """Convert model to schema dictionary."""
        return {
            "model_name": cls.model_name,
            "model_type": cls.model_type.value,
            "fields": {
                name: field.to_dict()
                for name, field in cls.get_fields().items()
            },
            "validators": cls.get_validators()
        }
    
    @classmethod
    def from_schema(cls, schema: Dict[str, Any]) -> Type['BaseModel']:
        """Create a model class from a schema definition."""
        # This would be implemented by specific model implementations
        raise NotImplementedError("Must be implemented by subclasses")


class ContentModel(BaseModel):
    """Base class for content models like articles, blog posts, etc."""
    
    model_type = ModelType.CONTENT


class TemplateModel(BaseModel):
    """Base class for template models."""
    
    model_type = ModelType.TEMPLATE


class ConfigModel(BaseModel):
    """Base class for configuration models."""
    
    model_type = ModelType.CONFIG


class SystemModel(BaseModel):
    """Base class for internal system models."""
    
    model_type = ModelType.SYSTEM 