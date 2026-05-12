import sys
from decimal import Decimal
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from src.services.parser_service import (
    parse_nobitex_assets,
    parse_nobitex_usdt_toman,
    parse_rapira_usdt_rub,
)
from src.utils.numbers import normalize_digits


def test_normalize_digits_supports_persian_digits():
    assert normalize_digits("۰۱۲۳۴۵۶۷۸۹") == "0123456789"


def test_normalize_digits_supports_arabic_digits():
    assert normalize_digits("٠١٢٣٤٥٦٧٨٩") == "0123456789"


def test_parse_nobitex_usdt_toman_example():
    assert parse_nobitex_usdt_toman("تتر: ۱۸۰,۶۳۶ تومان") == 180636


def test_parse_full_nobitex_assets_message():
    message = (
        "🔴 بیت‌کوین: ۸۰٬۶۵۳ دلار\n"
        "🔴 تتر: ۱۸۰٬۴۰۰ تومان\n"
        "🟢 انس طلا: ۴٬۶۹۲ دلار\n"
        "🟢 نفت: ۱۰۷.۵۳ دلار"
    )

    assets = parse_nobitex_assets(message)

    assert assets is not None
    assert assets.bitcoin_usd == 80653
    assert assets.usdt_toman == 180400
    assert assets.gold_ounce_usd == 4692
    assert assets.oil_usd == Decimal("107.53")
    assert parse_nobitex_usdt_toman(message) == 180400


def test_parse_rapira_usdt_rub_example():
    assert parse_rapira_usdt_rub("USDT/RUB 76.52 - Rapira") == Decimal("76.52")


def test_parse_rapira_usdt_rub_supports_decimal_comma():
    assert parse_rapira_usdt_rub("USDT/RUB 76,52 - Rapira") == Decimal("76.52")


def test_parsers_return_none_for_invalid_messages():
    message = "No exchange rate here"

    assert parse_nobitex_usdt_toman(message) is None
    assert parse_rapira_usdt_rub(message) is None
