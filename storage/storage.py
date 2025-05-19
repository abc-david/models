"""
File: database/storage/storage.py
MODULE: Object Storage
PURPOSE: Provides storage operations for content objects
CLASSES: ObjectStorage
DEPENDENCIES:
    - PostgreSQL with JSONB support
    - UUID for primary keys
    - Timestamps for tracking
    - DBOperator for database operations

This class provides a high-level interface for storing and retrieving content objects
in the Content Generation Framework. It handles metadata enrichment, cross-references,
and maintains referential integrity through metadata-based relationships.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from contextlib import contextmanager

from services.database.db_operator import DBOperator
from services.models.storage.models import (
    CREATE_CONTENTS_TABLE,
    GET_OBJECT,
    GET_OBJECTS_BY_TYPE,
    GET_OBJECTS_BY_PARENT,
    GET_OBJECTS_BY_HIERARCHY,
    GET_OBJECTS_BY_REFERENCE,
    GET_OBJECTS_BY_REFERENCED_BY,
    SEARCH_OBJECTS,
    UPDATE_OBJECT,
    DELETE_OBJECT,
    BATCH_INSERT_OBJECTS,
    BATCH_UPDATE_OBJECTS
)

class ObjectStorage:
    def __init__(self, db_operator: DBOperator, schema_name: str = "public"):
        """
        Initialize the ObjectStorage with a database operator.
        
        Args:
            db_operator: DBOperator instance for database operations
            schema_name: Database schema name (default: "public")
        """
        self.db = db_operator
        self.schema_name = schema_name
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        """Ensure required tables exist."""
        # Create schema if it doesn't exist
        if self.schema_name != "public":
            self.db.execute(f"CREATE SCHEMA IF NOT EXISTS {self.schema_name}")
        
        # Create tables and indexes
        self.db.execute(CREATE_CONTENTS_TABLE.format(schema_name=self.schema_name))

    @classmethod
    def create_project_schema(cls, db_operator: DBOperator, project_id: str) -> 'ObjectStorage':
        """
        Create a new project schema with all required tables and indexes.
        
        Args:
            db_operator: DBOperator instance for database operations
            project_id: UUID of the project
            
        Returns:
            ObjectStorage: Instance configured for the new project schema
        """
        schema_name = f"project_{project_id}"
        
        # Create schema
        db_operator.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
        
        # Create storage instance for the new schema
        storage = cls(db_operator, schema_name)
        
        # Create additional project-specific indexes
        storage._create_project_indexes()
        
        return storage

    def _create_project_indexes(self) -> None:
        """Create additional indexes specific to project schemas."""
        # Composite index for common queries
        self.db.execute(f"""
            CREATE INDEX IF NOT EXISTS {self.schema_name}_contents_type_created_idx 
            ON {self.schema_name}.contents(content_type, created_at DESC)
        """)
        
        # Partial index for active objects
        self.db.execute(f"""
            CREATE INDEX IF NOT EXISTS {self.schema_name}_contents_active_idx 
            ON {self.schema_name}.contents(id) 
            WHERE metadata->>'status' = 'active'
        """)
        
        # Expression index for case-insensitive title search
        self.db.execute(f"""
            CREATE INDEX IF NOT EXISTS {self.schema_name}_contents_title_lower_idx 
            ON {self.schema_name}.contents(LOWER(title))
        """)
        
        # Index for metadata tags (if used)
        self.db.execute(f"""
            CREATE INDEX IF NOT EXISTS {self.schema_name}_contents_metadata_tags_idx 
            ON {self.schema_name}.contents USING GIN ((metadata->'tags'))
        """)
        
        # Index for metadata custom fields (if used)
        self.db.execute(f"""
            CREATE INDEX IF NOT EXISTS {self.schema_name}_contents_metadata_custom_idx 
            ON {self.schema_name}.contents USING GIN ((metadata->'custom_fields'))
        """)

    @contextmanager
    def transaction(self):
        """Context manager for database transactions."""
        try:
            self.db.begin_transaction()
            yield
            self.db.commit_transaction()
        except Exception as e:
            self.db.rollback_transaction()
            raise e

    def store_object(
        self,
        content_type: str,
        title: str,
        content: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        parent_id: Optional[str] = None
    ) -> str:
        """
        Store a new object with enriched metadata.
        
        Args:
            content_type: Type of content (e.g., 'website', 'category')
            title: Object title
            content: Main content as JSON
            metadata: Additional metadata (optional)
            parent_id: ID of parent object (optional)
            
        Returns:
            str: Generated UUID for the object
        """
        object_id = str(uuid.uuid4())
        slug = self._generate_slug(title)
        
        # Enrich metadata
        enriched_metadata = self._enrich_metadata(
            metadata or {},
            content_type,
            parent_id
        )
        
        # Update cross-references
        self._update_cross_references(object_id, content, enriched_metadata)
        
        # Store the object
        with self.transaction():
            self.db.execute(
                f"INSERT INTO {self.schema_name}.contents "
                "(id, content_type, title, slug, content, metadata) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (object_id, content_type, title, slug, content, enriched_metadata)
            )
        
        return object_id

    def batch_store_objects(
        self,
        objects: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Store multiple objects in a single transaction.
        
        Args:
            objects: List of object dictionaries with required fields:
                    - content_type: str
                    - title: str
                    - content: Dict[str, Any]
                    - metadata: Optional[Dict[str, Any]]
                    - parent_id: Optional[str]
                    
        Returns:
            List[str]: List of generated UUIDs
        """
        object_ids = []
        values = []
        
        for obj in objects:
            object_id = str(uuid.uuid4())
            object_ids.append(object_id)
            
            # Enrich metadata
            enriched_metadata = self._enrich_metadata(
                obj.get('metadata', {}),
                obj['content_type'],
                obj.get('parent_id')
            )
            
            # Generate slug
            slug = self._generate_slug(obj['title'])
            
            values.append((
                object_id,
                obj['content_type'],
                obj['title'],
                slug,
                obj['content'],
                enriched_metadata,
                datetime.now(),
                datetime.now()
            ))
        
        # Store all objects
        with self.transaction():
            self.db.execute_batch(
                BATCH_INSERT_OBJECTS.format(schema_name=self.schema_name),
                values
            )
            
            # Update cross-references for all objects
            for obj_id, obj in zip(object_ids, objects):
                self._update_cross_references(
                    obj_id,
                    obj['content'],
                    obj.get('metadata', {})
                )
        
        return object_ids

    def get_object(self, object_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve an object by its ID.
        
        Args:
            object_id: UUID of the object
            
        Returns:
            Optional[Dict[str, Any]]: Object data if found, None otherwise
        """
        result = self.db.fetch_one(
            GET_OBJECT.format(schema_name=self.schema_name),
            (object_id,)
        )
        return result if result else None

    def get_objects_by_type(
        self,
        content_type: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Retrieve objects by content type.
        
        Args:
            content_type: Type of content to retrieve
            limit: Maximum number of objects to return
            offset: Number of objects to skip
            
        Returns:
            List[Dict[str, Any]]: List of matching objects
        """
        query = f"{GET_OBJECTS_BY_TYPE} LIMIT %s OFFSET %s"
        return self.db.fetch_all(
            query.format(schema_name=self.schema_name),
            (content_type, limit, offset)
        )

    def get_objects_by_parent(
        self,
        parent_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Retrieve objects by parent ID.
        
        Args:
            parent_id: ID of parent object
            limit: Maximum number of objects to return
            offset: Number of objects to skip
            
        Returns:
            List[Dict[str, Any]]: List of child objects
        """
        query = f"{GET_OBJECTS_BY_PARENT} LIMIT %s OFFSET %s"
        return self.db.fetch_all(
            query.format(schema_name=self.schema_name),
            (parent_id, limit, offset)
        )

    def get_objects_by_hierarchy(
        self,
        level: int,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Retrieve objects by hierarchy level.
        
        Args:
            level: Hierarchy level (0 for root, 1 for first level, etc.)
            limit: Maximum number of objects to return
            offset: Number of objects to skip
            
        Returns:
            List[Dict[str, Any]]: List of objects at specified level
        """
        query = f"{GET_OBJECTS_BY_HIERARCHY} LIMIT %s OFFSET %s"
        return self.db.fetch_all(
            query.format(schema_name=self.schema_name),
            (level, limit, offset)
        )

    def get_objects_by_reference(
        self,
        reference_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Retrieve objects that reference a specific object.
        
        Args:
            reference_id: ID of referenced object
            limit: Maximum number of objects to return
            offset: Number of objects to skip
            
        Returns:
            List[Dict[str, Any]]: List of referencing objects
        """
        query = f"{GET_OBJECTS_BY_REFERENCE} LIMIT %s OFFSET %s"
        return self.db.fetch_all(
            query.format(schema_name=self.schema_name),
            (f'[{{"id": "{reference_id}"}}]', limit, offset)
        )

    def get_objects_by_referenced_by(
        self,
        referenced_by_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Retrieve objects that are referenced by a specific object.
        
        Args:
            referenced_by_id: ID of referencing object
            limit: Maximum number of objects to return
            offset: Number of objects to skip
            
        Returns:
            List[Dict[str, Any]]: List of referenced objects
        """
        query = f"{GET_OBJECTS_BY_REFERENCED_BY} LIMIT %s OFFSET %s"
        return self.db.fetch_all(
            query.format(schema_name=self.schema_name),
            (f'[{{"id": "{referenced_by_id}"}}]', limit, offset)
        )

    def search_objects(
        self,
        query: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Search objects by content or metadata.
        
        Args:
            query: Search query
            limit: Maximum number of objects to return
            offset: Number of objects to skip
            
        Returns:
            List[Dict[str, Any]]: List of matching objects
        """
        search_pattern = f"%{query}%"
        search_query = f"{SEARCH_OBJECTS} LIMIT %s OFFSET %s"
        return self.db.fetch_all(
            search_query.format(schema_name=self.schema_name),
            (search_pattern, search_pattern, limit, offset)
        )

    def update_object(
        self,
        object_id: str,
        content: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update an existing object.
        
        Args:
            object_id: ID of object to update
            content: New content (optional)
            metadata: New metadata (optional)
            
        Returns:
            bool: True if update successful, False otherwise
        """
        # Get current object
        current = self.get_object(object_id)
        if not current:
            return False
        
        # Prepare update data
        new_content = content if content is not None else current['content']
        new_metadata = metadata if metadata is not None else current['metadata']
        
        # Update cross-references
        self._update_cross_references(object_id, new_content, new_metadata)
        
        # Update object
        with self.transaction():
            self.db.execute(
                UPDATE_OBJECT.format(schema_name=self.schema_name),
                (new_content, new_metadata, object_id)
            )
        
        return True

    def batch_update_objects(
        self,
        updates: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Update multiple objects in a single transaction.
        
        Args:
            updates: List of update dictionaries with required fields:
                    - id: str
                    - content: Optional[Dict[str, Any]]
                    - metadata: Optional[Dict[str, Any]]
                    
        Returns:
            List[str]: List of successfully updated object IDs
        """
        values = []
        updated_ids = []
        
        for update in updates:
            # Get current object
            current = self.get_object(update['id'])
            if not current:
                continue
            
            # Prepare update data
            new_content = update.get('content', current['content'])
            new_metadata = update.get('metadata', current['metadata'])
            
            values.append((
                update['id'],
                new_content,
                new_metadata
            ))
            updated_ids.append(update['id'])
        
        if values:
            with self.transaction():
                self.db.execute_batch(
                    BATCH_UPDATE_OBJECTS.format(schema_name=self.schema_name),
                    values
                )
                
                # Update cross-references for all objects
                for update in updates:
                    self._update_cross_references(
                        update['id'],
                        update.get('content', {}),
                        update.get('metadata', {})
                    )
        
        return updated_ids

    def delete_object(self, object_id: str) -> bool:
        """
        Delete an object and update its references.
        
        Args:
            object_id: ID of object to delete
            
        Returns:
            bool: True if deletion successful, False otherwise
        """
        # Get current object
        current = self.get_object(object_id)
        if not current:
            return False
        
        # Remove references
        self._remove_references(object_id, current['metadata'])
        
        # Delete object
        with self.transaction():
            self.db.execute(
                DELETE_OBJECT.format(schema_name=self.schema_name),
                (object_id,)
            )
        
        return True

    def _enrich_metadata(
        self,
        metadata: Dict[str, Any],
        content_type: str,
        parent_id: Optional[str]
    ) -> Dict[str, Any]:
        """
        Enrich metadata with additional fields.
        
        Args:
            metadata: Original metadata
            content_type: Type of content
            parent_id: ID of parent object
            
        Returns:
            Dict[str, Any]: Enriched metadata
        """
        enriched = metadata.copy()
        
        # Add hierarchy level
        if parent_id:
            parent = self.get_object(parent_id)
            parent_level = parent['metadata'].get('hierarchy_level', 0)
            enriched['hierarchy_level'] = parent_level + 1
        else:
            enriched['hierarchy_level'] = 0
        
        # Add object type
        enriched['object_type'] = content_type
        
        # Add parent reference
        if parent_id:
            enriched['parent_id'] = parent_id
        
        # Initialize reference lists if not present
        if 'references' not in enriched:
            enriched['references'] = []
        if 'referenced_by' not in enriched:
            enriched['referenced_by'] = []
        
        return enriched

    def _update_cross_references(
        self,
        object_id: str,
        content: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> None:
        """
        Update cross-references between objects.
        
        Args:
            object_id: ID of current object
            content: Object content
            metadata: Object metadata
        """
        # Get references from content and metadata
        references = self._extract_references(content, metadata)
        
        # Update references in current object
        metadata['references'] = references
        
        # Update referenced_by in referenced objects
        for ref in references:
            ref_id = ref['id']
            ref_obj = self.get_object(ref_id)
            if ref_obj:
                ref_metadata = ref_obj['metadata']
                if 'referenced_by' not in ref_metadata:
                    ref_metadata['referenced_by'] = []
                
                # Add reference if not present
                if not any(r['id'] == object_id for r in ref_metadata['referenced_by']):
                    ref_metadata['referenced_by'].append({
                        'id': object_id,
                        'type': metadata.get('object_type', 'unknown')
                    })
                
                # Update referenced object
                self.db.execute(
                    UPDATE_OBJECT.format(schema_name=self.schema_name),
                    (ref_obj['content'], ref_metadata, ref_id)
                )

    def _remove_references(
        self,
        object_id: str,
        metadata: Dict[str, Any]
    ) -> None:
        """
        Remove references when deleting an object.
        
        Args:
            object_id: ID of object being deleted
            metadata: Object metadata
        """
        # Remove from referenced objects
        for ref in metadata.get('references', []):
            ref_id = ref['id']
            ref_obj = self.get_object(ref_id)
            if ref_obj:
                ref_metadata = ref_obj['metadata']
                if 'referenced_by' in ref_metadata:
                    ref_metadata['referenced_by'] = [
                        r for r in ref_metadata['referenced_by']
                        if r['id'] != object_id
                    ]
                    self.db.execute(
                        UPDATE_OBJECT.format(schema_name=self.schema_name),
                        (ref_obj['content'], ref_metadata, ref_id)
                    )
        
        # Remove from objects that reference this one
        for ref in metadata.get('referenced_by', []):
            ref_id = ref['id']
            ref_obj = self.get_object(ref_id)
            if ref_obj:
                ref_metadata = ref_obj['metadata']
                if 'references' in ref_metadata:
                    ref_metadata['references'] = [
                        r for r in ref_metadata['references']
                        if r['id'] != object_id
                    ]
                    self.db.execute(
                        UPDATE_OBJECT.format(schema_name=self.schema_name),
                        (ref_obj['content'], ref_metadata, ref_id)
                    )

    def _extract_references(
        self,
        content: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Extract references from content and metadata.
        
        Args:
            content: Object content
            metadata: Object metadata
            
        Returns:
            List[Dict[str, Any]]: List of references
        """
        references = []
        
        # Extract references from content
        if isinstance(content, dict):
            for value in content.values():
                if isinstance(value, dict) and 'id' in value:
                    references.append({
                        'id': value['id'],
                        'type': value.get('type', 'unknown')
                    })
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict) and 'id' in item:
                            references.append({
                                'id': item['id'],
                                'type': item.get('type', 'unknown')
                            })
        
        # Add references from metadata
        if 'references' in metadata:
            references.extend(metadata['references'])
        
        # Remove duplicates
        seen = set()
        unique_references = []
        for ref in references:
            if ref['id'] not in seen:
                seen.add(ref['id'])
                unique_references.append(ref)
        
        return unique_references

    def _generate_slug(self, title: str) -> str:
        """
        Generate a URL-friendly slug from a title.
        
        Args:
            title: Object title
            
        Returns:
            str: Generated slug
        """
        # Convert to lowercase and replace spaces with hyphens
        slug = title.lower().replace(' ', '-')
        
        # Remove special characters
        slug = ''.join(c for c in slug if c.isalnum() or c == '-')
        
        # Remove duplicate hyphens
        while '--' in slug:
            slug = slug.replace('--', '-')
        
        # Remove leading/trailing hyphens
        slug = slug.strip('-')
        
        return slug

class DatabaseTemplateStorage:
    """
    Database storage for prompt templates.
    
    This class extends ObjectStorage to provide specific functionality for
    storing, retrieving, and managing prompt templates in the database.
    """
    
    def __init__(self, db_operator: DBOperator, schema_name: str = "public"):
        """
        Initialize the DatabaseTemplateStorage with a database operator.
        
        Args:
            db_operator: DBOperator instance for database operations
            schema_name: Database schema name (default: "public")
        """
        self.storage = ObjectStorage(db_operator, schema_name)
        self.db = db_operator
        self.schema_name = schema_name
    
    def store_template(self, template_data: Dict[str, Any]) -> str:
        """
        Store a prompt template.
        
        Args:
            template_data: Dictionary containing template data
                Required keys:
                - name: Template name
                - template_text: The template content
                - variables: Dictionary of template variables
                - model: Model to use with the template
                - temperature: Temperature setting
                
        Returns:
            str: ID of the stored template
        """
        template_id = template_data.get("id") or str(uuid.uuid4())
        title = template_data.get("name", "Untitled Template")
        
        # Prepare content
        content = {
            "template_text": template_data.get("template_text", ""),
            "variables": template_data.get("variables", {}),
            "model": template_data.get("model", "gpt-4-turbo"),
            "temperature": template_data.get("temperature", 0.7),
            "description": template_data.get("description", "")
        }
        
        # Prepare metadata
        metadata = {
            "category": template_data.get("category", "general"),
            "version": template_data.get("version", "1.0"),
            "status": "active",
            "tags": template_data.get("tags", ["template"])
        }
        
        # Use ObjectStorage to store
        stored_id = self.storage.store_object(
            content_type="prompt_template",
            title=title,
            content=content,
            metadata=metadata
        )
        
        return stored_id
    
    def get_template_by_id(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a template by ID.
        
        Args:
            template_id: ID of the template to retrieve
            
        Returns:
            Optional[Dict[str, Any]]: Template data if found, None otherwise
        """
        raw_template = self.storage.get_object(template_id)
        if not raw_template:
            return None
        
        # Convert to template format
        return {
            "id": raw_template["id"],
            "name": raw_template["title"],
            "template_text": raw_template["content"].get("template_text", ""),
            "variables": raw_template["content"].get("variables", {}),
            "model": raw_template["content"].get("model", "gpt-4-turbo"),
            "temperature": raw_template["content"].get("temperature", 0.7),
            "description": raw_template["content"].get("description", ""),
            "category": raw_template["metadata"].get("category", "general"),
            "version": raw_template["metadata"].get("version", "1.0"),
            "tags": raw_template["metadata"].get("tags", []),
            "created_at": raw_template["created_at"],
            "updated_at": raw_template["updated_at"]
        }
    
    def list_templates(self, category: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        List templates, optionally filtered by category.
        
        Args:
            category: Optional category filter
            limit: Maximum number of templates to return
            offset: Number of templates to skip
            
        Returns:
            List[Dict[str, Any]]: List of templates
        """
        templates = self.storage.get_objects_by_type("prompt_template", limit, offset)
        
        # Filter by category if provided
        if category:
            templates = [t for t in templates if t["metadata"].get("category") == category]
        
        # Convert to template format
        return [{
            "id": t["id"],
            "name": t["title"],
            "template_text": t["content"].get("template_text", ""),
            "variables": t["content"].get("variables", {}),
            "model": t["content"].get("model", "gpt-4-turbo"),
            "temperature": t["content"].get("temperature", 0.7),
            "description": t["content"].get("description", ""),
            "category": t["metadata"].get("category", "general"),
            "created_at": t["created_at"],
            "updated_at": t["updated_at"]
        } for t in templates]
    
    def update_template(self, template_id: str, template_data: Dict[str, Any]) -> bool:
        """
        Update an existing template.
        
        Args:
            template_id: ID of the template to update
            template_data: Dictionary containing template data to update
                
        Returns:
            bool: True if update successful, False otherwise
        """
        # Get current template
        current = self.storage.get_object(template_id)
        if not current:
            return False
        
        # Prepare content updates
        content = dict(current["content"])
        if "template_text" in template_data:
            content["template_text"] = template_data["template_text"]
        if "variables" in template_data:
            content["variables"] = template_data["variables"]
        if "model" in template_data:
            content["model"] = template_data["model"]
        if "temperature" in template_data:
            content["temperature"] = template_data["temperature"]
        if "description" in template_data:
            content["description"] = template_data["description"]
        
        # Prepare metadata updates
        metadata = dict(current["metadata"])
        if "category" in template_data:
            metadata["category"] = template_data["category"]
        if "tags" in template_data:
            metadata["tags"] = template_data["tags"]
        if "version" in template_data:
            metadata["version"] = template_data["version"]
        
        # Use ObjectStorage to update
        return self.storage.update_object(
            object_id=template_id,
            content=content,
            metadata=metadata
        )
    
    def store_template_adaptation(
        self,
        template_id: str,
        adapted_template: Dict[str, Any],
        site_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> str:
        """
        Store an adapted version of a template for a specific site or project.
        
        Args:
            template_id: ID of the original template
            adapted_template: Dictionary containing adapted template data
            site_id: Optional site ID
            project_id: Optional project ID
                
        Returns:
            str: ID of the stored adaptation
        """
        # Get original template
        original = self.storage.get_object(template_id)
        if not original:
            raise ValueError(f"Original template {template_id} not found")
        
        adaptation_id = str(uuid.uuid4())
        title = f"{original['title']} (Adapted)"
        
        # Prepare content
        content = {
            "template_text": adapted_template.get("template_text", ""),
            "variables": adapted_template.get("variables", {}),
            "model": adapted_template.get("model", original["content"].get("model", "gpt-4-turbo")),
            "temperature": adapted_template.get("temperature", original["content"].get("temperature", 0.7)),
            "original_template_id": template_id
        }
        
        # Prepare metadata
        metadata = {
            "category": original["metadata"].get("category", "general"),
            "version": adapted_template.get("version", "1.0"),
            "status": "active",
            "tags": ["adapted_template"],
            "site_id": site_id,
            "project_id": project_id
        }
        
        # Use ObjectStorage to store
        stored_id = self.storage.store_object(
            content_type="adapted_prompt_template",
            title=title,
            content=content,
            metadata=metadata,
            parent_id=template_id
        )
        
        return stored_id
    
    def get_template_adaptation(
        self,
        template_id: str,
        site_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get an adapted template for a site or project.
        
        Args:
            template_id: ID of the original template
            site_id: Optional site ID
            project_id: Optional project ID
            
        Returns:
            Optional[Dict[str, Any]]: Adapted template if found, None otherwise
        """
        # Get adaptations that reference this template
        adaptations = self.storage.get_objects_by_reference(template_id)
        
        # Filter by site_id and project_id
        for adaptation in adaptations:
            if (site_id and adaptation["metadata"].get("site_id") == site_id) or \
               (project_id and adaptation["metadata"].get("project_id") == project_id):
                # Convert to template format
                return {
                    "id": adaptation["id"],
                    "name": adaptation["title"],
                    "template_text": adaptation["content"].get("template_text", ""),
                    "variables": adaptation["content"].get("variables", {}),
                    "model": adaptation["content"].get("model", "gpt-4-turbo"),
                    "temperature": adaptation["content"].get("temperature", 0.7),
                    "original_template_id": adaptation["content"].get("original_template_id"),
                    "site_id": adaptation["metadata"].get("site_id"),
                    "project_id": adaptation["metadata"].get("project_id"),
                    "created_at": adaptation["created_at"],
                    "updated_at": adaptation["updated_at"]
                }
        
        return None