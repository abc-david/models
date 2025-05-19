# Models Service

The Models Service provides a centralized system for defining, validating, and managing data models throughout the Content Generator. It bridges the gap between data validation and database operations, ensuring data integrity across the application.

## Key Features

- **Data Validation**: Define models with validation rules and validate data against these models
- **Database Integration**: Seamless integration with database operations
- **Schema Management**: Tools for verifying and maintaining database schemas
- **Centralized API**: Access all functionality through a simple, consistent API

## Architecture

The Models Service follows a flattened architecture with a central orchestrator:

```
services/models/
│
├── __init__.py             # Exports key components
├── orchestrator.py         # Central API for accessing all functionality
├── db_schema_inspector.py  # Tools for database schema verification 
│
├── core/                   # Core model definitions
│   ├── base_model.py       # Base model classes
│   └── model_registry.py   # Registry for model definitions
│
├── validation/             # Data validation
│   └── validator.py        # Model validation implementation
│
├── storage/                # Database storage
│   ├── db_storage.py       # Relational database storage
│   ├── vector_storage.py   # Vector database storage
│   ├── cached_storage.py   # Cached storage implementations
│   ├── models.py           # Storage-related model definitions
│   └── README.md           # Storage documentation
│
├── schemas/                # Schema definitions
│   └── ...                 # Model schema definitions
│
├── exporters/              # Data exporters
│   └── ...                 # Functionality for exporting model data
│
└── utils/                  # Utilities and tools
    ├── verify_models.py    # Schema verification utility
    ├── model_db_integration.py # Database integration examples
    └── README.md           # Documentation for utilities
```

## Storage Subsystem

The storage subsystem (`services/models/storage/`) provides a comprehensive solution for storing, retrieving, and validating content objects in both relational and vector databases:

- **DBObjectStorage**: Stores content in PostgreSQL with full validation and metadata support
- **VectorObjectStorage**: Stores content in vector databases for semantic search
- **Cached Implementations**: Performance-optimized cached versions of storage classes
- **Project Context Storage**: Contextual storage specific to projects and workflow stages

The storage system is built on the asynchronous database layer using `asyncpg` and implements advanced features like transaction management, batched operations, and cross-references between objects.

## Usage

### Basic Usage

```python
from services.models import orchestrator

# Get a model definition
topic_map_model = await orchestrator.get_model("topic_map")

# Validate data against a model
validation_result = await orchestrator.validate_data("topic_map", data)
if validation_result.is_valid:
    # Use the validated data
    valid_data = validation_result.valid_data
else:
    # Handle validation errors
    errors = validation_result.errors
```

### Database Schema Verification

```python
from services.models import SchemaInspector

# Create an inspector
inspector = SchemaInspector()

# Verify a model's schema against a database schema
result = await inspector.verify_model_schema("public", "topic_map")
if result["is_valid"]:
    print("Model schema is valid!")
else:
    print(f"Missing columns: {result['missing_columns']}")
    
# Generate SQL for a model
sql_result = await inspector.generate_schema_sql("topic_map")
print(sql_result["create_table_sql"])

# Always close the inspector when done
await inspector.close()
```

### Using the Storage System

```python
from services.models.storage.db_storage import DBObjectStorage

# Create a storage instance
db_storage = DBObjectStorage()

# Store content with validation
result = await db_storage.store_object(
    content_type="article",
    title="Example Article",
    content={"body": "Article content...", "tags": ["example", "test"]},
    metadata={"author": "John Doe"},
    model_name="ArticleModel",  # Will validate against this model
    validate=True
)

# Retrieve content
article = await db_storage.get_object(result)

# Always close connections when done
await db_storage.close()
```

### Using the Orchestrator

The orchestrator is the central point for accessing all models functionality:

```python
from services.models import orchestrator

# List all available models
models = await orchestrator.list_models()

# Get a specific model
model = await orchestrator.get_model("topic_map")

# Validate data against a model
result = await orchestrator.validate_data("topic_map", data)

# Get information about a model
model_info = await orchestrator.get_model_info("topic_map")

# Verify database schemas for all models
verification_results = await orchestrator.verify_db_schemas("public")
```

## Utilities

The Models Service includes several utilities to help with common tasks:

1. **verify_models.py**: A command-line utility for verifying model schemas against database schemas
2. **model_db_integration.py**: Examples of integrating model validation with database operations

See the [utilities documentation](utils/README.md) for more information.

## Development

When developing new models:

1. Define the model in the appropriate schema file
2. Register the model in the model registry
3. Verify the model against your database schema
4. Create appropriate database migrations if necessary

## Testing

For testing, the Models Service includes tools for verifying schema compatibility and generating test data. See the testing documentation for more information.

## Integration Points

The Models Service is integrated with:

1. **Database Service** - For storing and retrieving model definitions (using asyncpg)
2. **LLM Service** - For validating LLM responses against model schemas
3. **API Service** - For validating incoming API requests

## Migration

This service represents a refactoring effort to centralize model-related code previously duplicated in other services. See the following files for code that has been migrated:

- `services/llm/core/response_validator.py` 
- `services/database/validation/validation.py` 