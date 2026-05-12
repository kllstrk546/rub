import ast
from decimal import Decimal
from pathlib import Path

from src.config import Settings
from src.services.rate_service import calculate_partner_rate


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_no_float_literals_or_float_calls_in_project_code():
    for path in (PROJECT_ROOT / "src").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            assert not (isinstance(node, ast.Constant) and isinstance(node.value, float)), path
            assert not (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "float"
            ), path


def test_admin_env_values_support_comma_separated_lists():
    settings = Settings(
        admin_ids="547486189, 7711077335",
        admin_usernames="bruhmomenteverytime,moreforsure",
    )

    assert settings.admin_ids == [547486189, 7711077335]
    assert settings.admin_usernames == ["bruhmomenteverytime", "moreforsure"]


def test_default_margin_percent_is_3_56():
    settings = Settings(_env_file=None)

    assert settings.rate_margin_percent == Decimal("3.56")


def test_required_financial_example_display_value():
    result = calculate_partner_rate(
        nobitex_usdt_toman=180636,
        rapira_usdt_rub_base=Decimal("76.52"),
        margin_percent=Decimal("3.56"),
    )

    assert result.rapira_usdt_rub_with_margin == Decimal("79.244112")
    assert result.rub_toman_display == 2279
