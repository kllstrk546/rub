from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import text

from src.config import get_settings
from src.models import Base


settings = get_settings()

engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True,
)

async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _ensure_rate_snapshot_columns(conn)
        await _sync_settings_defaults(conn)


async def dispose_db() -> None:
    await engine.dispose()


async def get_session() -> AsyncIterator[AsyncSession]:
    async with async_session_maker() as session:
        yield session


async def _ensure_rate_snapshot_columns(conn) -> None:
    result = await conn.execute(text("PRAGMA table_info(rate_snapshots)"))
    existing_columns = {row[1] for row in result.fetchall()}
    migrations = {
        "nobitex_message_date": "ALTER TABLE rate_snapshots ADD COLUMN nobitex_message_date DATETIME",
        "rapira_message_date": "ALTER TABLE rate_snapshots ADD COLUMN rapira_message_date DATETIME",
        "refresh_reason": (
            "ALTER TABLE rate_snapshots "
            "ADD COLUMN refresh_reason VARCHAR(64) NOT NULL DEFAULT 'startup'"
        ),
        "bitcoin_usd": "ALTER TABLE rate_snapshots ADD COLUMN bitcoin_usd INTEGER",
        "gold_ounce_usd": "ALTER TABLE rate_snapshots ADD COLUMN gold_ounce_usd INTEGER",
        "oil_usd": "ALTER TABLE rate_snapshots ADD COLUMN oil_usd NUMERIC(18, 6)",
    }

    for column_name, sql in migrations.items():
        if column_name not in existing_columns:
            await conn.execute(text(sql))


async def _sync_settings_defaults(conn) -> None:
    await conn.execute(
        text(
            "INSERT OR REPLACE INTO settings(key, value) "
            "VALUES ('margin_percent', :value)"
        ),
        {"value": str(settings.rate_margin_percent)},
    )
