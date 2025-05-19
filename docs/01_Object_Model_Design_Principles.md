# Object Model Design Principles

## Overview

This document outlines the key structural decisions for the object models in the Content Generation Framework. These decisions establish the foundation for how content is defined, stored, validated, and related within the system.

## Comprehensive Object Taxonomy

The framework uses a hierarchical taxonomy to classify all content objects:

### Alpha-Level Objects (Top-Level Containers)

Top-level containers that represent standalone content entities. See [Alpha Objects Listing](02_Alpha_Objects_Listing.md) for details.

### Beta-Level Objects (Content Units)

Mid-level objects that belong to alpha-level containers. See [Beta Objects Listing](03_Beta_Objects_Listing.md) for details.

### Gamma-Level Objects (Content Components)

Low-level components that form parts of beta-level objects. See [Gamma Objects Listing](04_Gamma_Objects_Listing.md) for details.

### Organizer Objects (Structural Elements)

Objects that categorize and organize other content:

1. **Topic** - Primary subject area
2. **Subtopic** - Secondary subject area
3. **Category** - Content classification
4. **Subcategory** - Nested classification
5. **Table of Contents** - Content organization listing
6. **Index** - Alphabetical topic listing
7. **Sitemap** - Website structure
8. **Course Module** - Group of related lessons
9. **Taxonomy Term** - Hierarchical classification term
10. **Content Hub** - Centralized topic collection
11. **Series** - Related content published in sequence
12. **Content Pillar** - Core content entity with related pieces
13. **Collections** - Curated content groupings
14. **Section** - Distinct part of a document
15. **Menu** - Navigation structure

### Qualifier Objects (Metadata Elements)

Objects that add metadata or qualifiers to other content:

1. **Tag** - Content classification label
2. **Keyword** - SEO search term
3. **Audience** - Target reader/user group
4. **Difficulty Level** - Content complexity indicator
5. **Author** - Content creator
6. **Content Status** - Publication workflow state
7. **Reading Time** - Estimated consumption duration
8. **SEO Metadata** - Search optimization information
9. **Language** - Content language identifier
10. **Geographic Target** - Location specificity
11. **Content License** - Usage permissions
12. **Version** - Content iteration identifier
13. **Revision** - Tracked content change
14. **Lifecycle Stage** - Content stage in buyer journey
15. **Sentiment** - Emotional tone indicator

## Object Type Classification

All object models in the framework are explicitly classified using a hierarchical taxonomy:

1. **Alpha-Level Objects**: Top-level containers that represent standalone content entities
2. **Beta-Level Objects**: Mid-level objects that belong to alpha-level containers
3. **Gamma-Level Objects**: Low-level components that form parts of beta-level objects
4. **Organizer Objects**: Objects that categorize and organize other content
5. **Qualifier Objects**: Objects that add metadata or qualifiers to other content

Each object model includes an explicit `object_type` field to clearly identify its position in this hierarchy.

## Organizational System Design

The framework implements two primary organizational systems with distinct purposes:

1. **Topics/Subtopics**: For organizing informational content and building topical authority (helps with SEO and establishing expertise)

2. **Product Categories/Subcategories**: For organizing commercial content and facilitating monetization (directly supports affiliate marketing)

This dual approach separates informational content organization from commercial content organization, providing clarity for both content creators and users while optimizing for both SEO and monetization.

Categories in this framework are specifically designed for product/SaaS tool organization to support effective affiliate marketing.

## Markdown as Primary Content Format

All content in the framework is produced and stored in markdown format. This decision brings several benefits:

1. **Human-Readable**: Markdown is easy to read and write by humans
2. **Portable**: Content can be easily moved between systems
3. **Convertible**: Markdown can be readily converted to HTML/CSS or other formats
4. **Future-Proof**: Content remains accessible even if presentation needs change
5. **Styling Separation**: Keeps styling concerns separate from content concerns

Content is stored in its complete form, without placeholders or assembly requirements. For alpha and beta level objects, the markdown content should be complete and ready for human consumption.

## Hierarchical Content Organization

### Content Hierarchy for Container Objects

Alpha and beta level container objects use a consistent `content_hierarchy` field to represent their inner hierarchical organization:

```json
"content_hierarchy": {
  "type": "Dict[str, Any]",
  "args": {
    "description": "Hierarchical organization of all content",
    "default_factory": "dict"
  }
}
```

This standardized approach makes it easy to:
- Navigate the content structure
- Understand the relationships between content elements
- Maintain consistent organization across different content types

For websites, the content hierarchy might include topics, subtopics, categories, and subcategories:

```json
"content_hierarchy": {
  "topics": [
    {
      "id": "topic-1",
      "name": "Smartphones",
      "slug": "smartphones",
      "subtopics": [...]
    }
  ],
  "categories": [
    {
      "id": "category-1",
      "name": "Reviews",
      "slug": "reviews",
      "subcategories": [...]
    }
  ]
}
```

For books, the content hierarchy might include chapters, sections, and appendices.

### Bidirectional Relationships with Belongs_To

Objects that are contained within other objects use a standardized `belongs_to` field to reference their containers:

```json
"belongs_to": {
  "type": "Dict[str, Any]",
  "args": {
    "description": "References to container objects",
    "default_factory": "dict"
  }
}
```

This enables bidirectional navigation of the content structure:
- Alpha-level objects contain hierarchies of their contents
- Beta-level and gamma-level objects reference their containers

Example of a blog post's `belongs_to` field:
```json
"belongs_to": {
  "website": "website-123",
  "topic": "topic-456",
  "category": "category-789"
}
```

## Model Definition Format

Object models are stored in the `object_models` table with a structured JSONB format:

```json
{
  "name": "BlogPost",
  "object_type": "beta",
  "fields": {
    "title": {
      "type": "str",
      "args": {
        "description": "The blog post title"
      }
    },
    "slug": {
      "type": "str",
      "args": {
        "description": "URL-friendly version of the title"
      }
    },
    "content": {
      "type": "str",
      "args": {
        "description": "Complete markdown content including all components"
      }
    },
    "excerpt": {
      "type": "str",
      "args": {
        "description": "Short summary of the post",
        "default": ""
      }
    },
    "belongs_to": {
      "type": "Dict[str, Any]",
      "args": {
        "description": "References to container objects",
        "default_factory": "dict"
      }
    },
    "key_takeaways": {
      "type": "List[str]",
      "args": {
        "description": "Main points for readers to remember",
        "default_factory": "list"
      }
    },
    "extracted_components": {
      "type": "Dict[str, List]",
      "args": {
        "description": "Components extracted from markdown content",
        "default_factory": "dict"
      }
    }
  },
  "metadata_schema": {
    "required": [
      "content_type", "word_count", "tags"
    ],
    "recommended": [
      "reading_time", "audience"
    ]
  },
  "validators": [
    {
      "name": "title_not_empty",
      "fields": ["title"],
      "pre": true,
      "code": "def title_not_empty(cls, v):\n    if not v.strip():\n        raise ValueError('Title cannot be empty')\n    return v"
    }
  ]
}
```

## Integration with Database and Models Service

This object model system is fully integrated with the Models Service (`/services/models`). The service offers:

1. **Dynamic Model Generation**: Converts JSON schema definitions into Pydantic models
2. **Validation**: Ensures content meets the requirements of its model
3. **Schema Management**: Tools for creating, updating, and verifying database schemas
4. **Storage Integration**: Seamless integration with the database storage system

The Models Service provides a central orchestrator that makes it easy to work with object models throughout the content generation workflow.

## Conclusion

These design principles guide the implementation of the object model system in the Content Generation Framework, ensuring a consistent and maintainable approach to content modeling, validation, and storage. 