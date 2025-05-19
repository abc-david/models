"""
File: services/database/storage/integration_example.py
MODULE: Integration Example
PURPOSE: Demonstrates how to use the unified validation and storage modules
DEPENDENCIES:
    - ObjectValidator for validation
    - DBObjectStorage for relational storage
    - VectorObjectStorage for vector storage

This example demonstrates various usage patterns for the validation and storage systems,
including:
1. Database-only storage with validation
2. Vector-only storage with validation
3. Combined storage (both database and vector)
4. Validation-only without storage
5. Batch operations with validation

These examples show the flexibility offered by separating validation from storage.
"""

import asyncio
import json

from services.database.db_operator import DBOperator
from services.database.validation.validation import ObjectValidator
from services.models.storage.db_storage import DBObjectStorage
from services.llm.services.vectorstore import VectorObjectStorage
from services.llm.services.vectorstore import VectorStoreManager


# Example data
EXAMPLE_ARTICLE = {
    "title": "Understanding Vector Databases",
    "content": {
        "text": "Vector databases are specialized databases that store data as high-dimensional vectors. "
                "These vectors represent the semantic meaning of data, making it possible to search for "
                "content based on meaning rather than keywords or exact matches. This approach is "
                "fundamental to modern AI applications.",
        "summary": "An introduction to vector databases and their applications.",
        "tags": ["vector-db", "ai", "embeddings"]
    },
    "metadata": {
        "author": "AI Researcher",
        "publish_date": "2023-07-15",
        "category": "AI Technology",
        "status": "published"
    }
}


async def example_db_storage_with_validation():
    """Example of storing content in the database with validation."""
    print("\n=== Database Storage with Validation ===")
    
    # Initialize components
    db_operator = DBOperator()
    validator = ObjectValidator(db_operator)
    db_storage = DBObjectStorage(db_operator, validator)
    
    # Store with validation
    article_type = "article"
    model_name = "ArticleModel"
    
    result = await db_storage.store_object(
        content_type=article_type,
        title=EXAMPLE_ARTICLE["title"],
        content=EXAMPLE_ARTICLE["content"],
        metadata=EXAMPLE_ARTICLE["metadata"],
        model_name=model_name,
        validate=True
    )
    
    # Check result
    if isinstance(result, tuple):
        object_id, validation_result = result
        if validation_result.is_valid:
            print(f"✅ Validation successful. Object stored with ID: {object_id}")
        else:
            print(f"❌ Validation failed: {validation_result.errors}")
    else:
        print(f"✅ Object stored with ID: {result}")
    
    # Retrieve the stored object
    if isinstance(result, tuple):
        object_id = result[0]
    else:
        object_id = result
        
    if object_id:
        stored_object = db_storage.get_object(object_id)
        print(f"Retrieved object title: {stored_object['title']}")
        print(f"Retrieved object metadata: {json.dumps(stored_object['metadata'], indent=2)}")
    
    return object_id


async def example_vector_storage_with_validation():
    """Example of storing content in the vector database with validation."""
    print("\n=== Vector Storage with Validation ===")
    
    # Initialize components
    db_operator = DBOperator()
    validator = ObjectValidator(db_operator)
    vector_store = VectorStoreManager()
    vector_storage = VectorObjectStorage(vector_store, validator)
    
    # Store with validation
    model_name = "ArticleModel"
    
    result = await vector_storage.store_object(
        content=EXAMPLE_ARTICLE["content"],
        metadata=EXAMPLE_ARTICLE["metadata"],
        collection_name="articles",
        model_name=model_name,
        validate=True
    )
    
    # Check result
    if isinstance(result, tuple):
        object_id, validation_result = result
        if validation_result.is_valid:
            print(f"✅ Validation successful. Object stored with ID: {object_id}")
        else:
            print(f"❌ Validation failed: {validation_result.errors}")
    else:
        print(f"✅ Object stored with ID: {result}")
    
    # Retrieve the stored object
    if isinstance(result, tuple):
        object_id = result[0]
    else:
        object_id = result
        
    if object_id:
        stored_object = await vector_storage.get_object(object_id, "articles")
        if stored_object:
            print(f"Retrieved object text: {stored_object['text'][:50]}...")
            print(f"Retrieved object metadata: {json.dumps(stored_object['metadata'], indent=2)}")
    
    # Search for the object
    search_results = await vector_storage.search_objects(
        query="semantic search vector database",
        collection_name="articles",
        limit=1
    )
    
    if search_results:
        print(f"Search found {len(search_results)} results")
        print(f"Top result similarity: {search_results[0].get('score', 0)}")
    
    return object_id


async def example_combined_storage():
    """Example of storing content in both database and vector store."""
    print("\n=== Combined Database and Vector Storage ===")
    
    # Initialize components
    db_operator = DBOperator()
    validator = ObjectValidator(db_operator)
    db_storage = DBObjectStorage(db_operator, validator)
    vector_store = VectorStoreManager()
    vector_storage = VectorObjectStorage(vector_store, validator, db_storage)
    
    # Step 1: Validate
    validation_data = {
        "content_type": "article",
        "title": EXAMPLE_ARTICLE["title"],
        "content": EXAMPLE_ARTICLE["content"],
        "metadata": EXAMPLE_ARTICLE["metadata"]
    }
    
    validation_result = await validator.validate_object(
        data=validation_data,
        model_name="ArticleModel"
    )
    
    if not validation_result.is_valid:
        print(f"❌ Validation failed: {validation_result.errors}")
        return None
    
    print("✅ Validation successful.")
    
    # Step 2: Store in database
    validated_data = validation_result.validated_data or validation_data
    
    db_object_id = await db_storage.store_object(
        content_type=validated_data["content_type"],
        title=validated_data["title"],
        content=validated_data["content"],
        metadata=validated_data["metadata"],
        skip_validation=True  # Already validated
    )
    
    print(f"✅ Stored in database with ID: {db_object_id}")
    
    # Step 3: Store in vector database with the same ID
    vector_object_id = await vector_storage.store_object(
        content=validated_data["content"],
        metadata={
            **validated_data["metadata"],
            "db_object_id": db_object_id,
            "title": validated_data["title"]
        },
        collection_name="articles",
        object_id=db_object_id,  # Use same ID for both stores
        skip_validation=True  # Already validated
    )
    
    print(f"✅ Stored in vector database with ID: {vector_object_id}")
    
    # Verify we can retrieve from both
    db_object = db_storage.get_object(db_object_id)
    vector_object = await vector_storage.get_object(vector_object_id, "articles")
    
    print(f"Database object title: {db_object['title']}")
    print(f"Vector object metadata title: {vector_object['metadata'].get('title')}")
    
    return db_object_id


async def example_validation_only():
    """Example of validation without storage."""
    print("\n=== Validation Only (No Storage) ===")
    
    # Initialize validator
    db_operator = DBOperator()
    validator = ObjectValidator(db_operator)
    
    # Prepare an intentionally invalid article
    invalid_article = {
        "content_type": "article",
        "title": "Missing Required Fields",
        "content": {
            # Missing 'text' field which is required
            "summary": "This article is missing required fields."
        },
        "metadata": {
            # Missing required author field
            "publish_date": "2023-07-15"
        }
    }
    
    # Validate without storing
    validation_result = await validator.validate_object(
        data=invalid_article,
        model_name="ArticleModel"
    )
    
    if validation_result.is_valid:
        print("✅ Validation successful (unexpected)")
    else:
        print(f"❌ Validation failed as expected. Errors:")
        for error in validation_result.errors:
            print(f"  - {error['path']}: {error['message']}")
    
    # Fix the errors
    fixed_article = {
        "content_type": "article",
        "title": "Fixed Article",
        "content": {
            "text": "This article now has all required fields.",
            "summary": "This article is no longer missing required fields."
        },
        "metadata": {
            "author": "Validation Tester",
            "publish_date": "2023-07-15"
        }
    }
    
    # Validate the fixed article
    fixed_validation_result = await validator.validate_object(
        data=fixed_article,
        model_name="ArticleModel"
    )
    
    if fixed_validation_result.is_valid:
        print("✅ Validation successful after fixing errors.")
    else:
        print(f"❌ Validation still failed: {fixed_validation_result.errors}")
    
    return fixed_validation_result.is_valid


async def example_batch_operations():
    """Example of batch operations with validation."""
    print("\n=== Batch Operations with Validation ===")
    
    # Initialize components
    db_operator = DBOperator()
    validator = ObjectValidator(db_operator)
    db_storage = DBObjectStorage(db_operator, validator)
    vector_store = VectorStoreManager()
    vector_storage = VectorObjectStorage(vector_store, validator)
    
    # Prepare batch of articles
    batch_articles = [
        {
            "content_type": "article",
            "title": "Article 1",
            "content": {
                "text": "This is the first article in the batch.",
                "summary": "First article summary."
            },
            "metadata": {
                "author": "Batch Author 1",
                "publish_date": "2023-07-15"
            }
        },
        {
            "content_type": "article",
            "title": "Article 2",
            "content": {
                "text": "This is the second article in the batch.",
                "summary": "Second article summary."
            },
            "metadata": {
                "author": "Batch Author 2",
                "publish_date": "2023-07-16"
            }
        }
    ]
    
    # Batch store in database
    db_result = await db_storage.batch_store_objects(
        objects=batch_articles,
        model_name="ArticleModel",
        validate=True
    )
    
    if isinstance(db_result, tuple):
        db_ids, validation_results = db_result
        print(f"✅ Database batch store successful. IDs: {db_ids}")
    else:
        db_ids = db_result
        print(f"✅ Database batch store successful. IDs: {db_ids}")
    
    # Prepare for vector storage
    vector_batch = []
    for i, article in enumerate(batch_articles):
        vector_batch.append({
            "content": article["content"],
            "metadata": {
                **article["metadata"],
                "title": article["title"],
                "db_id": db_ids[i] if db_ids else None
            }
        })
    
    # Batch store in vector database
    vector_result = await vector_storage.batch_store_objects(
        objects=vector_batch,
        collection_name="articles",
        model_name="ArticleModel",
        validate=True
    )
    
    if isinstance(vector_result, tuple):
        vector_ids, validation_results = vector_result
        print(f"✅ Vector batch store successful. IDs: {vector_ids}")
    else:
        vector_ids = vector_result
        print(f"✅ Vector batch store successful. IDs: {vector_ids}")
    
    return db_ids, vector_ids


async def run_examples():
    """Run all examples in sequence."""
    try:
        # Initialize collections
        vector_store = VectorStoreManager()
        collections = await vector_store.list_collections()
        if "articles" not in collections:
            await vector_store.create_collection("articles")
        
        # Run examples
        await example_db_storage_with_validation()
        await example_vector_storage_with_validation()
        await example_combined_storage()
        await example_validation_only()
        await example_batch_operations()
        
        print("\n✅ All examples completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during examples: {str(e)}")


if __name__ == "__main__":
    # Run the examples
    asyncio.run(run_examples()) 