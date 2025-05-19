"""
File: services/models/validation/type_validators.py
MODULE: Type Validators
PURPOSE: Provides validation for different data types
DEPENDENCIES: None

This module provides validator functions for different data types,
including basic types, collections, and custom types.
"""

import re
from typing import Any, Dict, List, Tuple, Optional, Union
from datetime import datetime


class TypeValidator:
    """
    Validator for different data types.
    
    This class provides methods for validating values against different
    data types, with support for complex type expressions.
    """
    
    def validate_type(self, value: Any, expected_type: str) -> Tuple[bool, str]:
        """
        Validate a value against an expected type.
        
        Args:
            value: Value to validate
            expected_type: Expected type as string (e.g., "str", "List[str]")
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        expected_type = expected_type.strip()
        
        # Handle basic types
        if expected_type == "str":
            return self._validate_string(value)
        elif expected_type == "int":
            return self._validate_integer(value)
        elif expected_type == "float":
            return self._validate_float(value)
        elif expected_type == "bool":
            return self._validate_boolean(value)
        elif expected_type == "Any" or expected_type == "any":
            return True, ""
        elif expected_type == "None" or expected_type == "none":
            return self._validate_none(value)
        elif expected_type == "datetime":
            return self._validate_datetime(value)
        
        # Handle List types
        list_match = re.match(r"List\[(.*)\]", expected_type)
        if list_match:
            return self._validate_list(value, list_match.group(1))
        
        # Handle Dict types
        dict_match = re.match(r"Dict\[(.*),(.*)\]", expected_type)
        if dict_match:
            return self._validate_dict(value, dict_match.group(1), dict_match.group(2))
        
        # Handle Union types
        union_match = re.match(r"Union\[(.*)\]", expected_type)
        if union_match:
            return self._validate_union(value, union_match.group(1))
        
        # Handle Optional types
        optional_match = re.match(r"Optional\[(.*)\]", expected_type)
        if optional_match:
            return self._validate_optional(value, optional_match.group(1))
        
        # If we get here, the type is not supported
        return False, f"unsupported type: {expected_type}"
    
    def _validate_string(self, value: Any) -> Tuple[bool, str]:
        """Validate a string value."""
        if isinstance(value, str):
            return True, ""
        return False, f"expected string, got {type(value).__name__}"
    
    def _validate_integer(self, value: Any) -> Tuple[bool, str]:
        """Validate an integer value."""
        if isinstance(value, int) and not isinstance(value, bool):
            return True, ""
        return False, f"expected integer, got {type(value).__name__}"
    
    def _validate_float(self, value: Any) -> Tuple[bool, str]:
        """Validate a float value."""
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return True, ""
        return False, f"expected number, got {type(value).__name__}"
    
    def _validate_boolean(self, value: Any) -> Tuple[bool, str]:
        """Validate a boolean value."""
        if isinstance(value, bool):
            return True, ""
        return False, f"expected boolean, got {type(value).__name__}"
    
    def _validate_none(self, value: Any) -> Tuple[bool, str]:
        """Validate a None value."""
        if value is None:
            return True, ""
        return False, f"expected None, got {type(value).__name__}"
    
    def _validate_datetime(self, value: Any) -> Tuple[bool, str]:
        """Validate a datetime value."""
        if isinstance(value, datetime):
            return True, ""
        elif isinstance(value, str):
            try:
                datetime.fromisoformat(value)
                return True, ""
            except ValueError:
                return False, "invalid datetime format"
        return False, f"expected datetime or ISO format string, got {type(value).__name__}"
    
    def _validate_list(self, value: Any, item_type: str) -> Tuple[bool, str]:
        """Validate a list value."""
        if not isinstance(value, list):
            return False, f"expected list, got {type(value).__name__}"
        
        # Validate each item in the list
        for index, item in enumerate(value):
            is_valid, error = self.validate_type(item, item_type)
            if not is_valid:
                return False, f"invalid item at index {index}: {error}"
        
        return True, ""
    
    def _validate_dict(self, value: Any, key_type: str, value_type: str) -> Tuple[bool, str]:
        """Validate a dictionary value."""
        if not isinstance(value, dict):
            return False, f"expected dictionary, got {type(value).__name__}"
        
        # Validate each key-value pair
        for k, v in value.items():
            # Validate key
            key_valid, key_error = self.validate_type(k, key_type)
            if not key_valid:
                return False, f"invalid key: {key_error}"
            
            # Validate value
            value_valid, value_error = self.validate_type(v, value_type)
            if not value_valid:
                return False, f"invalid value for key '{k}': {value_error}"
        
        return True, ""
    
    def _validate_union(self, value: Any, union_types: str) -> Tuple[bool, str]:
        """Validate a value against a union of types."""
        # Split the union types and normalize
        types = [t.strip() for t in union_types.split(",")]
        
        # Try each type
        errors = []
        for type_str in types:
            is_valid, error = self.validate_type(value, type_str)
            if is_valid:
                return True, ""
            errors.append(error)
        
        # If we get here, none of the types matched
        return False, f"value did not match any of the expected types: {', '.join(errors)}"
    
    def _validate_optional(self, value: Any, inner_type: str) -> Tuple[bool, str]:
        """Validate an optional value."""
        if value is None:
            return True, ""
        
        # Validate the inner type
        return self.validate_type(value, inner_type) 