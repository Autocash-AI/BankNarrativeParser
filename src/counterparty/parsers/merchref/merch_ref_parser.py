import re

def normalize_narrative(line: str) -> str:
    if not line:
        return ""
    line = line.lstrip(",")
    line = re.sub(r"[,\s]+$", "", line)
    line = re.sub(r"\s+", " ", line)
    return line.strip().upper()

MERCHANT_REF_SIMPLE_RE = re.compile(
    r"^[A-Z0-9 .&'-]+?\s+[A-Z0-9-]{2,}\s+\d{6,}\s+\d{6,}$"
)

MERCHANT_REF_CONTEXT_RE = re.compile(
    r"""
    ^
    [A-Z .&'-]+
    (?:\s+[A-Z0-9]{2,})+
    \s+[A-Z .&]{3,}
    \s+[A-Z0-9]{6,}
    $
    """,
    re.VERBOSE
)

def is_merchant_reference(line: str) -> bool:
    norm = normalize_narrative(line)
    return bool(
        MERCHANT_REF_SIMPLE_RE.match(norm)
        or MERCHANT_REF_CONTEXT_RE.match(norm)
    )



def parse_merchant_reference(line: str) -> dict:
    norm = normalize_narrative(line)
    parts = norm.split()

    return {
        "RAW": line,
        "FORMAT": "MERCHANT_REFERENCE",
        "ENTITY": " ".join(parts[:-3]),
        "REFERENCE_BLOCK": " ".join(parts[-3:]),
    }


