"""
MODULE: services/models/exporters/pydantic_exporter.py
PURPOSE: Exports Pydantic models as JSON-compatible dictionaries
DEPENDENCIES:
    - services.models.core.model_registry: For retrieving model definitions
    - services.models.schemas.pydantic_schema: For schema conversion utilities
    - pydantic: For model validation and schema generation

This module provides utilities to export Pydantic model structures as JSON-compatible
dictionaries based on object names.
"""

import logging
from typing import Dict, List, Any, Optional, Union
import json

from pydantic import BaseModel
from services.models.core.model_registry import ModelRegistry
from services.models.schemas.pydantic_schema import (
    pydantic_to_model_schema, 
    model_schema_to_pydantic
)

logger = logging.getLogger(__name__)

async def export_object_schema(object_name: str) -> Dict[str, Any]:
    """
    Export a single object's schema as a JSON-compatible dictionary.
    
    Args:
        object_name: Name of the object model to export
        
    Returns:
        Dictionary containing the object's schema
        
    Raises:
        ValueError: If the object model cannot be found or converted
    """
    try:
        # Get the model schema from the registry
        model_schema = await ModelRegistry.get_schema(object_name)
        if not model_schema:
            raise ValueError(f"Object model '{object_name}' not found in registry")
        
        # Convert to a JSON-compatible dictionary
        schema_dict = {
            "model_name": model_schema.get("model_name", object_name),
            "fields": {}
        }
        
        # Process fields
        for field_name, field_info in model_schema.get("fields", {}).items():
            field_dict = {
                "type": field_info.get("type", "Any"),
                "required": field_info.get("required", False),
                "description": field_info.get("args", {}).get("description", ""),
            }
            
            # Add default value if present and not a complex object
            default = field_info.get("args", {}).get("default")
            if default is not None and isinstance(default, (str, int, float, bool)):
                field_dict["default"] = default
                
            schema_dict["fields"][field_name] = field_dict
            
        return schema_dict
        
    except Exception as e:
        logger.error(f"Error exporting schema for object '{object_name}': {str(e)}")
        raise ValueError(f"Failed to export schema for '{object_name}': {str(e)}")

async def export_multiple_object_schemas(object_names: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Export multiple object schemas as a dictionary of JSON-compatible dictionaries.
    
    Args:
        object_names: List of object model names to export
        
    Returns:
        Dictionary mapping object names to their schema dictionaries
    """
    result = {}
    errors = []
    
    for object_name in object_names:
        try:
            schema = await export_object_schema(object_name)
            result[object_name] = schema
        except ValueError as e:
            errors.append(str(e))
            logger.warning(f"Skipped exporting schema for '{object_name}': {str(e)}")
    
    if errors and not result:
        raise ValueError(f"Failed to export any schemas: {'; '.join(errors)}")
        
    return result

async def export_object_schemas_to_json(
    object_names: List[str], 
    output_file: Optional[str] = None,
    indent: int = 2
) -> Optional[str]:
    """
    Export multiple object schemas to a JSON string or file.
    
    Args:
        object_names: List of object model names to export
        output_file: Optional file path to write the JSON output
        indent: Indentation level for JSON formatting
        
    Returns:
        JSON string if output_file is None, otherwise None
        
    Raises:
        ValueError: If no schemas could be exported
    """
    schemas = await export_multiple_object_schemas(object_names)
    
    if not schemas:
        raise ValueError("No schemas were exported")
    
    # Convert to JSON
    json_output = json.dumps(schemas, indent=indent)
    
    # Write to file if specified
    if output_file:
        try:
            with open(output_file, 'w') as f:
                f.write(json_output)
            logger.info(f"Exported {len(schemas)} schemas to {output_file}")
            return None
        except Exception as e:
            logger.error(f"Error writing to file {output_file}: {str(e)}")
            raise ValueError(f"Failed to write to file {output_file}: {str(e)}")
    
    return json_output

class ObjectSchemaExporter:
    """
    Class-based exporter for Pydantic object schemas.
    
    This class provides methods to export object schemas as JSON-compatible
    dictionaries and can be instantiated with custom configuration.
    """
    
    def __init__(self, registry: Optional[ModelRegistry] = None):
        """
        Initialize the schema exporter.
        
        Args:
            registry: Optional custom model registry instance
        """
        self.registry = registry or ModelRegistry
    
    async def export_schema(self, object_name: str) -> Dict[str, Any]:
        """
        Export a single object's schema.
        
        Args:
            object_name: Name of the object model to export
            
        Returns:
            Dictionary containing the object's schema
        """
        try:
            # Get the model schema from the registry
            model_schema = await self.registry.get_schema(object_name)
            if not model_schema:
                raise ValueError(f"Object model '{object_name}' not found in registry")
            
            # Convert to a dictionary format
            return self._convert_schema_to_dict(model_schema, object_name)
        
        except Exception as e:
            logger.error(f"Error exporting schema for object '{object_name}': {str(e)}")
            raise ValueError(f"Failed to export schema for '{object_name}': {str(e)}")
    
    async def export_schemas(self, object_names: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Export multiple object schemas.
        
        Args:
            object_names: List of object model names to export
            
        Returns:
            Dictionary mapping object names to their schema dictionaries
        """
        result = {}
        errors = []
        
        for object_name in object_names:
            try:
                schema = await self.export_schema(object_name)
                result[object_name] = schema
            except ValueError as e:
                errors.append(str(e))
                logger.warning(f"Skipped exporting schema for '{object_name}': {str(e)}")
        
        if errors and not result:
            raise ValueError(f"Failed to export any schemas: {'; '.join(errors)}")
            
        return result
    
    def _convert_schema_to_dict(self, model_schema: Dict[str, Any], object_name: str) -> Dict[str, Any]:
        """
        Convert a model schema to a JSON-compatible dictionary.
        
        Args:
            model_schema: The model schema to convert
            object_name: The name of the object model
            
        Returns:
            Dictionary containing the converted schema
        """
        schema_dict = {
            "model_name": model_schema.get("model_name", object_name),
            "fields": {}
        }
        
        # Process fields
        for field_name, field_info in model_schema.get("fields", {}).items():
            field_dict = {
                "type": field_info.get("type", "Any"),
                "required": field_info.get("required", False),
                "description": field_info.get("args", {}).get("description", ""),
            }
            
            # Add default value if present and not a complex object
            default = field_info.get("args", {}).get("default")
            if default is not None and isinstance(default, (str, int, float, bool)):
                field_dict["default"] = default
                
            schema_dict["fields"][field_name] = field_dict
            
        return schema_dict 