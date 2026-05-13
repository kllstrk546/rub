import sys
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))


def test_settings_loads_defaults():
    from src.config import get_settings

    settings = get_settings()

    assert settings.app_name == "rub-rate-bot"
    assert settings.database_url.startswith("sqlite+aiosqlite:///")


def test_metadata_contains_required_tables():
    from src.models import Base

    assert {"users", "access_requests", "rate_snapshots", "settings"} <= set(Base.metadata.tables)


@pytest.mark.asyncio
async def test_repositories_smoke_flow():
    from src.models import Base
    from src.repositories.rates import RateRepository
    from src.repositories.requests import AccessRequestRepository
    from src.repositories.users import UserRepository

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_maker() as session:
        users = UserRepository(session)
        requests = AccessRequestRepository(session)
        rates = RateRepository(session)

        user = await users.create_or_update_from_telegram(
            {
                "id": 1001,
                "username": "tester",
                "first_name": "Test",
                "last_name": "User",
            }
        )
        admin = await users.create_or_update_from_telegram({"id": 2002})
        await users.set_admin(admin.telegram_id)

        access_request = await requests.create_pending_request(user.id)
        await requests.approve_request(access_request.id, processed_by_admin_id=admin.id)

        snapshot = await rates.save_snapshot(
            nobitex_usdt_toman=Decimal("58200.12"),
            rapira_usdt_rub_base=Decimal("90.10"),
            rapira_usdt_rub_with_margin=Decimal("91.00"),
            margin_percent=Decimal("1.00"),
            rub_toman_raw=Decimal("639.56"),
            rub_toman_display=640,
        )

        assert await users.is_admin(admin.telegram_id) is True
        assert await users.is_approved(user.telegram_id) is True
        assert snapshot == await rates.get_latest_snapshot()

    await engine.dispose()


@pytest.mark.asyncio
async def test_start_auto_request_creates_single_pending_request():
    from src.models import Base
    from src.repositories.requests import AccessRequestRepository
    from src.repositories.users import UserRepository

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_maker() as session:
        users = UserRepository(session)
        requests = AccessRequestRepository(session)
        user = await users.create_or_update_from_telegram({"id": 3003})

        first_request = await requests.create_pending_request(user.id)
        second_request = await requests.create_pending_request(user.id)
        pending_requests = await requests.list_pending_requests()

        assert first_request.id == second_request.id
        assert len(pending_requests) == 1

    await engine.dispose()


@pytest.mark.asyncio
async def test_start_admin_does_not_need_pending_request():
    from src.models import Base
    from src.repositories.requests import AccessRequestRepository
    from src.repositories.users import UserRepository

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_maker() as session:
        users = UserRepository(session)
        requests = AccessRequestRepository(session)
        admin = await users.create_or_update_from_telegram({"id": 4004})
        await users.set_admin(admin.telegram_id)

        assert await users.is_admin(admin.telegram_id) is True
        assert await requests.get_active_pending_request(admin.id) is None

    await engine.dispose()


@pytest.mark.asyncio
async def test_start_approved_user_can_see_latest_snapshot():
    from src.models import Base
    from src.repositories.rates import RateRepository
    from src.repositories.users import UserRepository

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_maker() as session:
        users = UserRepository(session)
        rates = RateRepository(session)
        user = await users.create_or_update_from_telegram({"id": 5005})
        await users.approve_user(user.telegram_id)
        snapshot = await rates.save_snapshot(
            nobitex_usdt_toman=Decimal("180700"),
            rapira_usdt_rub_base=Decimal("76.51"),
            rapira_usdt_rub_with_margin=Decimal("79.233756"),
            margin_percent=Decimal("3.56"),
            rub_toman_raw=Decimal("2280.02"),
            rub_toman_display=2280,
            bitcoin_usd=80530,
            gold_ounce_usd=4670,
            oil_usd=Decimal("107.94"),
        )

        assert await users.is_approved(user.telegram_id) is True
        assert await rates.get_latest_snapshot() == snapshot

    await engine.dispose()
