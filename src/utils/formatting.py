from decimal import Decimal
from datetime import datetime
from typing import Any


def format_int_spaces(value: int) -> str:
    return f"{value:,}".replace(",", " ")


def format_int_commas(value: int | None) -> str:
    if value is None:
        return "-"
    return f"{value:,}"


def format_decimal(value: Decimal, places: int = 4) -> str:
    if places == 0:
        return format_int_spaces(int(value))

    quant = Decimal("1").scaleb(-places)
    formatted = f"{value.quantize(quant):f}"
    whole, _, fraction = formatted.partition(".")
    return f"{format_int_spaces(int(whole))}.{fraction}" if fraction else format_int_spaces(int(whole))


def format_rate_snapshot(snapshot: Any) -> str:
    updated_at = format_datetime(snapshot.created_at)
    return (
        "Актуальный курс:\n\n"
        f"1 RUB = {format_int_spaces(snapshot.rub_toman_display)} TOMAN\n\n"
        f"Биткоин: {format_int_commas(snapshot.bitcoin_usd)} $\n"
        f"USDT: {format_int_commas(int(snapshot.nobitex_usdt_toman))} تومان\n"
        f"Унция золота: {format_int_commas(snapshot.gold_ounce_usd)} $\n"
        f"Нефть: {format_oil_price(snapshot.oil_usd)} $\n\n"
        f"Обновлено: {updated_at}"
    )


def format_datetime(value: datetime | None) -> str:
    if value is None:
        return "-"
    return value.astimezone().strftime("%d.%m.%Y %H:%M:%S")


def format_oil_price(value: Decimal | None) -> str:
    if value is None:
        return "-"
    formatted = f"{value.quantize(Decimal('0.01')):f}"
    return formatted.replace(".", ",")
