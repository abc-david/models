#!/usr/bin/env python
"""
MODULE: services/models/utils/model_db_integration.py
PURPOSE: Utility demonstrating integration between models and database services
DEPENDENCIES:
    - services.models.orchestrator: Model management
    - services.database.db_operator: Database operations
    - asyncio: For async runtime

This utility script provides examples of common operations that integrate
model validation and database operations, showing how to effectively use
both services together.
"""

import asyncio
import logging
import argparse
import json
from typing import Any, Dict, List, Optional, Union

from services.models import orchestrator
from services.models.db_schema_inspector import SchemaInspector
from services.database.db_operator import DBOperator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def validate_and_insert(
    model_name: str, 
    data: Dict[str, Any], 
    schema: str = "public"
) -> Dict[str, Any]:
    """
    Validate data against a model and insert it into the database.
    
    Args:
        model_name: Name of the model to validate against
        data: Data to validate and insert
        schema: Database schema to use
        
    Returns:
        Dict containing the result of the operation
    """
    # Step 1: Validate the data against the model
    validation_result = await orchestrator.validate_data(model_name, data)
    
    if not validation_result.is_valid:
        return {
            "success": False,
            "errors": validation_result.errors,
            "message": "Data validation failed"
        }
    
    # Step 2: Get the table name for the model
    model = await orchestrator.get_model(model_name)
    if not model:
        return {
            "success": False,
            "message": f"Model '{model_name}' not found"
        }
    
    table_name = model.get_table_name()
    
    # Step 3: Insert data into the database
    db = DBOperator()
    try:
        # Clean data for database insertion (remove any fields not in the model)
        clean_data = validation_result.valid_data
        
        query = f"""
        INSERT INTO {schema}.{table_name} 
        ({', '.join(clean_data.keys())})
        VALUES ({', '.join(['$' + str(i+1) for i in range(len(clean_data))])})
        RETURNING id
        """
        
        result = await db.execute(
            query, 
            values=list(clean_data.values()),
            return_rows=True
        )
        
        if result and len(result) > 0:
            return {
                "success": True,
                "id": result[0]["id"],
                "message": f"Data inserted successfully into {schema}.{table_name}"
            }
        else:
            return {
                "success": False,
                "message": "Insert operation did not return an ID"
            }
    except Exception as e:
        logger.exception(f"Database error during insertion: {str(e)}")
        return {
            "success": False,
            "message": f"Database error: {str(e)}"
        }
    finally:
        await db.close()


async def fetch_and_validate(
    model_name: str, 
    record_id: int, 
    schema: str = "public"
) -> Dict[str, Any]:
    """
    Fetch data from the database and validate it against a model.
    
    Args:
        model_name: Name of the model to validate against
        record_id: ID of the record to fetch
        schema: Database schema to use
        
    Returns:
        Dict containing the result of the operation
    """
    # Step 1: Get the table name for the model
    model = await orchestrator.get_model(model_name)
    if not model:
        return {
            "success": False,
            "message": f"Model '{model_name}' not found"
        }
    
    table_name = model.get_table_name()
    
    # Step 2: Fetch data from the database
    db = DBOperator()
    try:
        query = f"SELECT * FROM {schema}.{table_name} WHERE id = $1"
        result = await db.execute(query, values=[record_id], return_rows=True)
        
        if not result or len(result) == 0:
            return {
                "success": False,
                "message": f"Record with ID {record_id} not found in {schema}.{table_name}"
            }
        
        data = result[0]
        
        # Step 3: Validate the fetched data against the model
        validation_result = await orchestrator.validate_data(model_name, data)
        
        if validation_result.is_valid:
            return {
                "success": True,
                "data": validation_result.valid_data,
                "message": "Data fetched and validated successfully"
            }
        else:
            return {
                "success": False,
                "data": data,
                "errors": validation_result.errors,
                "message": "Fetched data failed validation"
            }
    except Exception as e:
        logger.exception(f"Error during fetch and validate: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }
    finally:
        await db.close()


async def verify_and_repair_schema(
    model_name: str, 
    schema: str = "public",
    auto_repair: bool = False
) -> Dict[str, Any]:
    """
    Verify a model's schema against the database and optionally repair it.
    
    Args:
        model_name: Name of the model to verify
        schema: Database schema to use
        auto_repair: Whether to automatically repair the schema
        
    Returns:
        Dict containing the result of the operation
    """
    inspector = SchemaInspector()
    try:
        # Step 1: Verify the model's schema
        result = await inspector.verify_model_schema(schema, model_name)
        
        if result.get("error"):
            return {
                "success": False,
                "message": result["error"]
            }
            
        if result["is_valid"]:
            return {
                "success": True,
                "message": f"Model '{model_name}' schema is valid"
            }
        
        # Step 2: If auto_repair is True and the schema is invalid, repair it
        if auto_repair:
            if result["table_exists"]:
                # If the table exists but has missing columns, add them
                if result["missing_columns"]:
                    db = DBOperator()
                    try:
                        model = await orchestrator.get_model(model_name)
                        if not model:
                            return {
                                "success": False,
                                "message": f"Model '{model_name}' not found"
                            }
                        
                        # Generate ALTER TABLE statements for missing columns
                        alter_statements = []
                        for column in result["missing_columns"]:
                            column_def = model.get_field_db_definition(column)
                            if column_def:
                                alter_statements.append(
                                    f"ALTER TABLE {schema}.{result['table_name']} "
                                    f"ADD COLUMN {column} {column_def['type']}"
                                )
                        
                        # Execute ALTER TABLE statements
                        for statement in alter_statements:
                            await db.execute(statement)
                            
                        return {
                            "success": True,
                            "message": f"Added missing columns to {schema}.{result['table_name']}",
                            "columns_added": result["missing_columns"]
                        }
                    except Exception as e:
                        logger.exception(f"Error during schema repair: {str(e)}")
                        return {
                            "success": False,
                            "message": f"Error during schema repair: {str(e)}"
                        }
                    finally:
                        await db.close()
            else:
                # If the table doesn't exist, create it
                sql_result = await inspector.generate_schema_sql(model_name)
                if sql_result.get("error"):
                    return {
                        "success": False,
                        "message": sql_result["error"]
                    }
                
                db = DBOperator()
                try:
                    create_statement = sql_result["create_table_sql"].replace("{schema}", schema)
                    await db.execute(create_statement)
                    
                    return {
                        "success": True,
                        "message": f"Created table {schema}.{sql_result['table_name']}",
                        "sql": create_statement
                    }
                except Exception as e:
                    logger.exception(f"Error during table creation: {str(e)}")
                    return {
                        "success": False,
                        "message": f"Error during table creation: {str(e)}"
                    }
                finally:
                    await db.close()
        
        # If auto_repair is False, just return the verification result
        return {
            "success": False,
            "issues": {
                "missing_columns": result["missing_columns"],
                "type_mismatches": result["type_mismatches"]
            },
            "message": f"Model '{model_name}' schema is invalid"
        }
    finally:
        await inspector.close()


async def main() -> None:
    """Main function to parse arguments and run commands."""
    parser = argparse.ArgumentParser(description="Model-Database Integration Utility")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Insert command
    insert_parser = subparsers.add_parser("insert", help="Validate and insert data")
    insert_parser.add_argument("--model", "-m", required=True, help="Model name")
    insert_parser.add_argument("--data", "-d", required=True, help="JSON data to insert")
    insert_parser.add_argument("--schema", "-s", default="public", help="Database schema")
    
    # Fetch command
    fetch_parser = subparsers.add_parser("fetch", help="Fetch and validate data")
    fetch_parser.add_argument("--model", "-m", required=True, help="Model name")
    fetch_parser.add_argument("--id", "-i", type=int, required=True, help="Record ID")
    fetch_parser.add_argument("--schema", "-s", default="public", help="Database schema")
    
    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify and repair schema")
    verify_parser.add_argument("--model", "-m", required=True, help="Model name")
    verify_parser.add_argument("--schema", "-s", default="public", help="Database schema")
    verify_parser.add_argument("--repair", "-r", action="store_true", help="Auto-repair schema")
    
    args = parser.parse_args()
    
    if args.command == "insert":
        try:
            data = json.loads(args.data)
            result = await validate_and_insert(args.model, data, args.schema)
            print(json.dumps(result, indent=2))
        except json.JSONDecodeError:
            print({"success": False, "message": "Invalid JSON data"})
    
    elif args.command == "fetch":
        result = await fetch_and_validate(args.model, args.id, args.schema)
        print(json.dumps(result, indent=2))
    
    elif args.command == "verify":
        result = await verify_and_repair_schema(args.model, args.schema, args.repair)
        print(json.dumps(result, indent=2))
    
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main()) 