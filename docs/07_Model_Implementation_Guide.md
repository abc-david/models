# Model Implementation Guide

This document provides a comprehensive guide for implementing new models in the Content Generation Framework. It includes best practices, examples, and workflows for creating, registering, and using models.

## Model Definition Process

Creating a new model in the system involves the following steps:

1. **Define the model schema**
2. **Register the model with the Models Service**
3. **Create database tables or collections**
4. **Implement validation**
5. **Create helper methods for model operations**

## 1. Define the Model Schema

Models are defined using a JSON schema format that describes the structure and validation rules. The schema should be placed in the `services/models/schemas` directory.

### Example Model Schema: BlogPost

```python
# File: services/models/schemas/blog_post.py

from services.models.base_model import ModelDefinition

BLOG_POST_MODEL = ModelDefinition(
    name="BlogPost",
    schema={
        "type": "object",
        "required": ["title", "content", "status"],
        "properties": {
            "id": {"type": "string", "format": "uuid"},
            "title": {"type": "string", "minLength": 5, "maxLength": 200},
            "content": {"type": "string", "minLength": 100},
            "excerpt": {"type": "string", "maxLength": 500},
            "featured_image": {"type": "string", "format": "uri"},
            "belongs_to": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "type": {"type": "string", "enum": ["Website", "Blog"]}
                },
                "required": ["id", "type"]
            },
            "metadata": {"type": "object"},
            "status": {
                "type": "string",
                "enum": ["draft", "published", "archived"]
            },
            "slug": {"type": "string", "pattern": "^[a-z0-9-]+$"},
            "created_at": {"type": "string", "format": "date-time"},
            "updated_at": {"type": "string", "format": "date-time"}
        }
    },
    description="A blog post for websites and other content platforms",
    model_type="beta",
    db_table="blog_posts",
    example={
        "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "title": "How to Implement Models in the Content Framework",
        "content": "# Introduction\n\nIn this post, we'll explore...",
        "excerpt": "Learn how to implement models in our content framework",
        "featured_image": "https://example.com/images/model-implementation.jpg",
        "belongs_to": {
            "id": "e47ac10b-58cc-4372-a567-0e02b2c3d123",
            "type": "Website"
        },
        "metadata": {
            "reading_time": 5,
            "tags": ["technical", "tutorial"]
        },
        "status": "published",
        "slug": "how-to-implement-models",
        "created_at": "2023-01-15T14:30:00Z",
        "updated_at": "2023-01-15T15:45:00Z"
    }
)
```

## 2. Register the Model with the Models Service

Models must be registered with the Models Service to be available throughout the system. This is done through the `model_registry.py` file.

### Adding a Model to the Registry

```python
# In services/models/model_registry.py

from services.models.schemas.blog_post import BLOG_POST_MODEL
# ... other imports

class ModelRegistry:
    # ... existing code ...
    
    async def initialize_models(self):
        """Initialize all models in the registry."""
        self._models = {
            # ... existing models ...
            "BlogPost": BLOG_POST_MODEL,
            # ... other models ...
        }
```

Alternatively, you can use the dynamic registration method:

```python
# Either at application startup or in an initialization script
await orchestrator.register_model(BLOG_POST_MODEL)
```

## 3. Create Database Tables or Collections

Each model typically corresponds to a database table. You can generate the SQL for table creation using the `DBSchemaInspector`.

### Creating Tables for Models

```python
# In a migration script or initialization code
from services.models.db_schema_inspector import DBSchemaInspector

async def create_blog_post_table():
    inspector = DBSchemaInspector()
    sql = inspector.generate_create_table_sql("BlogPost")
    
    # Execute the SQL using the database connector
    from services.database.connector import DBConnector
    db = DBConnector()
    await db.execute(sql)
```

## 4. Implement Validation

The Models Service provides built-in validation through the `ModelValidator` class. Additional custom validation can be implemented for specific models.

### Custom Validation Example

```python
# In services/models/validation/custom_validators.py

from services.models.validation.validator import ModelValidator

class BlogPostValidator(ModelValidator):
    async def validate(self, data):
        # Call the base validation first
        result = await super().validate(data)
        
        # Add custom validation
        if result.is_valid:
            # Check that excerpts are derived from content
            if "excerpt" in data and "content" in data:
                if data["excerpt"] not in data["content"]:
                    result.add_error("excerpt", "Excerpt must be derived from content")
        
        return result

# Register the custom validator in the orchestrator
await orchestrator.register_validator("BlogPost", BlogPostValidator)
```

## 5. Create Helper Methods for Model Operations

The `orchestrator.py` module provides core functionality for model operations. You can extend it with helper methods for specific models.

### Example Helper Functions

```python
# In services/models/helpers/blog_post_helpers.py

from services.models import orchestrator
from services.database.connector import DBConnector

async def get_blog_posts_by_website(website_id, limit=10, offset=0):
    db = DBConnector()
    query = """
    SELECT * FROM blog_posts 
    WHERE belongs_to->>'id' = $1 
    ORDER BY created_at DESC 
    LIMIT $2 OFFSET $3
    """
    results = await db.fetch(query, website_id, limit, offset)
    
    # Validate results against the model
    validated_posts = []
    for post in results:
        validation = await orchestrator.validate_data(dict(post), "BlogPost")
        if validation.is_valid:
            validated_posts.append(post)
    
    return validated_posts

async def create_blog_post(data):
    # Validate data against the model
    validation = await orchestrator.validate_data(data, "BlogPost")
    if not validation.is_valid:
        return {"success": False, "errors": validation.errors}
    
    # Insert the data
    db = DBConnector()
    query = """
    INSERT INTO blog_posts (
        id, title, content, excerpt, featured_image, 
        belongs_to, metadata, status, slug, created_at, updated_at
    ) VALUES (
        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
    ) RETURNING *
    """
    
    result = await db.fetchone(
        query,
        data.get("id"),
        data.get("title"),
        data.get("content"),
        data.get("excerpt"),
        data.get("featured_image"),
        data.get("belongs_to"),
        data.get("metadata"),
        data.get("status"),
        data.get("slug"),
        data.get("created_at"),
        data.get("updated_at")
    )
    
    return {"success": True, "data": dict(result)}
```

## Using Models in Application Code

Once models are implemented, they can be used throughout the application:

```python
from services.models import orchestrator
from services.models.helpers.blog_post_helpers import get_blog_posts_by_website, create_blog_post

# Get a model definition
blog_post_model = await orchestrator.get_model("BlogPost")

# Validate some data
data = {
    "title": "My New Blog Post",
    "content": "This is the content of my blog post.",
    "status": "draft",
    "belongs_to": {
        "id": "website-123",
        "type": "Website"
    }
}
validation_result = await orchestrator.validate_data(data, "BlogPost")

if validation_result.is_valid:
    # Create the blog post
    result = await create_blog_post(data)
    print(f"Created blog post: {result['data']['id']}")
else:
    print(f"Validation errors: {validation_result.errors}")

# Fetch blog posts for a website
website_id = "website-123"
posts = await get_blog_posts_by_website(website_id)
```

## Best Practices for Model Implementation

1. **Follow the Object Taxonomy**: Classify models as Alpha, Beta, Gamma, Qualifier, or Organizer objects.
2. **Standardize Field Names**: Use consistent field names across models (id, created_at, updated_at, etc.).
3. **Document Thoroughly**: Add comprehensive descriptions and examples to model definitions.
4. **Test Model Definitions**: Verify that example data passes validation.
5. **Implement Proper Validation**: Define appropriate validation rules for each field.
6. **Use UUIDs for IDs**: Prefer UUIDs over sequential integers for primary keys.
7. **Include Timestamps**: Always include created_at and updated_at fields.
8. **Define Relationships Clearly**: Use explicit relationship fields like belongs_to.
9. **Consider Performance**: Optimize database queries and model validation for frequently used models.
10. **Version Your Models**: Track changes to model definitions to handle migrations.

## Model Implementation Checklist

- [ ] Model schema defined with complete field definitions
- [ ] Model registered in the Models Service
- [ ] Database table created with appropriate schema
- [ ] Validation logic implemented and tested
- [ ] Helper methods created for common operations
- [ ] Documentation updated to include the new model
- [ ] Test cases written for model operations
- [ ] Migration plan established for model updates

For more detailed information about model types, refer to:

- [Alpha Objects Listing](02_Alpha_Objects_Listing.md)
- [Beta Objects Listing](03_Beta_Objects_Listing.md)
- [Gamma Objects Listing](04_Gamma_Objects_Listing.md)
- [Qualifier Objects Listing](05_Qualifier_Objects_Listing.md)
- [Organizer Objects Listing](06_Organizer_Objects_Listing.md) 