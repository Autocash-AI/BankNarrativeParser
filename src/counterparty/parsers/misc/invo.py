import re

def normalize_narrative(line: str) -> str:
    if not line:
        return ""
    line = line.lstrip(",")
    line = re.sub(r"[,\s]+$", "", line)
    line = re.sub(r"\s+", " ", line)
    return line.strip().upper()

INVOICE_REFERENCE_RECOGNISE_RE = re.compile(
    r".+\/INVOICE\s+\w+\s+.+"
)

INVOICE_ALT_RECOGNISE_RE = re.compile(
    r"^.+?\s+INVOICE\s+\d{6}\s+[A-Z0-9]+(?:[A-Z0-9]+)?$", 
    re.IGNORECASE
)

def is_invoice_reference(line: str) -> bool:
    norm = normalize_narrative(line)
    if not norm:
        return False
    return bool(INVOICE_REFERENCE_RECOGNISE_RE.search(norm)) or bool(INVOICE_ALT_RECOGNISE_RE.search(norm))


INVOICE_REFERENCE_PARSE_RE = re.compile(
    r"""
    ^
    (?P<ENTITY_NAME>.+?)\/
    INVOICE\s+
    (?P<INVOICE_NO>[A-Z0-9]+)
    \s+
    (?P<SERVICE_PROVIDER>.+)
    $
    """,
    re.VERBOSE
)
INVOICE_ALT_PARSE_RE = re.compile(
    r"^(?P<ENTITY_NAME>.+?)\s+INVOICE\s+(?P<DATE>\d{6})\s+(?P<INVOICE_NO>[A-Z0-9]+(?:[A-Z0-9]+)?)$",
    re.IGNORECASE
)

def parse_invoice_reference(line: str) -> dict:
    norm = normalize_narrative(line)

    # first try slash /INVOICE format
    m = INVOICE_REFERENCE_PARSE_RE.search(norm)
    if m:
        return {
            "RAW": line,
            "FORMAT": "INVOICE_REFERENCE",
            "ENTITY": m.group("ENTITY_NAME"),
            "DOCUMENT_TYPE": "INVOICE",
            "INVOICE_NO": m.group("INVOICE_NO"),
            "SERVICE_PROVIDER": m.group("SERVICE_PROVIDER"),
            "META": norm
        }

    # try alternate format
    m2 = INVOICE_ALT_PARSE_RE.search(norm)
    if m2:
        return {
            "RAW": line,
            "FORMAT": "INVOICE_REFERENCE",
            "ENTITY": m2.group("ENTITY_NAME"),
            "DOCUMENT_TYPE": "INVOICE",
            "INVOICE_NO": m2.group("INVOICE_NO"),
            "DATE": m2.group("DATE"),
            "META": norm
        }

    return {
        "RAW": line,
        "META": norm, 
        "ERROR": "INVOICE_PARSE_FAILED"
    }

