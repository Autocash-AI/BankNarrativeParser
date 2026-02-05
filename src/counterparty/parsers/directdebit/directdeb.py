import re

def normalize_narrative(line: str) -> str:
    if not line:
        return ""
    line = re.sub(r"^[,|]+", "", line)
    line = re.sub(r"[\\|,]+$", "", line)
    line = re.sub(r"\s+", " ", line)
    return line.strip().upper()

DIRECT_DEBIT_RE = re.compile(
    r"""
    \b(
        DIRECT\s+DEB(IT)? |
        DIRECT\s+DEBIT |
        PAYMENT |
        PYMT |
        WITHDRAW(AL)? |
        AUTO(PAY)? |
        SUBSCRIPT(ION)? |
        MEMBERSHIP |
        RENT
    )\b
    """,
    re.VERBOSE
)


DIRECT_DEBIT_EXCLUDE_RE = re.compile(
    r"""
    \b(
        ACH |
        WIRE |
        CARD |
        RDC |
        CHECK |
        PAYPAL |
        AVIDPAY |
        TRANSACTION REF. |
        RMR |
        VENDORPYMT
    )\b
    """,
    re.VERBOSE
)

def is_direct_debit(line: str) -> bool:
    norm = normalize_narrative(line)
    if not norm:
        return False

    if DIRECT_DEBIT_EXCLUDE_RE.search(norm):
        return False

    return bool(DIRECT_DEBIT_RE.search(norm))

REF_RE = re.compile(r"\b[A-Z0-9\-]{6,}\b")

def parse_direct_debit(line: str) -> dict:
    norm = normalize_narrative(line)

    tokens = norm.split()

    counterparty_parts = []
    for t in tokens:
        if t in {"DIRECT", "DEBIT", "DEB", "PYMT", "PAYMENT", "PURCHASE"}:
            break
        counterparty_parts.append(t)

    counterparty = " ".join(counterparty_parts).strip() or None

    refs = REF_RE.findall(norm)

    return {
        "RAW": line,
        "TRANS_TYPE": "DIRECT_DEBIT",
        "ENTITY": counterparty,
        "REFERENCE_IDS": refs,
    }

