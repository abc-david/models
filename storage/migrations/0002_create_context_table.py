"""
MODULE: services/models/storage/migrations/0002_create_context_table.py
PURPOSE: Migration to create the contexts table
"""

from tortoise import BaseDBAsyncClient, fields
from tortoise.migration import Migration

class Migration(Migration):
    async def up(self, db: BaseDBAsyncClient) -> str:
        return """
        CREATE TABLE IF NOT EXISTS "contexts" (
            "id" UUID NOT NULL PRIMARY KEY,
            "type" VARCHAR(255) NOT NULL,
            "data" JSONB NOT NULL,
            "project_uuid" UUID,
            "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS "idx_contexts_project_uuid" ON "contexts" ("project_uuid");
        CREATE INDEX IF NOT EXISTS "idx_contexts_type" ON "contexts" ("type");
        """

    async def down(self, db: BaseDBAsyncClient) -> str:
        return """
        DROP TABLE IF EXISTS "contexts";
        """ 