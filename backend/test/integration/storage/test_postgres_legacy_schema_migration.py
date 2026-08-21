"""0.6.x 企业 schema 在真实 PostgreSQL 上的升级测试。"""

from __future__ import annotations

import os
import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine

from yuxi.storage.postgres.manager import PostgresManager

pytestmark = [pytest.mark.asyncio, pytest.mark.integration]


def _scoped_manager(engine) -> PostgresManager:
    """创建不触碰进程单例的隔离 schema manager。"""
    manager = object.__new__(PostgresManager)
    PostgresManager.__init__(manager)
    manager.async_engine = engine
    manager._initialized = True
    return manager


async def test_enterprise_06_schema_upgrade_is_idempotent_and_preserves_data() -> None:
    """旧企业表升级两次后应保留标识、模型配置并生成新版约束。"""
    database_name = f"pytest_enterprise_migration_{uuid.uuid4().hex[:16]}"
    source_url = make_url(os.environ["POSTGRES_URL"])
    admin_engine = create_async_engine(source_url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    legacy_engine = None

    try:
        async with admin_engine.connect() as connection:
            await connection.execute(text(f'CREATE DATABASE "{database_name}"'))

        legacy_engine = create_async_engine(source_url.set(database=database_name), pool_pre_ping=True)
        async with legacy_engine.begin() as connection:
            statements = [
                "CREATE TABLE users (id SERIAL PRIMARY KEY, user_id VARCHAR(64) NOT NULL)",
                ("CREATE TABLE knowledge_bases (db_id VARCHAR(64) PRIMARY KEY, embed_info JSONB, llm_info JSONB)"),
                "CREATE TABLE knowledge_files (id SERIAL PRIMARY KEY, db_id VARCHAR(64))",
                "CREATE TABLE message_feedbacks (id SERIAL PRIMARY KEY, user_id VARCHAR(64))",
                ("CREATE TABLE conversations (id SERIAL PRIMARY KEY, user_id VARCHAR(64), agent_id VARCHAR(128))"),
                "CREATE TABLE agent_runs (id VARCHAR(64) PRIMARY KEY, user_id VARCHAR(64))",
                "CREATE TABLE messages (id SERIAL PRIMARY KEY)",
                "CREATE TABLE skills (id SERIAL PRIMARY KEY, is_builtin BOOLEAN)",
                "CREATE TABLE mcp_servers (name VARCHAR(100) PRIMARY KEY)",
                "INSERT INTO users (user_id) VALUES ('legacy-user')",
                (
                    "INSERT INTO knowledge_bases (db_id, embed_info, llm_info) VALUES ("
                    "'legacy-kb', '{\"model_id\": \"legacy-embed\"}'::jsonb, "
                    '\'{"model_id": "legacy-llm"}\'::jsonb)'
                ),
                ("INSERT INTO conversations (user_id, agent_id) VALUES ('legacy-user', 'ChatbotAgent')"),
                "INSERT INTO mcp_servers (name) VALUES ('legacy-mcp')",
            ]
            for statement in statements:
                await connection.execute(text(statement))

        manager = _scoped_manager(legacy_engine)
        await manager.ensure_legacy_schema()
        await manager.ensure_legacy_schema()

        async with legacy_engine.connect() as connection:
            renamed_columns = {
                (row.table_name, row.column_name)
                for row in (
                    await connection.execute(
                        text(
                            """
                            SELECT table_name, column_name
                            FROM information_schema.columns
                            WHERE table_schema = 'public'
                              AND table_name IN (
                                  'users', 'knowledge_bases', 'knowledge_files',
                                  'message_feedbacks', 'conversations', 'agent_runs'
                              )
                            """
                        )
                    )
                )
            }
            knowledge_base = (
                await connection.execute(
                    text(
                        """
                        SELECT kb_id, embedding_model_spec, llm_model_spec
                        FROM knowledge_bases
                        WHERE kb_id = 'legacy-kb'
                        """
                    )
                )
            ).one()
            conversation = (
                await connection.execute(text("SELECT uid, agent_id FROM conversations WHERE id = 1"))
            ).one()
            mcp_server = (
                await connection.execute(text("SELECT id, slug FROM mcp_servers WHERE name = 'legacy-mcp'"))
            ).one()
            mcp_primary_key = await connection.scalar(
                text(
                    """
                    SELECT pg_get_constraintdef(oid)
                    FROM pg_constraint
                    WHERE conrelid = 'public.mcp_servers'::regclass AND contype = 'p'
                    """
                )
            )
            skill_columns = {
                row.column_name
                for row in (
                    await connection.execute(
                        text(
                            """
                            SELECT column_name
                            FROM information_schema.columns
                            WHERE table_schema = 'public' AND table_name = 'skills'
                            """
                        )
                    )
                )
            }
            indexes = {
                row.indexname
                for row in (
                    await connection.execute(
                        text(
                            """
                            SELECT indexname
                            FROM pg_indexes
                            WHERE schemaname = 'public'
                              AND tablename IN ('users', 'mcp_servers')
                            """
                        )
                    )
                )
            }

        assert {
            ("users", "uid"),
            ("knowledge_bases", "kb_id"),
            ("knowledge_files", "kb_id"),
            ("message_feedbacks", "uid"),
            ("conversations", "uid"),
            ("agent_runs", "uid"),
        }.issubset(renamed_columns)
        assert tuple(knowledge_base) == ("legacy-kb", "legacy-embed", "legacy-llm")
        assert tuple(conversation) == ("legacy-user", "default-chatbot")
        assert mcp_server.id is not None
        assert mcp_server.slug == "legacy-mcp"
        assert mcp_primary_key == "PRIMARY KEY (id)"
        assert "is_builtin" not in skill_columns
        assert {"ix_users_uid", "ix_mcp_servers_slug"}.issubset(indexes)
    finally:
        if legacy_engine is not None:
            await legacy_engine.dispose()
        async with admin_engine.connect() as connection:
            await connection.execute(text(f'DROP DATABASE IF EXISTS "{database_name}" WITH (FORCE)'))
        await admin_engine.dispose()
