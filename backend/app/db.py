import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker


def normalize_db_url(url: str) -> str:
    """Neon/Supabase отдают 'postgres://' — async SQLAlchemy требует '+asyncpg'."""
    if url.startswith(("postgres://", "postgresql://")):
        return "postgresql+asyncpg://" + url.split("://", 1)[1]
    return url


# Use DATABASE_URL env var when provided; fallback to a local SQLite DB for
# easy local startup without Postgres.
DATABASE_URL = normalize_db_url(os.getenv("DATABASE_URL") or "sqlite+aiosqlite:///./dev.db")
_engine_kwargs = {}
if DATABASE_URL.startswith("postgres"):
    # Small pool: Neon/Supabase free tier ограничивает число подключений.
    _engine_kwargs = {"pool_size": 5, "max_overflow": 5}
engine = create_async_engine(DATABASE_URL, future=True, echo=False, **_engine_kwargs)
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)


async def init_db():
    # Create tables from models (used for quick local setup). For production use Alembic.
    import app.models as models
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    # SQLite's create_all cannot add columns to existing tables. Apply lightweight
    # ALTER TABLE for any columns missing from the pre-existing `orders` table.
    if DATABASE_URL.startswith("sqlite"):
        missing_orders_cols = [c for c in (
            ("notes", "TEXT"),
            ("table_id", "INTEGER"),
            ("user_id", "INTEGER"),
            ("shift_id", "INTEGER"),
            ("payment_method", "VARCHAR"),
            ("paid_at", "DATETIME"),
            ("closed_at", "DATETIME"),
        ) if not _column_exists("orders", c[0])]
        for col_name, col_type in missing_orders_cols:
            async with engine.begin() as conn:
                await conn.execute(text(f'ALTER TABLE orders ADD COLUMN {col_name} {col_type}'))


def _column_exists(table: str, column: str) -> bool:
    import sqlite3
    conn = sqlite3.connect("dev.db")
    try:
        cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
        return column in cols
    finally:
        conn.close()


async def get_session():
    async with AsyncSessionLocal() as session:
        yield session
