"""
Example usage of the Models Service.

This example demonstrates how to:
1. Define a model
2. Register it with the ModelRegistry
3. Validate data against it
4. Convert between different schema formats
"""

import sys
import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from services.models.core import (
    BaseModel, 
    ContentModel, 
    FieldDefinition, 
    ModelRegistry
)
from services.models.validation import ModelValidator
from services.models.schemas import (
    pydantic_to_model_schema,
    model_schema_to_json_schema
)

# Define a model class
class BlogPost(ContentModel):
    """Model definition for a blog post."""
    
    model_name = "blog_post"
    
    @classmethod
    def get_fields(cls) -> Dict[str, FieldDefinition]:
        """Define the fields for this model."""
        return {
            "title": FieldDefinition(
                name="title",
                field_type="str",
                required=True,
                description="The title of the blog post"
            ),
            "content": FieldDefinition(
                name="content",
                field_type="str",
                required=True,
                description="The main content of the blog post"
            ),
            "author": FieldDefinition(
                name="author",
                field_type="str",
                required=True,
                description="The author of the blog post"
            ),
            "tags": FieldDefinition(
                name="tags",
                field_type="List[str]",
                required=False,
                default=[],
                description="Tags associated with the blog post"
            ),
            "published_date": FieldDefinition(
                name="published_date",
                field_type="datetime",
                required=False,
                description="The date the blog post was published"
            ),
            "is_published": FieldDefinition(
                name="is_published",
                field_type="bool",
                required=False,
                default=False,
                description="Whether the blog post is published"
            )
        }
    
    @classmethod
    def get_validators(cls) -> List[Dict[str, Any]]:
        """Define custom validators for this model."""
        return [
            {
                "name": "validate_title_length",
                "fields": ["title"],
                "code": """
def validate_title_length(data, result):
    title = data.get('title', '')
    if len(title) < 5:
        result.add_error('title', 'Title must be at least 5 characters long')
    if len(title) > 100:
        result.add_error('title', 'Title must be at most 100 characters long')
"""
            }
        ]


def main():
    """Run the example."""
    print("Models Service Example\n")
    
    # Register the model
    print("Registering BlogPost model...")
    ModelRegistry.register_model(BlogPost)
    
    # Get the model schema
    print("Getting model schema...")
    blog_post_schema = ModelRegistry.get_schema("blog_post")
    print(f"Schema name: {blog_post_schema['model_name']}")
    print(f"Field count: {len(blog_post_schema['fields'])}")
    print(f"Validator count: {len(blog_post_schema['validators'])}")
    
    # Convert to JSON Schema
    print("\nConverting to JSON Schema...")
    json_schema = model_schema_to_json_schema(blog_post_schema)
    print(json.dumps(json_schema, indent=2))
    
    # Validate valid data
    print("\nValidating valid data...")
    valid_data = {
        "title": "My First Blog Post",
        "content": "This is the content of my first blog post.",
        "author": "John Doe",
        "tags": ["example", "first-post"],
        "published_date": datetime.now().isoformat(),
        "is_published": True
    }
    
    validator = ModelValidator()
    result = validator.validate_against_model(valid_data, blog_post_schema)
    
    print(f"Valid: {result.is_valid}")
    if result.errors:
        print("Errors:")
        for error in result.errors:
            print(f"  - {error['path']}: {error['message']}")
    
    # Validate invalid data
    print("\nValidating invalid data...")
    invalid_data = {
        "title": "Hi",  # Too short
        "content": "This is the content of my first blog post.",
        "tags": "not-a-list",  # Wrong type
        "is_published": "yes"  # Wrong type
    }
    
    result = validator.validate_against_model(invalid_data, blog_post_schema)
    
    print(f"Valid: {result.is_valid}")
    if result.errors:
        print("Errors:")
        for error in result.errors:
            print(f"  - {error['path']}: {error['message']}")
    
    # Validate with partial data
    print("\nValidating partial data (partial=True)...")
    partial_data = {
        "title": "My Partial Blog Post",
        "content": "This is a partial blog post."
        # Missing 'author', which is required
    }
    
    result = validator.validate_against_model(partial_data, blog_post_schema, partial=True)
    
    print(f"Valid: {result.is_valid}")
    if result.errors:
        print("Errors:")
        for error in result.errors:
            print(f"  - {error['path']}: {error['message']}")


if __name__ == "__main__":
    main() 