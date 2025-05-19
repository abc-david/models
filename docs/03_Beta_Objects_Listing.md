# Beta-Level Objects Listing

This document provides a comprehensive list of all Beta-level objects in the Content Generation Framework. These are mid-level objects that belong to alpha-level containers.

## Beta-Level Objects (Content Units)

1. **Blog Post**
   - Standard article content with title, content, and metadata
   - Used for blog articles and general content

2. **Landing Page**
   - Conversion-focused page with specific goals
   - Used for marketing landing pages and conversion pages

3. **Product Page**
   - Page describing a specific product
   - Used for product listings and descriptions

4. **Product Review**
   - Evaluation of a product with pros and cons
   - Used for product reviews and comparisons

5. **Product Comparison**
   - Side-by-side evaluation of multiple products
   - Used for product comparisons and buying guides

6. **Listicle**
   - List-based article with numbered items
   - Used for list articles and roundups

7. **How-To Guide**
   - Step-by-step instructional content
   - Used for tutorials and instructions

8. **Case Study**
   - Detailed analysis of an implementation
   - Used for success stories and examples

9. **Whitepaper**
   - In-depth report on a specific topic
   - Used for technical papers and research

10. **Ebook Chapter**
    - Section of an ebook
    - Used for ebook content organization

11. **Book Chapter**
    - Section of a book
    - Used for book content organization

12. **FAQ Page**
    - Collection of questions and answers
    - Used for frequently asked questions

13. **Glossary Page**
    - Collection of term definitions
    - Used for terminology and definitions

14. **Email Message**
    - Single email in a campaign
    - Used for email marketing

15. **Social Media Post**
    - Individual social media content piece
    - Used for social media content

16. **Tweet Thread**
    - Connected series of tweets
    - Used for Twitter content

17. **Podcast Episode**
    - Single audio episode
    - Used for podcast content

18. **Video Lesson**
    - Individual video in a course
    - Used for video content

19. **Tutorial**
    - Step-by-step instruction
    - Used for learning content

20. **API Documentation**
    - Technical API reference
    - Used for developer documentation

21. **Newsletter Issue**
    - Single edition of a newsletter
    - Used for newsletter content

## Common Properties of Beta-Level Objects

Beta-level objects typically contain the following common fields:

```json
{
  "id": { "type": "str" },
  "title": { "type": "str" },
  "content": { "type": "str" },
  "excerpt": { "type": "str" },
  "belongs_to": { "type": "Dict[str, Any]" },
  "metadata": { "type": "Dict[str, Any]" },
  "created_at": { "type": "datetime" },
  "updated_at": { "type": "datetime" },
  "status": { "type": "str" },
  "slug": { "type": "str" }
}
```

## Relationships with Alpha-Level Objects

Beta-level objects are typically contained within Alpha-level objects, and this relationship is represented in the `belongs_to` field:

```json
"belongs_to": {
  "website": "website-123",
  "topic": "topic-456",
  "category": "category-789"
}
```

## Integration with Models Service

Beta-level objects are registered in the Models Service and can be accessed and validated through the orchestrator:

```python
from services.models import orchestrator

# Get the BlogPost model
blog_post_model = await orchestrator.get_model("BlogPost")

# Validate data against the BlogPost model
validation_result = await orchestrator.validate_data(blog_post_data, "BlogPost")
```

See [Object Model Design Principles](01_Object_Model_Design_Principles.md) for more information about the classification and design of these objects. 