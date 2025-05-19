"""
File: database/storage/models.py
MODULE: Storage Models
PURPOSE: SQL queries and table definitions for object storage
DEPENDENCIES: None

This module contains SQL queries and table definitions used by the ObjectStorage class.
All queries are parameterized and use the schema_name parameter for proper schema support.
"""

# Table creation
CREATE_CONTENTS_TABLE = """
CREATE TABLE IF NOT EXISTS {schema_name}.contents (
    id UUID PRIMARY KEY,
    content_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL,
    content JSONB NOT NULL DEFAULT '{{}}',
    metadata JSONB NOT NULL DEFAULT '{{}}',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS {schema_name}_contents_type_idx 
ON {schema_name}.contents(content_type);

CREATE INDEX IF NOT EXISTS {schema_name}_contents_slug_idx 
ON {schema_name}.contents(slug);

CREATE INDEX IF NOT EXISTS {schema_name}_contents_metadata_idx 
ON {schema_name}.contents USING GIN (metadata);

CREATE INDEX IF NOT EXISTS {schema_name}_contents_content_idx 
ON {schema_name}.contents USING GIN (content);
"""

# Query templates
GET_OBJECT = """
SELECT id, content_type, title, slug, content, metadata, created_at, updated_at
FROM {schema_name}.contents
WHERE id = %s
"""

GET_OBJECTS_BY_TYPE = """
SELECT id, content_type, title, slug, content, metadata, created_at, updated_at
FROM {schema_name}.contents
WHERE content_type = %s
ORDER BY created_at DESC
"""

GET_OBJECTS_BY_PARENT = """
SELECT id, content_type, title, slug, content, metadata, created_at, updated_at
FROM {schema_name}.contents
WHERE metadata->>'parent_id' = %s
ORDER BY created_at DESC
"""

GET_OBJECTS_BY_HIERARCHY = """
SELECT id, content_type, title, slug, content, metadata, created_at, updated_at
FROM {schema_name}.contents
WHERE (metadata->>'hierarchy_level')::int = %s
ORDER BY created_at DESC
"""

GET_OBJECTS_BY_REFERENCE = """
SELECT id, content_type, title, slug, content, metadata, created_at, updated_at
FROM {schema_name}.contents
WHERE metadata->'references' @> %s::jsonb
ORDER BY created_at DESC
"""

GET_OBJECTS_BY_REFERENCED_BY = """
SELECT id, content_type, title, slug, content, metadata, created_at, updated_at
FROM {schema_name}.contents
WHERE metadata->'referenced_by' @> %s::jsonb
ORDER BY created_at DESC
"""

SEARCH_OBJECTS = """
SELECT id, content_type, title, slug, content, metadata, created_at, updated_at
FROM {schema_name}.contents
WHERE 
    title ILIKE %s OR
    content::text ILIKE %s OR
    metadata::text ILIKE %s
ORDER BY created_at DESC
"""

UPDATE_OBJECT = """
UPDATE {schema_name}.contents
SET 
    content = %s,
    metadata = %s,
    updated_at = CURRENT_TIMESTAMP
WHERE id = %s
"""

DELETE_OBJECT = """
DELETE FROM {schema_name}.contents
WHERE id = %s
"""

BATCH_INSERT_OBJECTS = """
INSERT INTO {schema_name}.contents
(id, content_type, title, slug, content, metadata, created_at, updated_at)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
"""

BATCH_UPDATE_OBJECTS = """
UPDATE {schema_name}.contents
SET 
    content = %s,
    metadata = %s,
    updated_at = CURRENT_TIMESTAMP
WHERE id = %s
"""