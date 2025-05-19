# Database Schema Integration

This document outlines the integration between the Models Service and database schemas, explaining how model definitions are mapped to database tables and how to manage schema migrations.

## Overview

The Content Generation Framework uses a dynamic approach to database schema management, where model definitions drive the database schema. This ensures that the database structure always reflects the latest model definitions.

## Model-to-Schema Mapping

### Basic Mapping Rules

Each model type maps to database tables according to these rules:

1. **Alpha-Level Objects**: Each alpha object type gets its own table (e.g., `websites`, `books`)
2. **Beta-Level Objects**: Each beta object type gets its own table (e.g., `blog_posts`, `landing_pages`)
3. **Gamma-Level Objects**: Small components may be embedded in JSONB fields; larger ones get their own tables
4. **Qualifier Objects**: Each qualifier type gets its own table (e.g., `tags`, `categories`)
5. **Organizer Objects**: Each organizer type gets its own table plus relationship tables

### Type Conversion

JSON Schema types are mapped to PostgreSQL data types according to the following rules:

| JSON Schema Type | PostgreSQL Type |
|------------------|----------------|
| string           | TEXT           |
| string (format: date-time) | TIMESTAMP WITH TIME ZONE |
| string (format: uuid) | UUID |
| number           | NUMERIC |
| integer          | INTEGER |
| boolean          | BOOLEAN |
| object           | JSONB |
| array            | JSONB |

## Schema Generation

The `DBSchemaInspector` class provides methods to generate SQL schemas from model definitions.

### Generate a Table Creation SQL

```python
from services.models.db_schema_inspector import DBSchemaInspector

# Create an inspector instance
inspector = DBSchemaInspector()

# Generate SQL for a specific model
blog_post_sql = inspector.generate_create_table_sql("BlogPost")
print(blog_post_sql)

# Output example:
"""
CREATE TABLE IF NOT EXISTS blog_posts (
    id UUID PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    excerpt TEXT,
    featured_image TEXT,
    belongs_to JSONB NOT NULL,
    metadata JSONB,
    status TEXT NOT NULL,
    slug TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
"""
```

### Generate Index Creation SQL

```python
# Generate index SQL for a specific model
blog_post_indexes = inspector.generate_index_sql("BlogPost")
print(blog_post_indexes)

# Output example:
"""
CREATE INDEX IF NOT EXISTS blog_posts_title_idx ON blog_posts (title);
CREATE INDEX IF NOT EXISTS blog_posts_status_idx ON blog_posts (status);
CREATE INDEX IF NOT EXISTS blog_posts_belongs_to_idx ON blog_posts USING GIN (belongs_to);
"""
```

## Schema Verification

The `DBSchemaInspector` also provides methods to verify that the database schema matches the model definition.

### Verify a Single Model's Schema

```python
# Verify that the blog_posts table matches the BlogPost model
verification_result = await inspector.verify_model_schema("BlogPost")

if verification_result.is_valid:
    print("Schema is valid")
else:
    print("Schema discrepancies:", verification_result.discrepancies)
    
    # Generate SQL to fix discrepancies
    fix_sql = inspector.generate_fix_schema_sql(verification_result)
    print("SQL to fix schema:", fix_sql)
```

### Verify All Models' Schemas

```python
# Verify all model schemas
all_verification = await inspector.verify_all_models_schema()

for model_name, result in all_verification.items():
    if not result.is_valid:
        print(f"Schema issues for {model_name}:", result.discrepancies)
```

## Schema Migration

When model definitions change, the database schema needs to be updated. The framework provides tools to manage these migrations.

### Migration Process

1. **Create a migration file** with the changes to be applied
2. **Apply the migration** to update the database schema
3. **Verify the schema** to ensure it matches the model definitions

### Creating a Migration File

```python
# In services/models/storage/migrations/create_migration.py

from services.models.db_schema_inspector import DBSchemaInspector
from datetime import datetime

async def create_migration(description, models=None):
    """Create a new migration file for the specified models."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{timestamp}_{description.replace(' ', '_').lower()}.sql"
    
    inspector = DBSchemaInspector()
    
    # If no models specified, verify all models
    if models is None:
        verification = await inspector.verify_all_models_schema()
        models_to_fix = [model for model, result in verification.items() if not result.is_valid]
    else:
        models_to_fix = models
    
    # Generate SQL for each model that needs fixing
    sql_statements = []
    for model in models_to_fix:
        verification = await inspector.verify_model_schema(model)
        if not verification.is_valid:
            fix_sql = inspector.generate_fix_schema_sql(verification)
            sql_statements.append(f"-- Fix schema for {model}\n{fix_sql}")
    
    # Create the migration file
    with open(f"services/models/storage/migrations/{filename}", "w") as f:
        f.write("-- Migration: " + description + "\n\n")
        f.write("BEGIN;\n\n")
        f.write("\n\n".join(sql_statements))
        f.write("\n\nCOMMIT;")
    
    return filename
```

### Applying Migrations

```python
# In services/models/storage/migrations/apply_migrations.py

from services.database.connector import DBConnector
import os

async def apply_migrations(up_to=None):
    """Apply all pending migrations up to the specified one."""
    db = DBConnector()
    
    # Create migrations table if it doesn't exist
    await db.execute("""
    CREATE TABLE IF NOT EXISTS _migrations (
        id SERIAL PRIMARY KEY,
        filename TEXT NOT NULL,
        applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    )
    """)
    
    # Get list of applied migrations
    applied = await db.fetch("SELECT filename FROM _migrations ORDER BY id")
    applied_migrations = [row["filename"] for row in applied]
    
    # Get list of migration files
    migration_files = sorted(os.listdir("services/models/storage/migrations"))
    migration_files = [f for f in migration_files if f.endswith(".sql")]
    
    # Stop at specified migration if provided
    if up_to:
        try:
            index = migration_files.index(up_to)
            migration_files = migration_files[:index + 1]
        except ValueError:
            raise ValueError(f"Migration {up_to} not found")
    
    # Apply pending migrations
    for migration in migration_files:
        if migration in applied_migrations:
            continue
        
        print(f"Applying migration: {migration}")
        
        # Read and execute the migration
        with open(f"services/models/storage/migrations/{migration}", "r") as f:
            sql = f.read()
            await db.execute(sql)
        
        # Record that the migration was applied
        await db.execute(
            "INSERT INTO _migrations (filename) VALUES ($1)",
            migration
        )
    
    print("Migrations complete.")
```

## Example: Creating and Applying a Schema Change

Let's walk through a complete example of changing a model definition and updating the database schema:

### 1. Update Model Definition

```python
# Update the BlogPost model to add a new field
from services.models.base_model import ModelDefinition

BLOG_POST_MODEL = ModelDefinition(
    name="BlogPost",
    schema={
        # ... existing fields ...
        "properties": {
            # ... existing properties ...
            "reading_time": {"type": "integer", "minimum": 1},  # New field
            # ... other properties ...
        }
    },
    # ... other attributes ...
)

# Update the model in the registry
await orchestrator.register_model(BLOG_POST_MODEL)
```

### 2. Create a Migration

```python
# Create a migration for the updated BlogPost model
from services.models.storage.migrations.create_migration import create_migration

migration_file = await create_migration("add_reading_time_to_blog_posts", ["BlogPost"])
print(f"Created migration: {migration_file}")
```

### 3. Apply the Migration

```python
# Apply the migration
from services.models.storage.migrations.apply_migrations import apply_migrations

await apply_migrations()
print("Schema updated")
```

### 4. Verify the Schema

```python
# Verify that the schema now matches the model
from services.models.db_schema_inspector import DBSchemaInspector

inspector = DBSchemaInspector()
verification = await inspector.verify_model_schema("BlogPost")

if verification.is_valid:
    print("Schema successfully updated")
else:
    print("Schema still has issues:", verification.discrepancies)
```

## Best Practices for Schema Management

1. **Version Control Migrations**: Commit all migration files to version control.
2. **Test Migrations**: Test migrations in a staging environment before applying to production.
3. **Backup Before Migrating**: Always back up the database before applying migrations.
4. **Use Transactions**: Wrap migrations in transactions to ensure atomic operations.
5. **Document Schema Changes**: Document significant schema changes in a changelog.
6. **Maintain Backwards Compatibility**: When possible, make schema changes that are backward compatible.
7. **Coordinate with Code Changes**: Deploy schema changes along with corresponding code changes.
8. **Verify After Migration**: Always verify the schema after applying migrations.

## Advanced Schema Features

### Indexes and Constraints

The `DBSchemaInspector` can also generate SQL for indexes and constraints:

```python
# Generate SQL for indexes and constraints
from services.models.db_schema_inspector import DBSchemaInspector

inspector = DBSchemaInspector()

# Generate index SQL for a specific model
indexes_sql = inspector.generate_index_sql("BlogPost")

# Generate constraint SQL for a model
constraints_sql = inspector.generate_constraint_sql("BlogPost")
```

### Schema Visualization

The Models Service includes tools to visualize the database schema:

```python
# Generate a schema visualization
from services.models.visualization import schema_visualizer

# Generate a visualization of the entire schema
html = schema_visualizer.generate_schema_diagram()

# Save to a file
with open("schema_diagram.html", "w") as f:
    f.write(html)
```

### Partitioning Large Tables

For very large tables, the framework supports PostgreSQL table partitioning:

```python
# Generate SQL for a partitioned table
from services.models.db_schema_inspector import DBSchemaInspector

inspector = DBSchemaInspector()

# Generate partitioning SQL
partitioning_sql = inspector.generate_partitioning_sql(
    "ContentMetrics", 
    partition_by="RANGE",
    partition_key="created_at",
    partitions=[
        {"name": "content_metrics_2022", "from": "2022-01-01", "to": "2023-01-01"},
        {"name": "content_metrics_2023", "from": "2023-01-01", "to": "2024-01-01"}
    ]
)
```

## For More Information

- [PostgreSQL Data Types](https://www.postgresql.org/docs/current/datatype.html)
- [Model Implementation Guide](07_Model_Implementation_Guide.md)
- [Testing Database Schemas](../../../.cursor/rules/testing-practices.mdc) 