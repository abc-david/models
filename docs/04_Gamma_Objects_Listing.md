# Gamma-Level Objects Listing

This document provides a comprehensive list of all Gamma-level objects in the Content Generation Framework. These are low-level components that form parts of beta-level objects.

## Gamma-Level Objects (Content Components)

1. **Call to Action (CTA)**
   - Prompts for user action
   - Used for conversion elements

2. **Table**
   - Structured data presentation
   - Used for data display

3. **Blockquote**
   - Featured quote or excerpt
   - Used for highlighting content

4. **Image with Caption**
   - Visual element with descriptive text
   - Used for visual content

5. **Code Snippet**
   - Programming code example
   - Used for technical content

6. **Interactive Demo**
   - Interactive element
   - Used for interactive content

7. **Video Embed**
   - Embedded video content
   - Used for video integration

8. **Audio Player**
   - Embedded audio content
   - Used for audio integration

9. **Key Takeaway**
   - Important conclusion or learning
   - Used for highlighting key points

10. **FAQ Item**
    - Single question and answer pair
    - Used for FAQ content

11. **Testimonial**
    - Customer or user quote
    - Used for social proof

12. **Step Instructions**
    - Individual step in a process
    - Used for tutorials

13. **Definition**
    - Term explanation
    - Used for glossary items

14. **Sidebar Content**
    - Supplementary information
    - Used for additional content

15. **Pull Quote**
    - Highlighted quote from text
    - Used for emphasis

16. **Infographic**
    - Visual representation of information
    - Used for data visualization

17. **Data Visualization**
    - Chart, graph, or data display
    - Used for data presentation

18. **Product Feature**
    - Specific product capability
    - Used for product descriptions

19. **Pros and Cons List**
    - Advantages and disadvantages
    - Used for evaluations

20. **Checklist**
    - Action item list
    - Used for task organization

## Common Properties of Gamma-Level Objects

Gamma-level objects typically contain the following common fields:

```json
{
  "id": { "type": "str" },
  "type": { "type": "str" },
  "content": { "type": "str" },
  "metadata": { "type": "Dict[str, Any]" },
  "belongs_to": { "type": "Dict[str, Any]" },
  "created_at": { "type": "datetime" },
  "updated_at": { "type": "datetime" }
}
```

## Relationship with Beta-Level Objects

Gamma-level objects are typically embedded within Beta-level objects. They can be:

1. **Directly embedded in markdown** content (extracted during parsing)
2. **Explicitly referenced** in a beta-level object's `extracted_components` field
3. **Stored separately** and referenced by ID

Example of extraction and referencing:

```json
"extracted_components": {
  "key_takeaways": ["takeaway-123", "takeaway-456"],
  "code_snippets": ["snippet-789", "snippet-012"],
  "tables": ["table-345"]
}
```

## Integration with Models Service

Gamma-level objects are registered in the Models Service and can be accessed and validated through the orchestrator:

```python
from services.models import orchestrator

# Get the CodeSnippet model
code_snippet_model = await orchestrator.get_model("CodeSnippet")

# Validate data against the CodeSnippet model
validation_result = await orchestrator.validate_data(code_snippet_data, "CodeSnippet")
```

See [Object Model Design Principles](01_Object_Model_Design_Principles.md) for more information about the classification and design of these objects. 