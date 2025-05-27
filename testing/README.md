# Models Testing Utilities

This directory contains utilities to facilitate testing of model operations within the Content Generator.

## Available Utilities

### Test Mode Decorator (`decorators.py`)

The `with_model_test_mode` decorator simplifies testing of model operations by automatically configuring a `ModelOrchestrator` instance with the specified test mode and injecting it into your test function.

```python
from services.models.testing import with_model_test_mode

# Test in end-to-end mode (using test database)
@with_model_test_mode(mode='e2e')
async def test_model_registration(orchestrator):
    # The orchestrator is already configured with e2e mode
    model_id = await orchestrator.register_model_in_db(
        "TestModel",
        {"fields": {"name": {"type": "str"}}},
        "Test description"
    )
    # Assertions...

# Test in mock mode (no database connection)
@with_model_test_mode(mode='mock')
async def test_model_validation(orchestrator):
    # The orchestrator is configured with mock mode
    result = await orchestrator.validate_data(
        "TestModel",
        {"name": "Test"}
    )
    # Assertions...

# Test in production mode (default)
@with_model_test_mode()
async def test_default_configuration(orchestrator):
    # Standard orchestrator configuration
    # ...
```

## Test Modes

The following test modes are available:

1. **Production Mode** (`None`, default): Uses the standard configuration with real database connections.
2. **End-to-End Mode** (`'e2e'`): Uses a test database for full integration testing.
3. **Mock Mode** (`'mock'`): Uses mocked components with no actual database connections.

## Benefits

Using these utilities provides several benefits:

1. **Consistent Setup**: Ensures consistent initialization of components for tests.
2. **Resource Cleanup**: Automatically cleans up resources after tests complete.
3. **Flexible Testing**: Allows for different levels of testing (unit, integration, end-to-end).
4. **Simplified Code**: Reduces boilerplate in test functions.

## Best Practices

When using these testing utilities:

1. Always use the appropriate test mode for your test requirements.
2. Keep tests focused on specific functionality.
3. Try to avoid mixing test modes within a single test function.
4. Use assertions to verify expected behavior.
5. Test both success and failure cases. 