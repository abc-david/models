"""
MODULE: services/models/db_schema_inspector.py
PURPOSE: Inspect and verify database schemas against model definitions
DEPENDENCIES:
    - services.database: For database connectivity
    - services.models.core.model_registry: For model schema access

This module provides utilities for inspecting database schemas, verifying them
against model definitions, and diagnosing schema-related issues. It helps ensure
that database schemas are compatible with the models defined in the application.
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Set, Tuple

import config.settings
from services.database import DBConnector, SchemaSetup
from services.models.core.model_registry import ModelRegistry

logger = logging.getLogger(__name__)


class SchemaInspector:
    """
    Utility class for inspecting database schemas and verifying model compatibility.
    
    This class provides methods to:
    1. Inspect schema structures
    2. Verify database schemas against model definitions
    3. Diagnose schema issues
    4. Support test environment setup
    """
    
    def __init__(self, test_mode: Optional[str] = None):
        """
        Initialize the schema inspector.
        
        Args:
            test_mode: Test mode to use ('mock', 'e2e', or None for production)
        """
        # Store the previous test mode so we can restore it later
        self._previous_test_mode = config.settings.TEST_MODE
        
        # Set the test mode in the global settings if specified
        if test_mode:
            config.settings.TEST_MODE = test_mode
            
        self.test_mode = test_mode
        self.db = DBConnector()
        self.setup = SchemaSetup()
    
    async def close(self) -> None:
        """Close database connections and restore original test mode."""
        await self.db.close()
        await self.setup.close()
        
        # Restore the original test mode
        config.settings.TEST_MODE = self._previous_test_mode
        
    async def inspect_schema(self, schema_name: str) -> Dict[str, Any]:
        """
        Inspect a database schema and its tables.
        
        Args:
            schema_name: The schema to inspect
            
        Returns:
            Dict containing schema information and table structures
        """
        # Check if schema exists
        schema_exists = await self.setup._schema_exists(schema_name)
        if not schema_exists:
            logger.warning(f"Schema '{schema_name}' does not exist")
            return {"exists": False}
            
        # Get tables in schema
        tables = await self.setup._get_existing_tables(schema_name)
        logger.debug(f"Found {len(tables)} tables in schema '{schema_name}'")
        
        # Collect detailed information for each table
        tables_info = {}
        for table in tables:
            # Get column information
            columns = await self.db.execute(
                """
                SELECT 
                    column_name, 
                    data_type, 
                    is_nullable, 
                    column_default
                FROM 
                    information_schema.columns 
                WHERE 
                    table_schema = $1 
                    AND table_name = $2
                ORDER BY 
                    ordinal_position
                """,
                [schema_name, table],
                fetch_all=True
            )
            
            # Get primary key information
            primary_keys = await self.db.execute(
                """
                SELECT 
                    kcu.column_name
                FROM 
                    information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                      ON tc.constraint_name = kcu.constraint_name
                      AND tc.table_schema = kcu.table_schema
                WHERE 
                    tc.constraint_type = 'PRIMARY KEY'
                    AND tc.table_schema = $1
                    AND tc.table_name = $2
                """,
                [schema_name, table],
                fetch_all=True
            )
            
            # Get indexes
            indexes = await self.db.execute(
                """
                SELECT
                    indexname,
                    indexdef
                FROM
                    pg_indexes
                WHERE
                    schemaname = $1
                    AND tablename = $2
                """,
                [schema_name, table],
                fetch_all=True
            )
            
            # Store table information
            tables_info[table] = {
                "columns": columns,
                "primary_keys": [pk["column_name"] for pk in primary_keys],
                "indexes": indexes
            }
        
        return {
            "exists": True,
            "name": schema_name,
            "tables": tables,
            "tables_info": tables_info
        }
    
    async def verify_model_schema(self, db_schema: str, model_name: str) -> Dict[str, Any]:
        """
        Verify that a database schema matches a model schema.
        
        Args:
            db_schema: The database schema to verify
            model_name: The model name to verify against
            
        Returns:
            Dict with verification results
        """
        # Get the model schema
        model_schema = await ModelRegistry.get_schema(model_name)
        
        if not model_schema:
            logger.error(f"Model '{model_name}' not found in registry")
            return {"error": f"Model '{model_name}' not found in registry"}
            
        # Get database schema info
        db_info = await self.inspect_schema(db_schema)
        
        if not db_info.get("exists", False):
            logger.error(f"Database schema '{db_schema}' does not exist")
            return {"error": f"Database schema '{db_schema}' does not exist"}
            
        # Determine which table to check
        # By default, use model name (lowercase) as table name unless explicitly specified
        table_name = model_schema.get("table_name", model_name.lower())
        
        if table_name not in db_info["tables"]:
            missing_table_error = f"Table '{table_name}' not found in schema '{db_schema}'"
            logger.error(missing_table_error)
            return {
                "error": missing_table_error,
                "available_tables": db_info["tables"]
            }
            
        # Get table columns
        columns = {}
        for col in db_info["tables_info"][table_name]["columns"]:
            columns[col["column_name"]] = col
            
        # Check if all required fields have corresponding columns
        missing_columns = []
        type_mismatches = []
        
        for field_name, field_def in model_schema.get("fields", {}).items():
            # Skip fields that don't map directly to columns
            if field_def.get("type") in ["Dict", "List", "dict", "list"]:
                continue
                
            # Map model types to PostgreSQL types
            type_mapping = {
                "str": "character varying",
                "string": "character varying",
                "int": "integer",
                "float": "double precision",
                "bool": "boolean",
                "datetime": "timestamp without time zone",
                "date": "date",
                "UUID": "uuid",
                "uuid": "uuid",
                "json": "jsonb"
            }
            
            expected_type = type_mapping.get(field_def.get("type"), "character varying")
            
            # Check if column exists
            if field_name not in columns:
                if field_def.get("required", True):
                    missing_columns.append(field_name)
                continue
                
            # Check column type
            actual_type = columns[field_name]["data_type"]
            if actual_type != expected_type and field_def.get("required", True):
                type_mismatches.append({
                    "field": field_name,
                    "expected_type": expected_type,
                    "actual_type": actual_type
                })
        
        # Generate verification result
        is_valid = not missing_columns and not type_mismatches
        result = {
            "model_name": model_name,
            "db_schema": db_schema,
            "table_name": table_name,
            "is_valid": is_valid,
            "missing_columns": missing_columns,
            "type_mismatches": type_mismatches
        }
        
        # Log verification result
        if is_valid:
            logger.info(f"Model '{model_name}' is valid against schema '{db_schema}.{table_name}'")
        else:
            logger.warning(f"Model '{model_name}' has issues against schema '{db_schema}.{table_name}'")
        
        return result
        
    async def verify_all_models(
        self,
        db_schema: str = "public",
        filter_prefix: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Verify all models against a database schema.
        
        Args:
            db_schema: Database schema to verify against
            filter_prefix: Optional prefix to filter model names
            
        Returns:
            Dict mapping model names to verification results
        """
        models = await ModelRegistry.list_models()
        
        # Apply filter if specified
        if filter_prefix:
            models = [m for m in models if m.startswith(filter_prefix)]
            
        results = {}
        for model_name in models:
            results[model_name] = await self.verify_model_schema(db_schema, model_name)
            
        return results
        
    async def get_missing_tables(self, db_schema: str) -> Dict[str, Any]:
        """
        Identify tables that are defined in models but missing from the database.
        
        Args:
            db_schema: Database schema to check
            
        Returns:
            Dict with missing tables information
        """
        # Get all model schemas
        models = await ModelRegistry.list_models()
        model_tables = {}
        
        for model_name in models:
            model_schema = await ModelRegistry.get_schema(model_name)
            if model_schema:
                table_name = model_schema.get("table_name", model_name.lower())
                model_tables[table_name] = model_name
        
        # Get existing tables
        db_info = await self.inspect_schema(db_schema)
        if not db_info.get("exists", False):
            return {"error": f"Database schema '{db_schema}' does not exist"}
            
        existing_tables = set(db_info["tables"])
        
        # Find missing tables
        missing_tables = {}
        for table_name, model_name in model_tables.items():
            if table_name not in existing_tables:
                missing_tables[table_name] = model_name
                
        return {
            "db_schema": db_schema,
            "missing_tables": missing_tables,
            "existing_tables": list(existing_tables),
            "model_defined_tables": list(model_tables.keys())
        }
        
    async def generate_schema_sql(self, model_name: str) -> Dict[str, Any]:
        """
        Generate SQL statements to create a table for a model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Dict with SQL statements
        """
        # Get model schema
        model_schema = await ModelRegistry.get_schema(model_name)
        if not model_schema:
            return {"error": f"Model '{model_name}' not found in registry"}
            
        # Determine table name
        table_name = model_schema.get("table_name", model_name.lower())
        
        # Generate SQL for creating the table
        field_definitions = []
        primary_key = None
        
        # Map model types to SQL types
        type_mapping = {
            "str": "VARCHAR(255)",
            "string": "VARCHAR(255)",
            "int": "INTEGER",
            "float": "DOUBLE PRECISION",
            "bool": "BOOLEAN",
            "datetime": "TIMESTAMP",
            "date": "DATE",
            "UUID": "UUID",
            "uuid": "UUID",
            "json": "JSONB",
            "dict": "JSONB",
            "list": "JSONB"
        }
        
        for field_name, field_def in model_schema.get("fields", {}).items():
            field_type = field_def.get("type", "str")
            sql_type = type_mapping.get(field_type, "VARCHAR(255)")
            
            # Handle required/nullable
            nullable = "NOT NULL" if field_def.get("required", True) else "NULL"
            
            # Check if this field is a primary key
            is_primary_key = field_def.get("primary_key", False) or field_name == "id"
            if is_primary_key:
                primary_key = field_name
                
            field_definitions.append(f"    {field_name} {sql_type} {nullable}")
            
        # Add primary key if specified
        if primary_key:
            field_definitions.append(f"    PRIMARY KEY ({primary_key})")
            
        # Build the complete SQL statement
        create_table_sql = f"CREATE TABLE {{schema}}.{table_name} (\n"
        create_table_sql += ",\n".join(field_definitions)
        create_table_sql += "\n);"
        
        return {
            "model_name": model_name,
            "table_name": table_name,
            "create_table_sql": create_table_sql
        } 