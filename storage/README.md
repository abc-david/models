# Object Storage and Validation System

## Overview

This module provides a comprehensive system for storing, validating, and retrieving content objects in both relational and vector databases. The key design principle is the separation of concerns:

1. **Validation** - Handled by `ObjectValidator` in `validation.py`
2. **Relational Storage** - Handled by `DBObjectStorage` in `db_storage.py`
3. **Vector Storage** - Handled by `VectorObjectStorage` in `vector_storage.py`
4. **Cached Retrieval** - Handled by `CachedObjectStorage` in `cached_storage.py`

This separation allows for flexible workflows such as:
- Validation without storage
- Storage in relational database only
- Storage in vector database only
- Storage in both databases with the same ID
- Validation followed by specific storage strategies

## Architecture

### Core Components

#### 1. ObjectValidator (`validation.py`)

Validates content objects against models defined in the database schema. Features include:

- Validation against database-defined models
- Partial validation for updates
- Detailed validation results with errors and warnings
- Cached model schemas for performance
- Support for batch validation

```python
# Example usage
validator = ObjectValidator()
result = await validator.validate_object(data, "ArticleModel")
if result.is_valid:
    # Proceed with storage
else:
    # Handle validation errors
```

#### 2. DBObjectStorage (`db_storage.py`)

Manages storage and retrieval of content objects in the relational database using the async database interface. Features include:

- Integration with validation
- Metadata enrichment
- Cross-reference management
- Hierarchical relationships
- Transaction support
- Batch operations

```python
# Example usage
db_storage = DBObjectStorage()
try:
    object_id = await db_storage.store_object(
        content_type="article",
        title="Example Article",
        content=content_data,
        metadata=metadata,
        model_name="ArticleModel"  # Optional validation
    )
finally:
    await db_storage.close()  # Always close connections
```

#### 3. VectorObjectStorage (`vector_storage.py`)

Manages storage and retrieval of content objects in vector databases. Features include:

- Integration with validation
- Semantic search capabilities
- Content extraction for vectorization
- Collection management
- Optional integration with relational storage

```python
# Example usage
vector_storage = VectorObjectStorage()
try:
    object_id = await vector_storage.store_object(
        content=content_data,
        metadata=metadata,
        collection_name="articles",
        model_name="ArticleModel"  # Optional validation
    )

    # Search
    results = await vector_storage.search_objects(
        query="semantic search vector database",
        collection_name="articles"
    )
finally:
    await vector_storage.close()  # Always close connections
```

#### 4. CachedObjectStorage (`cached_storage.py`)

Provides cached retrieval of objects for improved performance:

- Builds on the Redis-based caching system from `services/cache`
- Caches frequently accessed objects
- Configurable TTL for different object types
- Cache invalidation on updates

```python
# Example usage
cached_storage = CachedObjectStorage()
try:
    # Use cached methods for read operations
    object_data = await cached_storage.get_object_cached(object_id)
    
    # Direct methods bypass cache and are used for writes
    await cached_storage.update_object(object_id, new_content)
    
    # Invalidate cache after writes if needed
    cached_storage.invalidate_object_cache(object_id)
finally:
    await cached_storage.close()  # Always close connections
```

## Benefits of This Approach

1. **Flexibility**: Use any component independently or in combination.
2. **Reusability**: Validation logic is centralized and reusable across storage systems.
3. **Clean Separation**: Each component has a single, clear responsibility.
4. **Better Testing**: Components can be tested in isolation.
5. **Support for Complex Workflows**: Enables advanced usage patterns.
6. **Fully Async**: All operations are async/await compatible for non-blocking I/O.

## Common Usage Patterns

### 1. Database-only Storage with Validation

```python
db_storage = DBObjectStorage()
try:
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
        if validation_result.is_valid:
            print(f"Stored with ID: {object_id}")
        else:
            print(f"Validation failed: {validation_result.errors}")
    else:
        print(f"Stored with ID: {result}")
finally:
    await db_storage.close()  # Always close connections
```

### 2. Vector-only Storage with Validation

```python
vector_storage = VectorObjectStorage()
try:
    result = await vector_storage.store_object(
        content=content_data,
        metadata=metadata,
        collection_name="articles",
        model_name="ArticleModel",
        validate=True
    )

    # Search
    results = await vector_storage.search_objects(
        query="semantic search vector database",
        collection_name="articles"
    )
finally:
    await vector_storage.close()  # Always close connections
```

### 3. Combined Storage (Both Database and Vector)

```python
# Create storage instances
db_storage = DBObjectStorage()
vector_storage = VectorObjectStorage()

try:
    # Validate once
    validator = ObjectValidator()
    validation_result = await validator.validate_object(
        data=validation_data,
        model_name="ArticleModel"
    )

    if validation_result.is_valid:
        # Store in database
        db_object_id = await db_storage.store_object(
            content_type="article",
            title=title,
            content=content,
            metadata=metadata,
            skip_validation=True  # Already validated
        )
        
        # Store in vector store with same ID
        vector_object_id = await vector_storage.store_object(
            content=content,
            metadata={**metadata, "db_id": db_object_id},
            collection_name="articles",
            object_id=db_object_id,  # Use same ID
            skip_validation=True  # Already validated
        )
finally:
    # Always close connections
    await db_storage.close()
    await vector_storage.close()
```

### 4. Using the ContentStorageOperator

The LLM service uses the `ContentStorageOperator` to simplify the combined storage workflow:

```python
from services.llm.modules.output_processing.content_storage_operator import ContentStorageOperator

operator = ContentStorageOperator()
try:
    # Stores in both relational and vector databases
    result = await operator.store_content(
        content_type="article",
        title="Generated Article",
        content=llm_output,
        metadata={"source": "llm_generation", "model": "gpt-4"},
        model_name="ArticleModel",
        validate=True,
        store_vectors=True
    )
    
    if result["success"]:
        print(f"Stored content with ID: {result['content_id']}")
        print(f"Vector ID: {result['vector_id']}")
    else:
        print(f"Storage failed: {result.get('error')}")
finally:
    # Close connections if the operator doesn't handle it
    if hasattr(operator.db_storage, 'close'):
        await operator.db_storage.close()
    if hasattr(operator.vector_storage, 'close'):
        await operator.vector_storage.close()
```

### 5. Batch Operations

```python
# Batch validate
validation_results = await validator.validate_objects(
    objects=batch_objects,
    model_name="ArticleModel"
)

# Batch store
db_storage = DBObjectStorage()
try:
    db_ids = await db_storage.batch_store_objects(
        objects=batch_objects,
        model_name="ArticleModel"
    )
finally:
    await db_storage.close()
```

## Integration with AsyncIO

All storage operations are async-compatible and should be used with `await`:

```python
async def process_content():
    db_storage = DBObjectStorage()
    try:
        # Use async/await pattern
        object_id = await db_storage.store_object(...)
        result = await db_storage.get_object(object_id)
        success = await db_storage.update_object(object_id, new_content)
    finally:
        # Always close connections
        await db_storage.close()

# Run with asyncio
import asyncio
asyncio.run(process_content())
```

## Best Practices

1. **Always Close Connections**: Use try/finally to ensure connections are closed
2. **Validate Early**: Validate objects as early as possible in your workflow
3. **Consistent IDs**: When storing in both databases, use the same ID for easy cross-referencing
4. **Transaction Management**: Use transactions when performing multiple related operations
5. **Error Handling**: Always check validation results before proceeding with storage
6. **Batch Operations**: Use batch operations for better performance when processing multiple objects
7. **Async Patterns**: Follow proper async/await patterns for all database operations

## Database Schema Dependencies

The validation system depends on the following table structure:

```sql
CREATE TABLE IF NOT EXISTS {schema_name}.object_models (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    definition JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

Where `definition` is a JSON Schema defining the object model.

## Note on LLM Output Validation

This validation system is particularly useful for validating LLM outputs against expected structures. The workflow is:

1. Define object models in the database
2. Generate content with LLMs
3. Validate the generated content against the models
4. Store valid content in the appropriate storage systems

This ensures that all LLM-generated content meets your application's data structure requirements. 