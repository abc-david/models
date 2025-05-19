# Organizer Objects Listing

This document provides a comprehensive list of all Organizer objects in the Content Generation Framework. Organizer objects are structural components that arrange and group content objects into logical collections.

## Organizer Objects

1. **Collection**
   - General-purpose content grouping
   - Used for flexible content organization

2. **Series**
   - Ordered sequence of content
   - Used for sequential content

3. **Taxonomy**
   - Hierarchical classification system
   - Used for content categorization

4. **ContentMap**
   - Structural blueprint
   - Used for content planning

5. **Sitemap**
   - Website structure definition
   - Used for navigation planning

6. **ContentCalendar**
   - Temporal organization of content
   - Used for publication scheduling

7. **WorkflowTemplate**
   - Process definition for content creation
   - Used for standardizing content creation

8. **ContentLayout**
   - Visual arrangement template
   - Used for content presentation

9. **ContentBundle**
   - Packaged content group
   - Used for distribution

10. **Campaign**
    - Goal-oriented content group
    - Used for marketing initiatives

## Common Properties of Organizer Objects

Organizer objects typically contain the following common fields:

```json
{
  "id": { "type": "str" },
  "name": { "type": "str" },
  "description": { "type": "str" },
  "content_items": { "type": "List[Dict[str, Any]]" },
  "structure": { "type": "Dict[str, Any]" },
  "metadata": { "type": "Dict[str, Any]" },
  "created_at": { "type": "datetime" },
  "updated_at": { "type": "datetime" },
  "status": { "type": "str" }
}
```

## Relationship with Content Objects

Organizer objects can contain references to any level of content objects (Alpha, Beta, or Gamma). The relationship is typically defined in the `content_items` field:

```json
"content_items": [
  {
    "id": "blog-123",
    "type": "BlogPost",
    "position": 1,
    "status": "published"
  },
  {
    "id": "landing-456",
    "type": "LandingPage",
    "position": 2,
    "status": "draft"
  }
]
```

## Structure Definition

Organizer objects often include a `structure` field that defines how content is arranged:

```json
"structure": {
  "type": "hierarchical",
  "levels": [
    {
      "name": "section",
      "allowed_types": ["Section", "Chapter"]
    },
    {
      "name": "unit",
      "allowed_types": ["Unit", "Lesson"]
    },
    {
      "name": "content",
      "allowed_types": ["BlogPost", "Article", "Tutorial"]
    }
  ]
}
```

## Integration with Models Service

Organizer objects are registered in the Models Service and can be accessed and validated through the orchestrator:

```python
from services.models import orchestrator

# Get the Collection model
collection_model = await orchestrator.get_model("Collection")

# Validate data against the Collection model
validation_result = await orchestrator.validate_data(collection_data, "Collection")

# Create a new collection
new_collection = await orchestrator.create_model_instance("Collection", {
    "name": "Technical Tutorials",
    "description": "A collection of technical tutorials on programming",
    "content_items": [
        {"id": "tutorial-123", "type": "Tutorial", "position": 1}
    ]
})
```

## Relationship to Database Schema

Organizer objects are typically stored in dedicated tables in the database with join tables to track relationships to content objects:

```sql
CREATE TABLE collections (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    structure JSONB,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status TEXT DEFAULT 'active'
);

CREATE TABLE collection_items (
    collection_id UUID REFERENCES collections(id),
    item_id UUID NOT NULL,
    item_type TEXT NOT NULL,
    position INTEGER,
    status TEXT DEFAULT 'active',
    metadata JSONB,
    PRIMARY KEY (collection_id, item_id)
);
```

See [Object Model Design Principles](01_Object_Model_Design_Principles.md) for more information about the classification and design of these objects. 