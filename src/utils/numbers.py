PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
ARABIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"
ASCII_DIGITS = "0123456789"

_DIGIT_TRANSLATION = str.maketrans(
    {
        **dict(zip(PERSIAN_DIGITS, ASCII_DIGITS, strict=True)),
        **dict(zip(ARABIC_DIGITS, ASCII_DIGITS, strict=True)),
    }
)


def normalize_digits(text: str) -> str:
    return text.translate(_DIGIT_TRANSLATION)
