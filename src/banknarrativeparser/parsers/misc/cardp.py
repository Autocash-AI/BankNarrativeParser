import re

def normalize_narrative(line: str) -> str:
    if not line:
        return ""
    line = line.lstrip(",")
    line = re.sub(r"[,\s]+$", "", line)
    line = re.sub(r"\s+", " ", line)
    return line.strip().upper()

CARD_PAYMENT_RECOGNISE_RE = re.compile(
    r"""
    ^[A-Z0-9 .&'-]+
    \s+
    (ONLINE|POS)\s+PMT
    \s+
    \d{8,}$
    """,
    re.VERBOSE
)

def is_card_payment(line: str) -> bool:
    norm = normalize_narrative(line)
    if not norm:
        return False

    # hard guard: exclude known rails / processors
    if any(k in norm for k in (
        "ACH", "WIRE", "REF ", "VAID", "RMR", "VENDOR", "AVIDPAY", "DISBURSE", "TFR"
    )):
        return False

    return bool(CARD_PAYMENT_RECOGNISE_RE.search(norm))

CARD_PAYMENT_PARSE_RE = re.compile(
    r"""
    ^
    (?P<MERCHANT_NAME>.+?)\s+
    (?P<CHANNEL>ONLINE|POS)\s+PMT
    \s+
    (?P<REFERENCE_ID>\d+)
    $
    """,
    re.VERBOSE
)

def parse_card_payment(line: str) -> dict:
    norm = normalize_narrative(line)

    m = CARD_PAYMENT_PARSE_RE.search(norm)
    if not m:
        return {"META": norm}

    return {
        "RAW": line,
        "FORMAT": "CARD_PAYMENT",
        "ENTITY": m.group("MERCHANT_NAME"),
        "CHANNEL": m.group("CHANNEL"),
        "REFERENCE_ID": m.group("REFERENCE_ID"),
        "META": norm
    }
