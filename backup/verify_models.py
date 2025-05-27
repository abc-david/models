#!/usr/bin/env python
"""
MODULE: services/models/utils/verify_models.py
PURPOSE: Utility to verify model schemas against database schemas
DEPENDENCIES:
    - services.models: For model access
    - asyncio: For async runtime

This utility script provides a command-line interface for verifying model schemas
against database schemas, identifying missing tables and columns, and generating
SQL statements to create missing tables.
"""

import asyncio
import json
import argparse
import sys
import logging
from typing import Dict, List, Any, Optional

from services.models import orchestrator, SchemaInspector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def verify_model(model_name: str, schema: str) -> None:
    """
    Verify a single model against a database schema.
    
    Args:
        model_name: Name of the model to verify
        schema: Database schema to verify against
    """
    inspector = SchemaInspector()
    try:
        result = await inspector.verify_model_schema(schema, model_name)
        
        if result.get("error"):
            print(f"Error: {result['error']}")
            return
            
        if result["is_valid"]:
            print(f"✅ Model '{model_name}' is valid against schema '{schema}.{result['table_name']}'")
        else:
            print(f"❌ Model '{model_name}' has issues against schema '{schema}.{result['table_name']}':")
            
            if result["missing_columns"]:
                print(f"  Missing columns: {', '.join(result['missing_columns'])}")
                
            if result["type_mismatches"]:
                print("  Type mismatches:")
                for mismatch in result["type_mismatches"]:
                    print(f"    {mismatch['field']}: Expected {mismatch['expected_type']}, got {mismatch['actual_type']}")
    finally:
        await inspector.close()


async def verify_all_models(schema: str, prefix: Optional[str] = None) -> None:
    """
    Verify all models against a database schema.
    
    Args:
        schema: Database schema to verify against
        prefix: Optional prefix to filter model names
    """
    inspector = SchemaInspector()
    try:
        results = await inspector.verify_all_models(schema, prefix)
        
        valid_count = 0
        invalid_count = 0
        error_count = 0
        
        print(f"Verifying models against schema '{schema}':")
        
        for model_name, result in results.items():
            if result.get("error"):
                print(f"❗ Error for model '{model_name}': {result['error']}")
                error_count += 1
                continue
                
            if result["is_valid"]:
                print(f"✅ Model '{model_name}' is valid")
                valid_count += 1
            else:
                print(f"❌ Model '{model_name}' has issues:")
                
                if result["missing_columns"]:
                    print(f"  Missing columns: {', '.join(result['missing_columns'])}")
                    
                if result["type_mismatches"]:
                    print("  Type mismatches:")
                    for mismatch in result["type_mismatches"]:
                        print(f"    {mismatch['field']}: Expected {mismatch['expected_type']}, got {mismatch['actual_type']}")
                
                invalid_count += 1
        
        print(f"\nVerification results: {valid_count} valid, {invalid_count} invalid, {error_count} errors")
    finally:
        await inspector.close()


async def list_models() -> None:
    """
    List all available models.
    """
    models = await orchestrator.list_models()
    if not models:
        print("No models registered.")
        return
        
    print(f"Available models ({len(models)}):")
    for model in sorted(models):
        print(f"  - {model}")


async def generate_sql(model_name: str) -> None:
    """
    Generate SQL statements to create a table for a model.
    
    Args:
        model_name: Name of the model
    """
    inspector = SchemaInspector()
    try:
        result = await inspector.generate_schema_sql(model_name)
        
        if result.get("error"):
            print(f"Error: {result['error']}")
            return
            
        print(f"SQL for model '{model_name}' (table: {result['table_name']}):")
        print(result["create_table_sql"].replace("{schema}", "public"))
    finally:
        await inspector.close()


async def find_missing_tables(schema: str) -> None:
    """
    Find tables that are defined in models but missing from the database.
    
    Args:
        schema: Database schema to check
    """
    inspector = SchemaInspector()
    try:
        result = await inspector.get_missing_tables(schema)
        
        if result.get("error"):
            print(f"Error: {result['error']}")
            return
            
        missing_tables = result["missing_tables"]
        
        if not missing_tables:
            print(f"No missing tables in schema '{schema}'.")
            return
            
        print(f"Missing tables in schema '{schema}':")
        for table_name, model_name in missing_tables.items():
            print(f"  - {table_name} (model: {model_name})")
            
        # Generate SQL for missing tables
        for table_name, model_name in missing_tables.items():
            sql_result = await inspector.generate_schema_sql(model_name)
            if not sql_result.get("error"):
                print(f"\nSQL for {table_name}:")
                print(sql_result["create_table_sql"].replace("{schema}", schema))
    finally:
        await inspector.close()


async def main() -> None:
    """
    Parse command-line arguments and run the appropriate function.
    """
    parser = argparse.ArgumentParser(description="Model Schema Verification Utility")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify a model schema")
    verify_parser.add_argument("--model", "-m", help="Model name to verify")
    verify_parser.add_argument("--schema", "-s", default="public", help="Database schema to verify against")
    verify_parser.add_argument("--prefix", "-p", help="Filter models by prefix")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List available models")
    
    # SQL command
    sql_parser = subparsers.add_parser("sql", help="Generate SQL for a model")
    sql_parser.add_argument("--model", "-m", required=True, help="Model name")
    
    # Missing command
    missing_parser = subparsers.add_parser("missing", help="Find missing tables")
    missing_parser.add_argument("--schema", "-s", default="public", help="Database schema to check")
    
    args = parser.parse_args()
    
    if args.command == "verify":
        if args.model:
            await verify_model(args.model, args.schema)
        else:
            await verify_all_models(args.schema, args.prefix)
    elif args.command == "list":
        await list_models()
    elif args.command == "sql":
        await generate_sql(args.model)
    elif args.command == "missing":
        await find_missing_tables(args.schema)
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main()) 