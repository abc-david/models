"""
File: services/models/schemas/converters.py
MODULE: Schema Converters
PURPOSE: Provides utilities for converting between different schema formats
DEPENDENCIES: None

This module provides utilities for converting between different schema formats,
including JSON Schema, OpenAPI schema, and our internal model schema format.
"""

import re
from typing import Dict, List, Any, Optional, Tuple


def json_schema_to_model_schema(json_schema: Dict[str, Any], model_name: str = None) -> Dict[str, Any]:
    """
    Convert a JSON Schema to our internal model schema format.
    
    Args:
        json_schema: JSON Schema to convert
        model_name: Name for the model (defaults to schema title if available)
        
    Returns:
        Model schema in our internal format
    """
    # Get model name from schema title if not provided
    if model_name is None:
        model_name = json_schema.get("title", "UnnamedModel")
    
    # Get field definitions
    properties = json_schema.get("properties", {})
    required_fields = json_schema.get("required", [])
    
    fields = {}
    for name, prop in properties.items():
        field_type = _json_schema_type_to_model_type(prop)
        required = name in required_fields
        description = prop.get("description", "")
        default = prop.get("default")
        
        fields[name] = {
            "name": name,
            "type": field_type,
            "required": required,
            "args": {
                "default": default,
                "description": description
            }
        }
    
    # Build schema
    schema = {
        "model_name": model_name,
        "fields": fields,
        "validators": []  # JSON Schema doesn't have direct validator equivalents
    }
    
    return schema


def model_schema_to_json_schema(model_schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert our internal model schema to a JSON Schema.
    
    Args:
        model_schema: Model schema in our internal format
        
    Returns:
        JSON Schema
    """
    # Get model name
    model_name = model_schema.get("model_name", "UnnamedModel")
    
    # Build properties
    properties = {}
    required = []
    
    for name, field_def in model_schema.get("fields", {}).items():
        field_type = field_def.get("type", "Any")
        is_required = field_def.get("required", True)
        args = field_def.get("args", {})
        
        # Convert field type to JSON Schema type
        json_type, format_type = _model_type_to_json_schema_type(field_type)
        
        # Build property
        prop = {
            "type": json_type
        }
        
        # Add format if available
        if format_type:
            prop["format"] = format_type
        
        # Add description if available
        description = args.get("description")
        if description:
            prop["description"] = description
        
        # Add default if available
        default = args.get("default")
        if default is not None:
            prop["default"] = default
        
        # Add to properties
        properties[name] = prop
        
        # Add to required list if required
        if is_required:
            required.append(name)
    
    # Build JSON Schema
    json_schema = {
        "title": model_name,
        "type": "object",
        "properties": properties,
        "required": required
    }
    
    return json_schema


def _json_schema_type_to_model_type(property_def: Dict[str, Any]) -> str:
    """
    Convert a JSON Schema type to our internal model type.
    
    Args:
        property_def: JSON Schema property definition
        
    Returns:
        Model type string
    """
    json_type = property_def.get("type")
    format_type = property_def.get("format")
    
    # Handle string types
    if json_type == "string":
        if format_type == "date-time":
            return "datetime"
        return "str"
    
    # Handle number types
    elif json_type == "number":
        return "float"
    elif json_type == "integer":
        return "int"
    
    # Handle boolean
    elif json_type == "boolean":
        return "bool"
    
    # Handle null
    elif json_type == "null":
        return "None"
    
    # Handle arrays
    elif json_type == "array":
        items = property_def.get("items", {})
        if items:
            item_type = _json_schema_type_to_model_type(items)
            return f"List[{item_type}]"
        return "List[Any]"
    
    # Handle objects
    elif json_type == "object":
        return "Dict[str, Any]"
    
    # Default
    return "Any"


def _model_type_to_json_schema_type(model_type: str) -> Tuple[str, Optional[str]]:
    """
    Convert our internal model type to a JSON Schema type.
    
    Args:
        model_type: Model type string
        
    Returns:
        Tuple of (json_type, format)
    """
    # Handle basic types
    if model_type == "str":
        return "string", None
    elif model_type == "int":
        return "integer", None
    elif model_type == "float":
        return "number", None
    elif model_type == "bool":
        return "boolean", None
    elif model_type == "None":
        return "null", None
    elif model_type == "datetime":
        return "string", "date-time"
    elif model_type == "Any" or model_type == "any":
        return "object", None
    
    # Handle List types
    list_match = re.match(r"List\[(.*)\]", model_type)
    if list_match:
        inner_type = list_match.group(1)
        json_type, format_type = _model_type_to_json_schema_type(inner_type)
        return "array", None
    
    # Handle Dict types
    dict_match = re.match(r"Dict\[(.*),(.*)\]", model_type)
    if dict_match:
        return "object", None
    
    # Default
    return "object", None 