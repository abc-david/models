"""
File: services/models/validation/validator.py
MODULE: Model Validation
PURPOSE: Provides validation functionality for data against model schemas
DEPENDENCIES:
    - Type validation utilities

This module provides a centralized validation service for checking data 
against model schemas. It supports both direct validation against model 
definitions and validation through Pydantic models when available.
"""

import re
import logging
from typing import Dict, List, Any, Tuple, Optional, Type, Union
from datetime import datetime

from services.models.core.base_model import BaseModel
from services.models.validation.type_validators import TypeValidator

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Exception raised for validation errors."""
    
    def __init__(self, message: str, errors: List[Dict[str, Any]] = None):
        """
        Initialize validation error.
        
        Args:
            message: Error message
            errors: List of validation errors
        """
        self.message = message
        self.errors = errors or []
        super().__init__(self.message)


class ValidationResult:
    """
    Container for validation results.
    
    Attributes:
        is_valid: Whether the data is valid
        errors: List of validation errors
        warnings: List of validation warnings
        validated_data: The validated data after any coercion
    """
    
    def __init__(
        self,
        is_valid: bool = True,
        errors: List[Dict[str, Any]] = None,
        warnings: List[Dict[str, Any]] = None,
        validated_data: Optional[Dict[str, Any]] = None,
        original_data: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize validation result.
        
        Args:
            is_valid: Whether the data is valid
            errors: List of validation errors
            warnings: List of validation warnings
            validated_data: The validated data after coercion
            original_data: The original data before validation
        """
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []
        self.validated_data = validated_data
        self.original_data = original_data
    
    def add_error(self, path: str, message: str, code: str = "invalid") -> None:
        """
        Add an error to the validation result.
        
        Args:
            path: Path to the field with the error
            message: Error message
            code: Error code
        """
        self.errors.append({
            "path": path,
            "message": message,
            "code": code
        })
        self.is_valid = False
    
    def add_warning(self, path: str, message: str, code: str = "warning") -> None:
        """
        Add a warning to the validation result.
        
        Args:
            path: Path to the field with the warning
            message: Warning message
            code: Warning code
        """
        self.warnings.append({
            "path": path,
            "message": message,
            "code": code
        })


class ModelValidator:
    """
    Validates data against model schemas.
    
    This class provides methods for validating data against model schemas,
    with support for different validation strategies depending on the context.
    """
    
    def __init__(self):
        """Initialize the model validator."""
        self.type_validator = TypeValidator()
    
    def validate_against_model(
        self,
        data: Dict[str, Any],
        model_schema: Dict[str, Any],
        partial: bool = False
    ) -> ValidationResult:
        """
        Validate data against a model schema.
        
        Args:
            data: Data to validate
            model_schema: Model schema to validate against
            partial: Whether to allow partial validation (missing fields)
            
        Returns:
            ValidationResult containing validation status and details
        """
        result = ValidationResult(original_data=data)
        
        # Validate required fields
        for field_name, field_def in model_schema.get("fields", {}).items():
            is_required = field_def.get("required", True)
            
            if field_name not in data:
                # Check if field is required
                if is_required and not partial and "default" not in field_def.get("args", {}):
                    result.add_error(field_name, f"Missing required field: {field_name}")
                continue
            
            # Type validation
            field_type = field_def.get("type", "Any")
            field_value = data[field_name]
            
            type_valid, error_message = self.type_validator.validate_type(field_value, field_type)
            if not type_valid:
                result.add_error(field_name, f"Invalid type for {field_name}: {error_message}")
        
        # Run custom validators if no errors so far
        if result.is_valid:
            for validator in model_schema.get("validators", []):
                try:
                    # Execute validator code
                    validator_code = validator.get("code", "")
                    if validator_code:
                        local_vars = {"data": data, "result": result}
                        exec(validator_code, {}, local_vars)
                except Exception as e:
                    validator_name = validator.get("name", "unknown")
                    result.add_error("", f"Validator {validator_name} failed: {str(e)}")
        
        # Set validated data if valid
        if result.is_valid:
            result.validated_data = data.copy()
        
        return result
    
    def validate_with_model_class(
        self,
        data: Dict[str, Any],
        model_class: Type[BaseModel],
        partial: bool = False
    ) -> ValidationResult:
        """
        Validate data against a model class.
        
        Args:
            data: Data to validate
            model_class: Model class to validate against
            partial: Whether to allow partial validation (missing fields)
            
        Returns:
            ValidationResult containing validation status and details
        """
        # Convert model class to schema
        model_schema = model_class.to_schema()
        
        # Validate against schema
        return self.validate_against_model(data, model_schema, partial)
    
    def validate_with_pydantic(
        self,
        data: Dict[str, Any],
        pydantic_model,
        partial: bool = False
    ) -> ValidationResult:
        """
        Validate data using a Pydantic model.
        
        Args:
            data: Data to validate
            pydantic_model: Pydantic model class
            partial: Whether to allow partial validation
            
        Returns:
            ValidationResult containing validation status and details
        """
        result = ValidationResult(original_data=data)
        
        try:
            # Handle partial validation
            if partial:
                # Only validate fields that are present
                partial_data = {k: v for k, v in data.items() if k in data}
                model_instance = pydantic_model.parse_obj(partial_data)
            else:
                model_instance = pydantic_model.parse_obj(data)
            
            # Successfully validated
            result.validated_data = model_instance.dict()
            
        except Exception as e:
            result.is_valid = False
            
            # Handle Pydantic validation errors
            if hasattr(e, "errors"):
                for error in e.errors():
                    path = ".".join(str(p) for p in error.get("loc", []))
                    message = error.get("msg", "Unknown error")
                    code = error.get("type", "validation_error")
                    result.add_error(path, message, code)
            else:
                # Generic error
                result.add_error("", str(e))
        
        return result 