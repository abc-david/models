"""
File: services/models/schemas/pydantic_schema.py
MODULE: Pydantic Schema Utilities
PURPOSE: Provides utilities for working with Pydantic schemas
DEPENDENCIES:
    - Pydantic for schema generation

This module provides utilities for working with Pydantic schemas,
including converting between Pydantic models and our internal model schema format.
"""

import inspect
from typing import Dict, List, Any, Type, get_type_hints, Union, Optional
from pydantic import BaseModel, Field, create_model
from datetime import datetime

# Type mapping between Python types and string representations
TYPE_MAPPING = {
    str: "str",
    int: "int",
    float: "float",
    bool: "bool",
    list: "List[Any]",
    dict: "Dict[str, Any]",
    datetime: "datetime",
    None: "None",
    type(None): "None"
}


def get_type_string(field_type) -> str:
    """
    Convert a Python type to a string representation.
    
    Args:
        field_type: Type to convert
        
    Returns:
        String representation of the type
    """
    # Handle basic types
    if field_type in TYPE_MAPPING:
        return TYPE_MAPPING[field_type]
    
    # Handle generic types with args (List, Dict, etc.)
    origin = getattr(field_type, "__origin__", None)
    args = getattr(field_type, "__args__", [])
    
    if origin is list:
        inner_type = get_type_string(args[0]) if args else "Any"
        return f"List[{inner_type}]"
    elif origin is dict:
        key_type = get_type_string(args[0]) if len(args) > 0 else "str"
        value_type = get_type_string(args[1]) if len(args) > 1 else "Any"
        return f"Dict[{key_type}, {value_type}]"
    elif origin is Union:
        types = [get_type_string(arg) for arg in args]
        return f"Union[{', '.join(types)}]"
    elif origin is Optional:
        inner_type = get_type_string(args[0]) if args else "Any"
        return f"Optional[{inner_type}]"
    
    # Handle classes
    if inspect.isclass(field_type):
        return field_type.__name__
    
    # Default
    return "Any"


def pydantic_to_model_schema(model_class: Type[BaseModel]) -> Dict[str, Any]:
    """
    Convert a Pydantic model class to our internal model schema format.
    
    Args:
        model_class: Pydantic model class to convert
        
    Returns:
        Model schema in our internal format
    """
    # Get model name
    model_name = model_class.__name__
    
    # Get field definitions
    fields = {}
    for name, field in model_class.__fields__.items():
        field_type = get_type_string(field.type_)
        required = field.required
        default = field.default if field.default is not ... else None
        description = field.field_info.description or ""
        
        # Extract validators
        validators = []
        if hasattr(field, "validators"):
            for validator in field.validators:
                validator_name = validator.__name__
                validators.append({
                    "name": validator_name,
                    "fields": [name]
                })
        
        fields[name] = {
            "name": name,
            "type": field_type,
            "required": required,
            "args": {
                "default": default,
                "description": description
            },
            "validators": validators
        }
    
    # Get model validators
    validators = []
    if hasattr(model_class, "validators"):
        for validator in model_class.validators:
            validator_name = validator.__name__
            validator_fields = getattr(validator, "fields", [])
            validators.append({
                "name": validator_name,
                "fields": validator_fields
            })
    
    # Build schema
    schema = {
        "model_name": model_name,
        "fields": fields,
        "validators": validators
    }
    
    return schema


def model_schema_to_pydantic(model_schema: Dict[str, Any]) -> Type[BaseModel]:
    """
    Convert our internal model schema to a Pydantic model class.
    
    Args:
        model_schema: Model schema in our internal format
        
    Returns:
        Pydantic model class
    """
    # Get model name
    model_name = model_schema.get("model_name", "DynamicModel")
    
    # Create field definitions
    fields = {}
    for name, field_def in model_schema.get("fields", {}).items():
        field_type = field_def.get("type", "Any")
        required = field_def.get("required", True)
        args = field_def.get("args", {})
        
        # Set default
        default = args.get("default")
        if default is None and not required:
            default = None
        elif required:
            default = ...
        
        # Create field with metadata
        description = args.get("description", "")
        fields[name] = (field_type, Field(default=default, description=description))
    
    # Create model class
    model = create_model(model_name, **fields)
    
    # Add validators (would require more complex logic)
    # This is a simplified version
    
    return model 