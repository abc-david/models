"""
MODULE: services/models/testing/__init__.py
PURPOSE: Testing utilities for model operations
DEPENDENCIES:
    - services.models.testing.decorators: For test mode decorators

This module provides testing utilities for model operations, including
decorators for test mode configuration and test data setup.
"""

from services.models.testing.decorators import with_model_test_mode

# Export the decorator
__all__ = ["with_model_test_mode"]
