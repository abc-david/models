#!/usr/bin/env python
"""
Example script to demonstrate retrieving a model from the database.

This script retrieves the prompt template model from the database and prints its details.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add the parent directory to the Python path to allow importing project modules
parent_dir = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(parent_dir))

from services.models.utils.model_registrar import ModelRegistrar

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def retrieve_model(model_name):
    """
    Retrieve a model from the database.
    
    Args:
        model_name: Name of the model to retrieve
    """
    try:
        # Create a model registrar
        registrar = ModelRegistrar()
        
        # Retrieve the model
        model = await registrar.get_model_definition(model_name)
        
        if model:
            logger.info(f"Retrieved model '{model_name}' with ID: {model['id']}")
            logger.info(f"Model type: {model['object_type']}")
            logger.info(f"Model version: {model['version']}")
            logger.info(f"Description: {model['description']}")
            logger.info("Model definition:")
            logger.info(json.dumps(model['definition'], indent=2))
            return model
        else:
            logger.error(f"Model '{model_name}' not found")
            return None
    except Exception as e:
        logger.error(f"Error retrieving model: {e}")
        raise


async def main():
    """Main entry point for the script."""
    model_name = "PromptTemplate"
    logger.info(f"Retrieving model '{model_name}'...")
    model = await retrieve_model(model_name)
    
    if model:
        # Example of how to use the model definition
        fields = model['definition'].get('fields', {})
        logger.info(f"Model has {len(fields)} fields:")
        for field_name, field_def in fields.items():
            logger.info(f"  - {field_name}: {field_def['type']}")
        
        validators = model['definition'].get('validators', [])
        logger.info(f"Model has {len(validators)} validators:")
        for validator in validators:
            logger.info(f"  - {validator['name']} (fields: {', '.join(validator['fields'])})")


if __name__ == '__main__':
    asyncio.run(main()) 