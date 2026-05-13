import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from src.utils.numbers import normalize_digits


@dataclass(frozen=True)
class NobitexAssets:
    bitcoin_usd: int
    usdt_toman: int
    gold_ounce_usd: int
    oil_usd: Decimal


NOBITEX_KEYWORDS = ("تتر", "USDT", "Tether", "تومان")
NOBITEX_NUMBER_RE = re.compile(r"\d[\d,\s،٬]*(?:[.٫]\d+)?|\d+")
RAPIRA_USDT_RUB_RE = re.compile(
    r"USDT/RUB\s*([0-9]+(?:[.,][0-9]+)?)",
    re.IGNORECASE,
)
THOUSAND_SEPARATORS = str.maketrans("", "", ", ،٬\u2009\u202f")


def parse_nobitex_usdt_toman(message: str) -> int | None:
    assets = parse_nobitex_assets(message)
    if assets is not None:
        return assets.usdt_toman

    normalized_message = normalize_digits(message)

    for line in normalized_message.splitlines():
        if not _contains_nobitex_keyword(line):
            continue

        value = _extract_first_number(line)
        if value is not None:
            return int(value)

    return None


def parse_nobitex_assets(message: str) -> NobitexAssets | None:
    normalized_message = normalize_digits(message)
    bitcoin_usd = _extract_number_after_keywords(normalized_message, ("بیت‌کوین", "بیت کوین", "BTC"))
    usdt_toman = _extract_number_after_keywords(normalized_message, ("تتر", "USDT", "Tether"))
    gold_ounce_usd = _extract_number_after_keywords(normalized_message, ("انس طلا", "XAUT"))
    oil_usd = _extract_number_after_keywords(normalized_message, ("نفت",))

    if None in (bitcoin_usd, usdt_toman, gold_ounce_usd, oil_usd):
        return None

    return NobitexAssets(
        bitcoin_usd=int(bitcoin_usd),
        usdt_toman=int(usdt_toman),
        gold_ounce_usd=int(gold_ounce_usd),
        oil_usd=oil_usd,
    )


def parse_rapira_usdt_rub(message: str) -> Decimal | None:
    normalized_message = normalize_digits(message)
    match = RAPIRA_USDT_RUB_RE.search(normalized_message)
    if not match:
        return None

    try:
        return Decimal(match.group(1).replace(",", "."))
    except InvalidOperation:
        return None


def _contains_nobitex_keyword(line: str) -> bool:
    normalized_line = line.casefold()
    return any(keyword.casefold() in normalized_line for keyword in NOBITEX_KEYWORDS)


def _extract_first_number(line: str) -> Decimal | None:
    match = NOBITEX_NUMBER_RE.search(line)
    if not match:
        return None

    raw_number = match.group(0)
    clean_number = raw_number.translate(THOUSAND_SEPARATORS).replace("٫", ".")
    try:
        return Decimal(clean_number)
    except InvalidOperation:
        return None


def _extract_number_after_keywords(text: str, keywords: tuple[str, ...]) -> Decimal | None:
    folded_text = text.casefold()
    for keyword in keywords:
        index = folded_text.find(keyword.casefold())
        if index == -1:
            continue

        tail = text[index + len(keyword): index + len(keyword) + 80]
        value = _extract_first_number(tail)
        if value is not None:
            return value

    return None
