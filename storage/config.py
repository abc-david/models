"""
MODULE: services/models/storage/config.py
PURPOSE: Tortoise ORM configuration
"""

from typing import Dict, Any
from config.settings import DB_CONFIG

# Prepare credentials dictionary for Tortoise ORM
credentials = {
    "host": DB_CONFIG["host"],
    "port": str(DB_CONFIG["port"]),
    "user": DB_CONFIG["user"],
    "database": DB_CONFIG["database"],
    "minsize": 1,
    "maxsize": 50
}

# Add password only if it exists in DB_CONFIG
if "password" in DB_CONFIG:
    credentials["password"] = DB_CONFIG["password"]

TORTOISE_ORM: Dict[str, Any] = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.asyncpg",
            "credentials": credentials
        }
    },
    "apps": {
        "models": {
            "models": [
                "services.models.storage.project",
                "services.models.storage.context",
                "aerich.models"
            ],
            "default_connection": "default"
        }
    }
} 