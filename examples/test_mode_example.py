"""
MODULE: services/models/examples/test_mode_example.py
PURPOSE: Demonstrate how to use different test modes with the model service
DEPENDENCIES:
    - services.models.testing: For test mode decorators
    - services.models.orchestrator: For model operations
    - asyncio: For async execution

This example demonstrates how to use the different test modes (None, 'mock', 'e2e')
with the model service for testing and development purposes.

Example usage:
```
python -m services.models.examples.test_mode_example
```
"""

import asyncio
import json
import logging
from typing import Dict, Any

# Import model components
from services.models.orchestrator import ModelOrchestrator
from services.models.testing import with_model_test_mode

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def pretty_print(data: Any) -> None:
    """Pretty print data as JSON."""
    print(json.dumps(data, indent=2, default=str))


@with_model_test_mode(mode=None)  # Production mode (no test mode)
async def demo_production_mode(orchestrator: ModelOrchestrator) -> None:
    """
    Demonstrate using the ModelOrchestrator in production mode.
    
    Args:
        orchestrator: The model orchestrator instance
    """
    print("\n=== Production Mode Example ===\n")
    print("Using production database connection:")
    print(f"  Test Mode: {orchestrator.test_mode}")
    
    print("\nIn production mode:")
    print("1. Connects to the real production database")
    print("2. Model operations affect real data")
    print("3. Changes are persistent and affect the real system")
    
    print("\nExample query (limited to avoid affecting production data):")
    try:
        models = await orchestrator.list_models_in_db()
        print(f"\nFound {len(models)} models in production database:")
        for model in models[:3]:  # Show only first 3 to limit output
            print(f"  - {model['name']} (type: {model['object_type']}, version: {model['version']})")
        
        if len(models) > 3:
            print(f"  - ... and {len(models) - 3} more")
    except Exception as e:
        print(f"Error accessing production database: {e}")


@with_model_test_mode(mode='e2e')  # End-to-end test mode
async def demo_e2e_mode(orchestrator: ModelOrchestrator) -> None:
    """
    Demonstrate using the ModelOrchestrator in end-to-end test mode.
    
    Args:
        orchestrator: The model orchestrator instance
    """
    print("\n=== End-to-End Test Mode Example ===\n")
    print("Using test database connection:")
    print(f"  Test Mode: {orchestrator.test_mode}")
    
    print("\nIn e2e mode:")
    print("1. Connects to a test database instead of production")
    print("2. Changes affect the test database")
    print("3. Allows testing with real database interactions")
    print("4. Safe to make changes without affecting production")
    
    print("\nExample query:")
    try:
        models = await orchestrator.list_models_in_db()
        print(f"\nFound {len(models)} models in test database:")
        for model in models:
            print(f"  - {model['name']} (type: {model['object_type']}, version: {model['version']})")
            
        # Test inserting a model definition (only in test mode)
        test_model = {
            "name": "test_example_model",
            "fields": {
                "id": {"type": "UUID", "primary": True},
                "name": {"type": "str", "required": True},
                "description": {"type": "str", "required": False},
                "created_at": {"type": "datetime", "auto_now": True}
            }
        }
        
        print("\nRegistering test model in test database...")
        model_id = await orchestrator.register_model_in_db(
            "test_example_model",
            test_model,
            "Example model for testing",
            model_type="alpha",
            version="1.0"
        )
        
        print(f"Registered test model with ID: {model_id}")
        
        # Verify the model was added
        models_after = await orchestrator.list_models_in_db()
        print(f"\nAfter insert: Found {len(models_after)} models in test database")
        
    except Exception as e:
        print(f"Error in e2e mode: {e}")


@with_model_test_mode(mode='mock')  # Mock mode
async def demo_mock_mode(orchestrator: ModelOrchestrator) -> None:
    """
    Demonstrate using the ModelOrchestrator in mock mode.
    
    Args:
        orchestrator: The model orchestrator instance
    """
    print("\n=== Mock Mode Example ===\n")
    print("Using mock database:")
    print(f"  Test Mode: {orchestrator.test_mode}")
    
    print("\nIn mock mode:")
    print("1. No actual database connection is used")
    print("2. Model operations return realistic mock data")
    print("3. No changes are persisted anywhere")
    print("4. Fastest test mode and doesn't require database setup")
    
    print("\nExample model operations:")
    try:
        # List models (will return mock data)
        models = await orchestrator.list_models_in_db()
        print("\nMock model list:")
        pretty_print(models[:2])
        
        # Get a mock model definition
        model = await orchestrator.get_model_definition_from_db("example_model")
        print("\nMock model definition:")
        pretty_print(model)
        
        # Register a mock model
        test_model = {
            "name": "test_mock_model",
            "fields": {
                "id": {"type": "UUID", "primary": True},
                "content": {"type": "str"},
                "tags": {"type": "json"}
            }
        }
        
        model_id = await orchestrator.register_model_in_db(
            "test_mock_model",
            test_model,
            "Test mock model",
            model_type="beta",
            version="1.0"
        )
        
        print(f"\nMock registration returned ID: {model_id}")
        
    except Exception as e:
        print(f"Error in mock mode: {e}")


async def main():
    """Run the model test mode demonstrations."""
    print("\n=== Model Service Test Modes Example ===")
    print("This example demonstrates the three test modes available:")
    print("1. Production mode (no test_mode)")
    print("2. End-to-end test mode (test_mode='e2e')")
    print("3. Mock mode (test_mode='mock')")
    
    # Decide which demos to run
    run_production = False  # Set to True if you want to see production mode (be careful!)
    run_e2e = True
    run_mock = True
    
    # Run the selected demos
    if run_production:
        await demo_production_mode()
    
    if run_e2e:
        try:
            await demo_e2e_mode()
        except Exception as e:
            print(f"\nError in e2e mode demo: {e}")
            print("Make sure your test database is properly configured.")
    
    if run_mock:
        await demo_mock_mode()
    
    print("\n=== Example Complete ===\n")

if __name__ == "__main__":
    asyncio.run(main()) 