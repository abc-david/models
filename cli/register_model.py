#!/usr/bin/env python
"""
CLI script for registering a model definition in the database.

This script provides a command-line interface for registering model
definitions in the public.object_models table.

Usage:
    python -m services.models.cli.register_model --file <model_file.json> --type alpha
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# Add the parent directory to the Python path to allow importing project modules
parent_dir = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(parent_dir))

from services.models.registrar import ModelRegistrar

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def register_model_from_file(file_path, model_type, version):
    """
    Register a model from a JSON file.
    
    Args:
        file_path: Path to the JSON file containing the model definition
        model_type: Type of model (alpha, beta, gamma, qualifier, organizer)
        version: Model version
        
    Returns:
        ID of the registered model
    """
    try:
        # Read the JSON file
        with open(file_path, 'r') as f:
            definition = json.load(f)
        
        # Extract the name and description from the definition
        name = definition.get('name')
        if not name:
            raise ValueError("Model definition must contain a 'name' field")
        
        description = definition.get('description', f"{name} model definition")
        
        # Create a model registrar and register the model
        registrar = ModelRegistrar()
        model_id = await registrar.register_model(
            name=name,
            definition=definition,
            description=description,
            model_type=model_type,
            version=version
        )
        
        logger.info(f"Successfully registered model '{name}' with ID: {model_id}")
        return model_id
        
    except Exception as e:
        logger.error(f"Error registering model: {e}")
        raise


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Register a model definition in the database')
    
    parser.add_argument(
        '--file',
        type=str,
        required=True,
        help='Path to the JSON file containing the model definition'
    )
    
    parser.add_argument(
        '--type',
        type=str,
        choices=['alpha', 'beta', 'gamma', 'qualifier', 'organizer', 'prompt_template', 'prompt_chain'],
        default='alpha',
        help='Type of the model'
    )
    
    parser.add_argument(
        '--version',
        type=str,
        default='1.0',
        help='Version of the model'
    )
    
    return parser.parse_args()


async def main():
    """Main entry point for the script."""
    args = parse_arguments()
    
    try:
        # Check if the file exists
        if not os.path.isfile(args.file):
            logger.error(f"File '{args.file}' does not exist")
            sys.exit(1)
        
        # Register the model
        await register_model_from_file(args.file, args.type, args.version)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main()) 