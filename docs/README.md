# Models Service Documentation

This directory contains comprehensive documentation for the Models Service in the Content Generation Framework.

## Documentation Overview

| File | Description |
|------|-------------|
| [01_Object_Model_Design_Principles.md](01_Object_Model_Design_Principles.md) | Core design principles for object models in the framework |
| [02_Alpha_Objects_Listing.md](02_Alpha_Objects_Listing.md) | Top-level container objects (Websites, Books, etc.) |
| [03_Beta_Objects_Listing.md](03_Beta_Objects_Listing.md) | Mid-level content objects (Blog Posts, Landing Pages, etc.) |
| [04_Gamma_Objects_Listing.md](04_Gamma_Objects_Listing.md) | Low-level component objects (CTAs, Tables, etc.) |
| [05_Qualifier_Objects_Listing.md](05_Qualifier_Objects_Listing.md) | Metadata objects (Tags, Categories, etc.) |
| [06_Organizer_Objects_Listing.md](06_Organizer_Objects_Listing.md) | Structural objects (Collections, Series, etc.) |
| [07_Model_Implementation_Guide.md](07_Model_Implementation_Guide.md) | Practical guide for implementing new models |
| [08_Database_Schema_Integration.md](08_Database_Schema_Integration.md) | Database schema creation and migration management |

## Models Service Overview

The Models Service is a core component of the Content Generation Framework that:

1. **Provides Schema Definitions**: Defines the structure, validation rules, and relationships for all content objects
2. **Ensures Data Integrity**: Validates content against defined schemas
3. **Manages Database Integration**: Handles the mapping between models and database tables
4. **Facilitates Content Operations**: Provides APIs for creating, reading, updating, and deleting content objects

## Key Components

The Models Service consists of several key components:

- **Model Definitions**: JSON Schema-based definitions for all content object types
- **Model Registry**: Central registry for all model definitions
- **Validation System**: Framework for validating data against model schemas
- **Database Schema Inspector**: Tools for mapping models to database schemas
- **Orchestrator**: Central API for accessing and working with models

## Getting Started

If you're new to the Models Service, we recommend starting with the following documents:

1. [Object Model Design Principles](01_Object_Model_Design_Principles.md) to understand the overall design
2. [Model Implementation Guide](07_Model_Implementation_Guide.md) for practical implementation guidance
3. [Alpha/Beta/Gamma Objects Listings](02_Alpha_Objects_Listing.md) to understand the object taxonomy

## Working with Models

### Basic Usage Example

```python
from services.models import orchestrator

# Get a model definition
website_model = await orchestrator.get_model("Website")

# Validate data against a model
data = {
    "name": "My Corporate Website",
    "description": "Official website for my company",
    "content_hierarchy": { /* ... */ },
    "settings": { /* ... */ },
    "status": "active"
}
validation_result = await orchestrator.validate_data(data, "Website")

if validation_result.is_valid:
    # Store the data
    new_website = await orchestrator.create_model_instance("Website", data)
    print(f"Created website with ID: {new_website['id']}")
else:
    print(f"Validation errors: {validation_result.errors}")
```

## Extending the Models Service

To add new models to the system:

1. Define the model schema in a Python file in the `services/models/schemas` directory
2. Register the model in the `model_registry.py` file or using the dynamic registration method
3. Create database tables and indexes for the model
4. Implement any custom validation if needed
5. Add helper methods for common operations

See the [Model Implementation Guide](07_Model_Implementation_Guide.md) for detailed instructions.

## Ensuring Database Consistency

The Models Service provides tools to ensure that the database schema always matches the model definitions:

1. Use `DBSchemaInspector.verify_all_models_schema()` to check for discrepancies
2. Generate migrations to fix any issues using the migration utilities
3. Apply migrations to update the database schema

See [Database Schema Integration](08_Database_Schema_Integration.md) for more details. 