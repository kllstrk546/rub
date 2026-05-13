from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_FLOOR


@dataclass(frozen=True)
class RateCalculationResult:
    nobitex_usdt_toman: int
    rapira_usdt_rub_base: Decimal
    rapira_usdt_rub_with_margin: Decimal
    margin_percent: Decimal
    rub_toman_raw: Decimal
    rub_toman_display: int


def calculate_partner_rate(
    nobitex_usdt_toman: int,
    rapira_usdt_rub_base: Decimal,
    margin_percent: Decimal,
) -> RateCalculationResult:
    margin_multiplier = Decimal("1") + (margin_percent / Decimal("100"))
    rapira_usdt_rub_with_margin = rapira_usdt_rub_base * margin_multiplier
    rub_toman_raw = Decimal(nobitex_usdt_toman) / rapira_usdt_rub_with_margin
    rub_toman_display = int(rub_toman_raw.to_integral_value(rounding=ROUND_FLOOR))

    return RateCalculationResult(
        nobitex_usdt_toman=nobitex_usdt_toman,
        rapira_usdt_rub_base=rapira_usdt_rub_base,
        rapira_usdt_rub_with_margin=rapira_usdt_rub_with_margin,
        margin_percent=margin_percent,
        rub_toman_raw=rub_toman_raw,
        rub_toman_display=rub_toman_display,
    )


def calculate_seconds_until_next_aligned_refresh(
    now: datetime,
    every_minutes: int,
    delay_seconds: int,
) -> float:
    if every_minutes <= 0:
        raise ValueError("every_minutes must be greater than 0")
    if delay_seconds < 0:
        raise ValueError("delay_seconds must be non-negative")

    minute_remainder = now.minute % every_minutes
    minutes_to_add = 0 if minute_remainder == 0 else every_minutes - minute_remainder
    candidate = now.replace(second=0, microsecond=0) + timedelta(minutes=minutes_to_add)
    candidate = candidate + timedelta(seconds=delay_seconds)

    if candidate <= now:
        candidate = candidate + timedelta(minutes=every_minutes)

    return (candidate - now).total_seconds()
