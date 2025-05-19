# Models Service Utilities

This directory contains utilities for working with the models service, including tools for schema verification, database integration, and model visualization.

## Available Utilities

### 1. Model Schema Verification (`verify_models.py`)

A command-line utility for verifying model schemas against database schemas, identifying missing tables and columns, and generating SQL statements.

```bash
# List all available models
python -m services.models.utils.verify_models list

# Verify a specific model against a database schema
python -m services.models.utils.verify_models verify --model topic_map --schema public

# Verify all models against a database schema
python -m services.models.utils.verify_models verify --schema content_project

# Generate SQL for a model
python -m services.models.utils.verify_models sql --model topic_map

# Find missing tables in a schema
python -m services.models.utils.verify_models missing --schema content_project
```

### 2. Model-Database Integration (`model_db_integration.py`)

A utility demonstrating integration between model validation and database operations, showing how to effectively use both services together.

```bash
# Validate data against a model and insert it into the database
python -m services.models.utils.model_db_integration insert --model topic_map --data '{"name": "Test Topic Map", "description": "A test topic map"}' --schema public

# Fetch data from the database and validate it against a model
python -m services.models.utils.model_db_integration fetch --model topic_map --id 1 --schema public

# Verify a model's schema against the database and optionally repair it
python -m services.models.utils.model_db_integration verify --model topic_map --schema public --repair
```

## Best Practices

These utilities demonstrate best practices for working with the models service:

1. **Validation Before Database Operations**: Always validate data against models before inserting or updating it in the database.

2. **Schema Verification**: Regularly verify model schemas against database schemas to ensure they are in sync.

3. **Integration**: Use the models and database services together effectively, leveraging the strengths of each.

4. **Error Handling**: Handle errors gracefully and provide meaningful error messages.

5. **Clean Up**: Always close database connections and other resources when done with them.

## Extending the Utilities

These utilities are designed to be extended and adapted for specific needs. To extend them:

1. Add new commands or options to the existing utilities.
2. Create new utilities for specific needs, following the patterns established in the existing utilities.
3. Add examples and documentation to help others understand how to use the utilities. 