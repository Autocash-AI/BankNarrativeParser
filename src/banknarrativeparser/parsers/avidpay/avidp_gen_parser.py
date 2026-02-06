import re
from .avidp_check_parser import is_avidpay_check

def normalize_narrative(line: str) -> str:
    if not line:
        return ""
    line = line.lstrip(",")
    line = re.sub(r"[,\s]+$", "", line)
    line = re.sub(r"\s+", " ", line)
    return line.strip().upper()

AVIDPAY_GENERIC_RECOGNISE_RE = re.compile(
    r"\bAVIDPAY\b\s+REFCK\d+\*.+$"
)

def is_avidpay_generic(line: str) -> bool:
    norm = normalize_narrative(line)
    if not norm:
        return False

    # exclude full check grammar (those are handled earlier)
    if is_avidpay_check(norm):
        return False

    return bool(AVIDPAY_GENERIC_RECOGNISE_RE.search(norm))

AVIDPAY_GENERIC_PARSE_RE = re.compile(
    r"""
    ^
    (?P<COUNTERPARTY_NAME>.+?)\-?
    AVIDPAY\s+
    REFCK(?P<CHECK_NO>\d+)
    \*
    (?P<PAYEE_NAME>.+)
    $
    """,
    re.VERBOSE
)

def parse_avidpay_generic(line: str) -> dict:
    norm = normalize_narrative(line)

    m = AVIDPAY_GENERIC_PARSE_RE.search(norm)
    if not m:
        return {
            "RAW": line,
            "META": norm
        }

    return {
        "RAW": line,
        "FORMAT": "AVIDPAY_GENERIC",
        "PROCESSOR": "AVIDPAY",
        "PAYMENT_METHOD": "CHECK",
        "ENTITY": m.group("COUNTERPARTY_NAME").rstrip("-"),
        "CHECK_NO": m.group("CHECK_NO"),
        "PAYEE_NAME": m.group("PAYEE_NAME"),
        "META": norm
    }
