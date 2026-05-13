import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from src.services.rate_service import (
    RateCalculationResult,
    calculate_partner_rate,
    calculate_seconds_until_next_aligned_refresh,
)


def test_calculate_partner_rate_uses_decimal_formula():
    result = calculate_partner_rate(
        nobitex_usdt_toman=180636,
        rapira_usdt_rub_base=Decimal("76.52"),
        margin_percent=Decimal("3.56"),
    )

    assert isinstance(result, RateCalculationResult)
    assert result.nobitex_usdt_toman == 180636
    assert result.rapira_usdt_rub_base == Decimal("76.52")
    assert result.margin_percent == Decimal("3.56")
    assert result.rapira_usdt_rub_with_margin == Decimal("79.244112")
    assert result.rub_toman_raw == Decimal("180636") / Decimal("79.244112")
    assert result.rub_toman_raw.quantize(Decimal("0.001")) == Decimal("2279.488")
    assert result.rub_toman_display == 2279


def test_calculate_partner_rate_without_margin():
    result = calculate_partner_rate(
        nobitex_usdt_toman=1000,
        rapira_usdt_rub_base=Decimal("4"),
        margin_percent=Decimal("0"),
    )

    assert result.rapira_usdt_rub_with_margin == Decimal("4")
    assert result.rub_toman_raw == Decimal("250")
    assert result.rub_toman_display == 250


def test_calculate_partner_rate_required_final_example():
    result = calculate_partner_rate(
        nobitex_usdt_toman=180400,
        rapira_usdt_rub_base=Decimal("76.51"),
        margin_percent=Decimal("3.56"),
    )

    assert result.rapira_usdt_rub_with_margin == Decimal("79.233756")
    assert Decimal("2276.80") < result.rub_toman_raw < Decimal("2276.81")
    assert result.rub_toman_display == 2276


def test_next_aligned_refresh_from_between_marks():
    now = datetime(2026, 5, 12, 12, 52, 30)

    assert calculate_seconds_until_next_aligned_refresh(now, 5, 15) == 165


def test_next_aligned_refresh_after_delayed_mark():
    now = datetime(2026, 5, 12, 12, 55, 16)

    assert calculate_seconds_until_next_aligned_refresh(now, 5, 15) == 299


def test_next_aligned_refresh_before_next_hour_mark():
    now = datetime(2026, 5, 12, 12, 59, 50)

    assert calculate_seconds_until_next_aligned_refresh(now, 5, 15) == 25


def test_next_aligned_refresh_on_mark_before_delay():
    now = datetime(2026, 5, 12, 12, 0, 10)

    assert calculate_seconds_until_next_aligned_refresh(now, 5, 15) == 5


def test_next_aligned_refresh_on_mark_after_delay():
    now = datetime(2026, 5, 12, 12, 0, 16)

    assert calculate_seconds_until_next_aligned_refresh(now, 5, 15) == 299
