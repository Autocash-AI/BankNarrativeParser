import re

# 1. NORMALIZATION (shared)
def normalize_narrative(line: str) -> str:
    if not line:
        return ""
    line = line.strip(",")
    line = re.sub(r"\s+", " ", line)
    return line.strip().upper()



# 2. IDENTIFICATION REGEX
VENDOR_PAY_RECOGNISE_RE = re.compile(
    r"\bVENDOR\s+PAY\b.*\b\d+\b$"
)


def is_vendor_pay_narrative(line: str) -> bool:
    norm = normalize_narrative(line)
    if not norm:
        return False
    return bool(VENDOR_PAY_RECOGNISE_RE.search(norm))



# 3. PARSING REGEX
VENDOR_PAY_PARSE_RE = re.compile(
    r"""
    ^
    (?P<CTPTY_NAME>.+?)\s+
    VENDOR\s+PAY\s+
    (?P<MANAGER_NAME>.+?)\s+
    (?P<VENDOR_PAY_ID>\d+)
    $
    """,
    re.VERBOSE
)


def parse_vendor_pay_narrative(line: str) -> dict:
    norm = normalize_narrative(line)

    match = VENDOR_PAY_PARSE_RE.search(norm)
    if not match:
        return {}

    return {
        "RAW": line,
        "ENTITY": match.group("CTPTY_NAME"),
        "TRANS_TYPE": "VENDOR_PAY",
        "MANAGER_NAME": match.group("MANAGER_NAME"),
        "VENDOR_PAY_ID": match.group("VENDOR_PAY_ID"),
    }
