import re
import json


def normalize_narrative(line: str) -> str:
    if not line:
        return ""
    line = line.upper()
    line = re.sub(r"^[,|\\]+", "", line)
    line = re.sub(r"[\\|,]+$", "", line)
    line = re.sub(r"\s+", " ", line)
    return line.strip()


card_keywords = [
    "DINERS CLUB",
    "DINERS",
    "VISA",
    "VISANET",
    "MASTERCARD",
    "AMEX",
    "AMERICAN EXPRESS",
    "DISCOVER",
    "REDCARD",
    "PROSA"
]


pattern11 = re.compile(
    "|".join(card_keywords),
    re.IGNORECASE
)


def is_pattern11(line: str) -> bool:
    if not line:
        return False
    txt = normalize_narrative(line)
    return bool(pattern11.search(txt))


def extract_posting_code(txt: str) -> str | None:
    # leading alphanumeric block e.g. 2401DE
    m = re.match(r"([A-Z0-9]+)", txt)
    return m.group(1) if m else None


def extract_network(txt: str) -> str | None:
    for w in card_keywords:
        if w in txt:
            return w
    return None


def parse_pattern11(line: str) -> dict | None:
    if not line:
        return None

    txt = normalize_narrative(line)

    if not is_pattern11(txt):
        return None

    posting_code = extract_posting_code(txt)
    network = extract_network(txt)

    return {
        "transaction_type": "CARD_PAYMENT",
        "direction": "OUTGOING",
        "card_network": network,
        "posting_code": posting_code
    }


if __name__ == "__main__":
    pass
