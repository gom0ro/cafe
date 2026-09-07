from logging.config import fileConfig
import os
import sys
import asyncio
from sqlalchemy import pool
from alembic import context

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

config = context.config
fileConfig(config.config_file_name)

# import your models' MetaData object here for 'autogenerate' support
from app import models
target_metadata = models.Base.metadata


def _async_url(url: str) -> str:
    """Neon/Supabase отдают 'postgres://' — async SQLAlchemy требует '+asyncpg'."""
    if url.startswith(("postgres://", "postgresql://")):
        return "postgresql+asyncpg://" + url.split("://", 1)[1]
    return url


def _resolve_url() -> str:
    return _async_url(os.getenv('DATABASE_URL', config.get_main_option('sqlalchemy.url')))


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_offline():
    context.configure(url=_resolve_url(), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online():
    from sqlalchemy.ext.asyncio import create_async_engine
    connectable = create_async_engine(_resolve_url(), poolclass=pool.NullPool)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())