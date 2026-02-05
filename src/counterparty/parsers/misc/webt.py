import re

def normalize_narrative(line: str) -> str:
    if not line:
        return ""
    line = line.lstrip(",")
    line = re.sub(r"[,\s]+$", "", line)
    line = re.sub(r"\s+", " ", line)
    return line.strip().upper()

WEB_TRANSFER_RECOGNISE_RE = re.compile(
    r"\bWEB\s+TFR\s+FR\s+\d+"
)

def is_web_transfer(line: str) -> bool:
    norm = normalize_narrative(line)
    if not norm:
        return False
    return bool(WEB_TRANSFER_RECOGNISE_RE.search(norm))

WEB_TRANSFER_PARSE_RE = re.compile(
    r"""
    ^
    WEB\s+TFR\s+FR\s+
    (?P<SOURCE_REF>\d+)
    \s+
    (?P<DESCRIPTION>.+?)
    \s+
    (?P<TRAILING_REFS>(\d+[,\s]?)+)
    $
    """,
    re.VERBOSE
)

def parse_web_transfer(line: str) -> dict:
    norm = normalize_narrative(line)

    m = WEB_TRANSFER_PARSE_RE.search(norm)
    if not m:
        return {
            "RAW": line,
            "META": norm
        }

    refs = re.findall(r"\d+", m.group("TRAILING_REFS"))

    return {
        "RAW": line,
        "FORMAT": "WEB_TRANSFER",
        "CHANNEL": "WEB",
        "SOURCE_REF": m.group("SOURCE_REF"),
        "DESCRIPTION": m.group("DESCRIPTION").strip(),
        "REFERENCE_IDS": refs,
        "META": norm
    }
