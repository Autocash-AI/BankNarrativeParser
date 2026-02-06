import re
from typing import Dict, Optional


def normalize_narrative(line: str) -> str:
    if not line:
        return ""
    line = line.upper()
    line = re.sub(r"^[,|\\]+", "", line)
    line = re.sub(r"[\\|,]+$", "", line)
    line = re.sub(r"\s+", " ", line)
    return line.strip()


def is_pattern1(line: str) -> bool:
    return normalize_narrative(line).startswith("/PT/")


def is_pattern1a(line: str) -> bool:
    txt = normalize_narrative(line)
    return bool(re.match(r"^/PT/DE/EI/", txt))


def is_pattern1b(line: str) -> bool:
    txt = normalize_narrative(line)

    if not txt.startswith("/PT/"):
        return False

    parts = [p for p in txt.split("/") if p]
    if len(parts) < 6:
        return False

    kv = 0
    i = 1
    while i + 1 < len(parts):
        k = parts[i]
        v = parts[i + 1]
        if 1 <= len(k) <= 4 and v:
            kv += 1
            i += 2
        else:
            i += 1

    return kv >= 3


def is_pattern1c(line: str) -> bool:
    txt = normalize_narrative(line)
    if not txt.startswith("/PT/"):
        return False
    return True


def detect_pattern1_variant(line: str) -> str:
    if is_pattern1a(line):
        return "1A"
    if is_pattern1b(line):
        return "1B"
    if is_pattern1c(line):
        return "1C"
    return "UNKNOWN"


pattern1a_full = re.compile(
    r"^/([A-Z/]+)\s+REF\.?\s+(\d+)\s+A\sF/V\s+(.+?)\s+([A-Z0-9]{2,5})\s+([0-9]{2})(?:/([A-Z0-9]{2,10})/([0-9]{1,5})/([A-Z0-9]+))?$",
    re.IGNORECASE
)

pattern1a_short = re.compile(
    r"^/([A-Z/]+)([0-9]+)?(?:[-\s]+(.+))?$",
    re.IGNORECASE
)


def parse_pattern1a(line: str) -> Optional[Dict]:
    txt = normalize_narrative(line)

    m = pattern1a_full.match(txt)
    if m:
        (
            flags_raw,
            reference_id,
            beneficiary,
            internal_code,
            seq_no,
            tag,
            code,
            action
        ) = m.groups()

        return {
            "variant": "1A",
            "transaction_type": "PAYMENT",
            "flags": [f for f in flags_raw.split("/") if f],
            "reference_id": reference_id,
            "beneficiary": beneficiary.strip(),
            "internal_code": internal_code,
            "sequence_number": seq_no,
            "control_tag": tag,
            "control_code": code,
            "transaction_action": action,
        }

    m = pattern1a_short.match(txt)
    if m:
        flags_raw, internal_code, detail = m.groups()
        return {
            "variant": "1A",
            "transaction_type": "PAYMENT",
            "flags": [f for f in flags_raw.split("/") if f],
            "internal_code": internal_code,
            "detail": detail,
        }

    return None


def parse_pattern1b(line: str) -> Dict:
    txt = normalize_narrative(line)
    parts = [p for p in txt.split("/") if p]

    fields = {}
    i = 1
    while i + 1 < len(parts):
        k = parts[i]
        v = parts[i + 1]
        if 1 <= len(k) <= 4:
            if k not in fields:
                fields[k] = v.strip()
            i += 2
        else:
            i += 1

    return {
        "variant": "1B",
        "transaction_type": "SETTLEMENT",
        "flags": [parts[0]],
        **fields
    }


def parse_pattern1c(line: str) -> Dict:
    txt = normalize_narrative(line)
    parts = [p for p in txt.split("/") if p]

    return {
        "variant": "1C",
        "transaction_type": "PATTERN1_PARTIAL",
        "tokens": parts
    }


def parse_pattern1(line: str) -> Optional[Dict]:
    if not is_pattern1(line):
        return None

    v = detect_pattern1_variant(line)

    if v == "1A":
        return parse_pattern1a(line)

    if v == "1B":
        return parse_pattern1b(line)

    if v == "1C":
        return parse_pattern1c(line)

    return {}
