"""
File: services/models/migration.py
MODULE: Models Migration
PURPOSE: Helps migrate from legacy validation to new models service
DEPENDENCIES:
    - Database for schema updates

This module provides utilities for migrating from the legacy validation
systems to the new centralized models service. It includes functions for
migrating model definitions from the old format to the new format.
"""

import json
import logging
from typing import Dict, List, Any, Optional

from services.database.db_operator import DBOperator

logger = logging.getLogger(__name__)


async def create_models_schema(db_operator: DBOperator) -> None:
    """
    Create the models schema and tables if they don't exist.
    
    Args:
        db_operator: Database operator instance
    """
    # Create schema
    try:
        await db_operator.execute_async(
            "CREATE SCHEMA IF NOT EXISTS models"
        )
        
        # Create model_definitions table
        await db_operator.execute_async(
            """
            CREATE TABLE IF NOT EXISTS models.model_definitions (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE,
                model_type VARCHAR(50) NOT NULL,
                definition JSONB NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
            """
        )
        
        # Create indexes
        await db_operator.execute_async(
            """
            CREATE INDEX IF NOT EXISTS model_definitions_name_idx 
            ON models.model_definitions(name)
            """
        )
        
        await db_operator.execute_async(
            """
            CREATE INDEX IF NOT EXISTS model_definitions_type_idx 
            ON models.model_definitions(model_type)
            """
        )
        
        logger.info("Created models schema and tables")
        
    except Exception as e:
        logger.error(f"Error creating models schema: {str(e)}")
        raise


async def migrate_llm_object_models(db_operator: DBOperator) -> None:
    """
    Migrate object models from LLM service to new models service.
    
    Args:
        db_operator: Database operator instance
    """
    try:
        # Get all object models from LLM service
        object_models = await db_operator.execute_async(
            """
            SELECT name, definition FROM llm.object_models
            """
        )
        
        if not object_models:
            logger.info("No LLM object models to migrate")
            return
        
        # Migrate each model
        for row in object_models:
            name, definition = row
            
            if isinstance(definition, str):
                definition = json.loads(definition)
            
            # Convert to new format if needed
            model_def = {
                "model_name": name,
                "model_type": "content",
                "fields": definition.get("fields", {}),
                "validators": definition.get("validators", [])
            }
            
            # Insert into new table
            await db_operator.execute_async(
                """
                INSERT INTO models.model_definitions (name, model_type, definition)
                VALUES (%s, %s, %s)
                ON CONFLICT (name) DO UPDATE SET 
                    definition = EXCLUDED.definition,
                    updated_at = NOW()
                """,
                (name, "content", json.dumps(model_def))
            )
            
            logger.info(f"Migrated LLM object model: {name}")
            
        logger.info(f"Migrated {len(object_models)} LLM object models")
        
    except Exception as e:
        logger.error(f"Error migrating LLM object models: {str(e)}")
        raise


async def migrate_database_object_models(db_operator: DBOperator) -> None:
    """
    Migrate object models from database service to new models service.
    
    Args:
        db_operator: Database operator instance
    """
    try:
        # Get all object models from database service
        schemas = await db_operator.execute_async(
            """
            SELECT schema_name FROM information_schema.schemata
            WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast', 'models', 'llm')
            """
        )
        
        total_migrated = 0
        
        # For each schema, check for object_models table
        for schema_row in schemas:
            schema_name = schema_row[0]
            
            # Check if object_models table exists in this schema
            table_exists = await db_operator.execute_async(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = %s AND table_name = 'object_models'
                )
                """,
                (schema_name,)
            )
            
            if not table_exists or not table_exists[0][0]:
                continue
            
            # Get models from this schema
            object_models = await db_operator.execute_async(
                f"""
                SELECT name, definition FROM {schema_name}.object_models
                """
            )
            
            if not object_models:
                continue
            
            # Migrate each model
            for row in object_models:
                name, definition = row
                
                if isinstance(definition, str):
                    definition = json.loads(definition)
                
                # Convert JSON Schema format to our internal format
                fields = {}
                for prop_name, prop_def in definition.get("properties", {}).items():
                    field_type = _json_schema_type_to_model_type(prop_def)
                    is_required = prop_name in definition.get("required", [])
                    
                    fields[prop_name] = {
                        "name": prop_name,
                        "type": field_type,
                        "required": is_required,
                        "args": {
                            "default": prop_def.get("default"),
                            "description": prop_def.get("description", "")
                        }
                    }
                
                # Create model definition
                model_def = {
                    "model_name": name,
                    "model_type": "content",
                    "fields": fields,
                    "validators": []
                }
                
                # Insert into new table
                await db_operator.execute_async(
                    """
                    INSERT INTO models.model_definitions (name, model_type, definition)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (name) DO UPDATE SET 
                        definition = EXCLUDED.definition,
                        updated_at = NOW()
                    """,
                    (f"{schema_name}_{name}", "content", json.dumps(model_def))
                )
                
                logger.info(f"Migrated database object model: {schema_name}.{name}")
                total_migrated += 1
            
        logger.info(f"Migrated {total_migrated} database object models")
        
    except Exception as e:
        logger.error(f"Error migrating database object models: {str(e)}")
        raise


def _json_schema_type_to_model_type(property_def: Dict[str, Any]) -> str:
    """
    Convert a JSON Schema type to our internal model type.
    
    Args:
        property_def: JSON Schema property definition
        
    Returns:
        Model type string
    """
    json_type = property_def.get("type")
    format_type = property_def.get("format")
    
    # Handle string types
    if json_type == "string":
        if format_type == "date-time":
            return "datetime"
        return "str"
    
    # Handle number types
    elif json_type == "number":
        return "float"
    elif json_type == "integer":
        return "int"
    
    # Handle boolean
    elif json_type == "boolean":
        return "bool"
    
    # Handle null
    elif json_type == "null":
        return "None"
    
    # Handle arrays
    elif json_type == "array":
        items = property_def.get("items", {})
        if items:
            item_type = _json_schema_type_to_model_type(items)
            return f"List[{item_type}]"
        return "List[Any]"
    
    # Handle objects
    elif json_type == "object":
        return "Dict[str, Any]"
    
    # Default
    return "Any"


async def run_migration() -> None:
    """Run the full migration process."""
    db_operator = DBOperator()
    
    try:
        # Create models schema and tables
        await create_models_schema(db_operator)
        
        # Migrate LLM object models
        await migrate_llm_object_models(db_operator)
        
        # Migrate database object models
        await migrate_database_object_models(db_operator)
        
        logger.info("Migration completed successfully")
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        raise


if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_migration()) 