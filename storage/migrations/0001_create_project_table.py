"""
MODULE: services/models/storage/migrations/0001_create_project_table.py
PURPOSE: Migration to create the projects table
"""

from tortoise import BaseDBAsyncClient, fields
from tortoise.migration import Migration

class Migration(Migration):
    async def up(self, db: BaseDBAsyncClient) -> str:
        return """
        CREATE TABLE IF NOT EXISTS "projects" (
            "id" UUID NOT NULL PRIMARY KEY,
            "name" VARCHAR(255) NOT NULL,
            "description" TEXT,
            "metadata" JSONB NOT NULL DEFAULT '{}',
            "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS "idx_projects_name" ON "projects" ("name");
        """

    async def down(self, db: BaseDBAsyncClient) -> str:
        return """
        DROP TABLE IF EXISTS "projects";
        """ 