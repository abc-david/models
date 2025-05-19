# Migration Guide: ObjectStorage to Modular Architecture

This guide explains how to migrate from the original `ObjectStorage` class to the new modular architecture that separates validation and storage concerns.

## Overview of Changes

### Before: Monolithic ObjectStorage

The original `ObjectStorage` class combined:
- Database schema management
- Content storage and retrieval
- Metadata enrichment
- Cross-reference handling
- Data validation (implicitly through SQL constraints)

### After: Modular Components

The new architecture separates these concerns into three distinct components:
1. `ObjectValidator` - Handles validation against Pydantic models
2. `DBObjectStorage` - Handles relational database storage
3. `VectorObjectStorage` - Handles vector database storage

## Migration Steps

### Step 1: Update Imports

Replace:

```python
from services.models.storage.storage import ObjectStorage
```

With:

```python
from services.database.validation.validation import ObjectValidator
from services.models.storage.db_storage import DBObjectStorage
from services.llm.services.vectorstore import VectorObjectStorage  # If using vector storage
```

### Step 2: Initialize Components

Replace:
```python
storage = ObjectStorage(db_operator, schema_name)
```

With:
```python
# For database storage only
validator = ObjectValidator(db_operator)
db_storage = DBObjectStorage(db_operator, validator, schema_name)

# For vector storage
vector_store = VectorStoreManager()
vector_storage = VectorObjectStorage(vector_store, validator)

# For combined storage
vector_storage = VectorObjectStorage(vector_store, validator, db_storage)
```

### Step 3: Update Storage Operations

#### 3.1 Object Creation

Replace:
```python
object_id = storage.store_object(
    content_type="article",
    title="Example Article",
    content=content_data,
    metadata=metadata
)
```

With:
```python
# Without validation
object_id = await db_storage.store_object(
    content_type="article",
    title="Example Article",
    content=content_data,
    metadata=metadata
)

# With validation
result = await db_storage.store_object(
    content_type="article",
    title="Example Article",
    content=content_data,
    metadata=metadata,
    model_name="ArticleModel",
    validate=True
)

if isinstance(result, tuple):
    object_id, validation_result = result
    if not validation_result.is_valid:
        # Handle validation errors
        print(f"Validation errors: {validation_result.errors}")
else:
    object_id = result
```

#### 3.2 Batch Storage

Replace:
```python
object_ids = storage.batch_store_objects(objects)
```

With:
```python
# Without validation
object_ids = await db_storage.batch_store_objects(objects)

# With validation
result = await db_storage.batch_store_objects(
    objects=objects,
    model_name="ArticleModel",
    validate=True
)

if isinstance(result, tuple):
    object_ids, validation_results = result
    # Check validation_results for errors
else:
    object_ids = result
```

#### 3.3 Object Retrieval

Replace:
```python
object = storage.get_object(object_id)
```

With:
```python
# From database
object = db_storage.get_object(object_id)

# From vector store
object = await vector_storage.get_object(object_id, collection_name="articles")
```

#### 3.4 Object Updates

Replace:
```python
success = storage.update_object(
    object_id,
    content=updated_content,
    metadata=updated_metadata
)
```

With:
```python
# Without validation
success = await db_storage.update_object(
    object_id,
    content=updated_content,
    metadata=updated_metadata
)

# With validation
result = await db_storage.update_object(
    object_id,
    content=updated_content,
    metadata=updated_metadata,
    model_name="ArticleModel",
    validate=True
)

if isinstance(result, tuple):
    success, validation_result = result
    if not validation_result.is_valid:
        # Handle validation errors
else:
    success = result
```

#### 3.5 Object Deletion

Replace:
```python
success = storage.delete_object(object_id)
```

With:
```python
# From database
success = db_storage.delete_object(object_id)

# From vector store
success = await vector_storage.delete_object(object_id, collection_name="articles")

# From both
db_success = db_storage.delete_object(object_id)
vector_success = await vector_storage.delete_object(object_id, collection_name="articles")
```

### Step 4: Add Vector Storage Support (New Capability)

For content that needs to be searchable by meaning:

```python
# Store in both database and vector store
db_object_id = await db_storage.store_object(
    content_type="article",
    title="Example Article",
    content=content_data,
    metadata=metadata
)

vector_object_id = await vector_storage.store_object(
    content=content_data,
    metadata={
        **metadata,
        "title": "Example Article",
        "db_id": db_object_id
    },
    collection_name="articles",
    object_id=db_object_id  # Use same ID for consistency
)

# Search by meaning
results = await vector_storage.search_objects(
    query="semantic search about vector databases",
    collection_name="articles",
    limit=5
)
```

### Step 5: Explicit Validation (New Capability)

For cases where you want to validate without storing:

```python
validator = ObjectValidator(db_operator)

validation_result = await validator.validate_object(
    data={
        "content_type": "article",
        "title": "Example Article",
        "content": content_data,
        "metadata": metadata
    },
    model_name="ArticleModel"
)

if validation_result.is_valid:
    # Process validated data
    validated_data = validation_result.validated_data
    # ...
else:
    # Handle validation errors
    for error in validation_result.errors:
        print(f"{error['path']}: {error['message']}")
```

## Handling Async Methods

Note that many methods in the new architecture are asynchronous. If you're working in a synchronous context, you'll need to use `asyncio.run()` or a similar approach:

```python
import asyncio

# In synchronous code
object_id = asyncio.run(
    db_storage.store_object(
        content_type="article",
        title="Example Article",
        content=content_data,
        metadata=metadata
    )
)
```

## Best Practices for Migration

1. **Start with validation**: First migrate to using `ObjectValidator` for explicit validation.
2. **Then update storage**: Replace `ObjectStorage` with `DBObjectStorage`.
3. **Finally add vector storage**: Add `VectorObjectStorage` for semantic search capabilities.
4. **Update error handling**: The new components provide more detailed error information.
5. **Test thoroughly**: Make sure all your workflows continue to work as expected.

## Backward Compatibility Wrapper

If you need to maintain backward compatibility during migration, you can create a wrapper class:

```python
class CompatibilityStorage:
    def __init__(self, db_operator, schema_name="public"):
        self.validator = ObjectValidator(db_operator)
        self.db_storage = DBObjectStorage(db_operator, self.validator, schema_name)
        
    def store_object(self, content_type, title, content, metadata=None, parent_id=None):
        return asyncio.run(
            self.db_storage.store_object(
                content_type=content_type,
                title=title,
                content=content,
                metadata=metadata,
                parent_id=parent_id
            )
        )
        
    # Implement other methods similarly...
```

This wrapper can help you migrate gradually without disrupting existing code.

## Questions?

If you have any questions about migrating to the new architecture, please contact the development team. 