"""
MODULE: services/models/testing/decorators.py
PURPOSE: Decorators to facilitate testing of model operations
DEPENDENCIES:
    - services.models.orchestrator: For model orchestration
    - services.database.testing: For database testing utilities

This module provides decorators that simplify testing of model-related operations
with various test modes (production, end-to-end, mock).
"""

import functools
import logging
from typing import Any, Callable, Optional, TypeVar

from services.models.orchestrator import ModelOrchestrator

# Type variable for function return type
T = TypeVar('T')

logger = logging.getLogger(__name__)


def with_model_test_mode(mode: Optional[str] = None):
    """
    Decorator for configuring model operations with a specific test mode.
    
    This decorator creates a ModelOrchestrator instance with the specified
    test mode and injects it into the decorated function. It ensures proper
    resource cleanup after execution.
    
    Args:
        mode: Test mode to use:
            - None: Production mode (default)
            - 'e2e': End-to-end test mode (uses test database)
            - 'mock': Mock mode (no database connection)
            
    Returns:
        Decorator function
        
    Example usage:
    
    ```python
    @with_model_test_mode(mode='e2e')
    async def test_model_registration(orchestrator: ModelOrchestrator):
        # The orchestrator is already configured with e2e mode
        model_id = await orchestrator.register_model_in_db(...)
        # Test assertions...
    ```
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # Create orchestrator with specified test mode
            orchestrator = ModelOrchestrator(test_mode=mode)
            
            try:
                # Call the original function with the orchestrator
                return await func(orchestrator, *args, **kwargs)
            finally:
                # Ensure resources are cleaned up
                await orchestrator.close()
                
        return wrapper
    
    return decorator 