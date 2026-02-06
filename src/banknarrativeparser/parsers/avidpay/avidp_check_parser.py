import re

def normalize_narrative(line: str) -> str:
    if not line: return ""
    line = re.sub(r"^[,\|]+", "", line)
    line = re.sub(r"[,\|\\]+$", "", line)
    line = re.sub(r"\s+", " ", line)
    return line.strip().upper()

AVIDPAY_CHECK_RECOGNISE_RE = re.compile(
    r"(?:^|[\s\-])AVIDPAY(?!.*\bACH\b).*REF\*?CK\*?\d+\*",
)


def is_avidpay_check(line: str) -> bool:
    norm = normalize_narrative(line)
    if not norm:
        return False
    return bool(AVIDPAY_CHECK_RECOGNISE_RE.search(norm))

AVIDPAY_CHECK_PARSE_RE = re.compile(
    r"""
    ^
    (?P<CTPTY_NAME>.+?)
    [\s\-]*
    AVIDPAY
    \s*
    REF\*?CK\*?(?P<CHECK_NO>\d+)\*
    (?P<PAYEE>.+?)
    $
    """,
    re.VERBOSE
)

AVIDPAY_CHECK_CCD_PARSE_RE = re.compile(
    r"""
    AVIDPAY
    .*?
    REF\*CK\*
    (?P<CHECK_NO>\d+)
    \*
    (?P<PAYEE>.+)
    $
    """,
    re.VERBOSE
)


def parse_avidpay_check(line: str) -> dict:
    norm = normalize_narrative(line)

    # Variant 1: backslash-delimited (existing one)
    m = AVIDPAY_CHECK_PARSE_RE.search(norm)
    if m:
        return {
            "RAW": line,
            "TRANS_TYPE": "AVIDPAY_CHECK",
            "CHECK_NO": m.group("CHECK_NO"),
            "ENTITY": m.group("PAYEE").strip(),
            "VARIANT": "LOCKBOX"
        }

    # Variant 2: CCD / ACH embedded AVIDPAY
    m = AVIDPAY_CHECK_CCD_PARSE_RE.search(norm)
    if m:
        return {
            "RAW": line,
            "TRANS_TYPE": "AVIDPAY_CHECK",
            "CHECK_NO": m.group("CHECK_NO"),
            "ENTITY": m.group("PAYEE").strip(),
            "VARIANT": "CCD"
        }

    return {
        "RAW": line,
        "META": norm,
        "ERROR": "AVIDPAY_CHECK_PARSE_FAILED"
    }


if __name__=='__main__':
    pass