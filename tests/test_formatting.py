import sys
import inspect
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from src.bot.keyboards import rate_snapshot_keyboard
from src.bot import handlers_user
from src.utils.formatting import format_decimal, format_int_spaces, format_rate_snapshot


@dataclass
class SnapshotStub:
    nobitex_usdt_toman: Decimal
    rapira_usdt_rub_base: Decimal
    rapira_usdt_rub_with_margin: Decimal
    margin_percent: Decimal
    rub_toman_display: int
    created_at: datetime
    bitcoin_usd: int
    gold_ounce_usd: int
    oil_usd: Decimal


def test_format_int_spaces():
    assert format_int_spaces(2279) == "2 279"
    assert format_int_spaces(180636) == "180 636"


def test_format_decimal():
    assert format_decimal(Decimal("76.52"), places=2) == "76.52"
    assert format_decimal(Decimal("79.244112"), places=4) == "79.2441"


def test_format_rate_snapshot():
    snapshot = SnapshotStub(
        nobitex_usdt_toman=Decimal("180636"),
        rapira_usdt_rub_base=Decimal("76.52"),
        rapira_usdt_rub_with_margin=Decimal("79.244112"),
        margin_percent=Decimal("3.56"),
        rub_toman_display=2277,
        created_at=datetime(2026, 5, 11, 23, 55),
        bitcoin_usd=80653,
        gold_ounce_usd=4692,
        oil_usd=Decimal("107.53"),
    )

    text = format_rate_snapshot(snapshot)

    assert text == (
        "Актуальный курс:\n\n"
        "1 RUB = 2 277 TOMAN\n\n"
        "Биткоин: 80,653 $\n"
        "USDT: 180,636 تومان\n"
        "Унция золота: 4,692 $\n"
        "Нефть: 107,53 $\n\n"
        "Обновлено: 11.05.2026 23:55:00"
    )
    assert "USDT/TOMAN Nobitex" not in text
    assert "USDT/RUB Rapira" not in text
    assert "Детали расчёта" not in text
    assert "Debug" not in text
    assert "Snapshot" not in text
    assert "message_id" not in text
    assert "Последние сообщения" not in text


def test_rate_keyboard_contains_only_refresh_button():
    keyboard = rate_snapshot_keyboard()

    assert len(keyboard.inline_keyboard) == 1
    assert len(keyboard.inline_keyboard[0]) == 1
    assert keyboard.inline_keyboard[0][0].text == "Обновить"


def test_public_handlers_do_not_check_access_or_create_requests():
    source = inspect.getsource(handlers_user)

    assert "is_approved" not in source
    assert "is_admin" not in source
    assert "AccessRequest" not in source
    assert "pending" not in source
    assert "request_access" not in source


def test_public_start_and_refresh_force_refresh_rate():
    start_source = inspect.getsource(handlers_user.handle_start)
    refresh_source = inspect.getsource(handlers_user.handle_refresh_rate)

    assert 'reason="user_start"' in start_source
    assert 'reason="manual_button"' in refresh_source
    assert "force_refresh_rate" in inspect.getsource(handlers_user._get_public_rate_snapshot)
    assert "edit_text" in refresh_source


def test_router_does_not_include_admin_router():
    router_source = (PROJECT_ROOT / "src" / "bot" / "router.py").read_text(encoding="utf-8")

    assert "handlers_admin" not in router_source
    assert "admin_router" not in router_source
