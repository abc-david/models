# Alpha-Level Objects Listing

This document provides a comprehensive list of all Alpha-level objects in the Content Generation Framework. These are top-level containers that represent standalone content entities.

## Alpha-Level Objects (Top-Level Containers)

1. **Website**
   - Top-level container for website content with topics, categories, and settings
   - Used for content marketing websites, blogs, documentation sites, and product websites

2. **Book**
   - Top-level container for book content with chapters, front matter, and back matter
   - Used for book publishing, technical manuals, educational resources, and fiction works

3. **Ebook**
   - Top-level container for digital book content with specialized digital publishing fields
   - Used for digital publishing, lead magnets, online courses, and digital products

4. **Documentation Site**
   - Top-level container for technical documentation with specialized structure
   - Used for API documentation, technical guides, and reference materials

5. **Knowledge Base**
   - Top-level container for structured information repository
   - Used for FAQs, help centers, and information databases

6. **Learning Management System**
   - Top-level container for educational platform with courses
   - Used for online learning platforms and educational content

7. **Email Campaign**
   - Top-level container for series of related email messages
   - Used for marketing campaigns and newsletter series

8. **Social Media Campaign**
   - Top-level container for collection of coordinated social media posts
   - Used for social media marketing and content campaigns

9. **Podcast Series**
   - Top-level container for collection of audio episodes
   - Used for podcast content and audio series

10. **Video Course**
    - Top-level container for educational video series
    - Used for video tutorials and online courses

11. **Newsletter**
    - Top-level container for recurring publication sent to subscribers
    - Used for email newsletters and regular updates

## Common Properties of Alpha-Level Objects

All alpha-level objects typically contain the following common fields:

```json
{
  "id": { "type": "str" },
  "name": { "type": "str" },
  "description": { "type": "str" },
  "content_hierarchy": { "type": "Dict[str, Any]" },
  "metadata": { "type": "Dict[str, Any]" },
  "settings": { "type": "Dict[str, Any]" },
  "created_at": { "type": "datetime" },
  "updated_at": { "type": "datetime" },
  "status": { "type": "str" }
}
```

## Integration with Models Service

Alpha-level objects are registered in the Models Service and can be accessed and validated through the orchestrator:

```python
from services.models import orchestrator

# Get the Website model
website_model = await orchestrator.get_model("Website")

# Validate data against the Website model
validation_result = await orchestrator.validate_data(website_data, "Website")
```

See [Object Model Design Principles](01_Object_Model_Design_Principles.md) for more information about the classification and design of these objects. 