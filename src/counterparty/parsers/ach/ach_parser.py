import re
from counterparty.key_engine.keys import KEYS, INLINE_KEYS
from counterparty.util import norm


KEYS = sorted(set(KEYS), key=len, reverse=True)
INLINE_KEYS = sorted(INLINE_KEYS, key=len, reverse=True)
ALLOWED = {' ', ':', '=', ',', '/', '\\', '_', '#', '-'}


ACH_RE = re.compile(
    r"\b(ACH|A\.?C\.?H|ODFI|RDFI|TRACE(\s*NO|\s*NUMBER)?|"
    r"COMPANY\s*ID|ENTRY\s*DESC|DISCRETIONARY|"
    r"SEC\s*(CCD|PPD|CTX|WEB|TEL|POP)|CCD|PPD|CTX|WEB)\b",
    re.I
)

ACH_EXCLUDE_RE = re.compile(
    r"\b(WIRE|FEDWIRE|FED\s*REF|IMAD|OMAD|UETR|MT\d{3}|"
    r"SWIFT|IBAN|ORG=|OBK=|IBK=|BBK=|BNF=|CARD|CHECK|RDC)\b",
    re.I
)

ACH_RETURN_RE = re.compile(
    r"\b(ACH\s*RTN|ACH\s*RETURN|RETURNED\s*ACH|ACH\s*REVERSAL)\b",
    re.I
)

ACH_RETURN_REASON_RE = re.compile(
    r"\b(NOT\s*AUTHORIZED|UNAUTHORIZED|CUSTOMER\s*ADVISES|"
    r"DISPUTE|REVERSAL)\b",
    re.I
)

BANK_PREFIX_RE = re.compile(
    r"^[A-Z][A-Z0-9&.\- ]{3,30}BK\b",
    re.I
)

REF_RE = re.compile(
    r"\b([A-Z]{2,6}\d{5,}|ITD\d+|TRACE\d+)\b",
    re.I
)


def is_ach(text: str) -> bool:
    t = norm(text)
    return bool(t and not ACH_EXCLUDE_RE.search(t) and ACH_RE.search(t))


def ach_return_parser(narr: str):
    t = norm(narr)
    if not t:
        return None

    if not ACH_RETURN_RE.search(t):
        return None

    out = {
        "RAW": narr,
        "txn_type": "ACH_RETURN",
        "rail": "ACH",
        "category": "BANK_ADJUSTMENT",
    }

    m = BANK_PREFIX_RE.search(t)
    if m:
        out["bank"] = m.group().strip()

    m = ACH_RETURN_REASON_RE.search(t)
    if m:
        out["return_reason"] = m.group().upper()

    m = REF_RE.search(t)
    if m:
        out["reference"] = m.group()

    try:
        a = ACH_RETURN_RE.search(t).end()
        name = t[a:]
        name = re.sub(r"\b(CUSTOMER\s+ADV\S*|ADV\S*)\b", "", name, flags=re.I)
        name = re.sub(r"\s{2,}", " ", name).strip(" -:,")
        if name:
            out["ENTITY"] = name
    except Exception:
        pass

    return out


def is_standalone(text, i, k_len):
    before = text[i - 1] if i > 0 else ' '
    after = text[i + k_len] if i + k_len < len(text) else ' '
    return before in ALLOWED and after in ALLOWED


def normalize_key(k: str):
    if k in ("REMAR K", "R EMARK", "REMA RK", "REMARK"):
        return "REMARK"
    return k


def find_keys(text, key_list):
    found = {}
    reserved = []

    for k in key_list:
        k_len = len(k)
        for i in range(len(text) - k_len + 1):
            if text[i:i + k_len] != k:
                continue
            if not is_standalone(text, i, k_len):
                continue
            if any(s <= i < e for s, e in reserved):
                continue

            found[i] = k
            reserved.append((i, i + k_len))

    return dict(sorted(found.items()))


def split_inline_keys(text: str):
    marks = find_keys(text, INLINE_KEYS)

    if not marks:
        return text.strip()

    idx = [0] + list(marks.keys()) + [len(text)]
    out = {}

    out["value"] = text[:idx[1]].strip()

    for i in range(1, len(idx) - 1):
        start, end = idx[i], idx[i + 1]
        raw_k = marks[start]
        k = normalize_key(raw_k)

        z = start + len(raw_k)
        while z < len(text) and not text[z].isalnum():
            z += 1

        out[k] = text[z:end].strip()

    return out


def ach_parser_v2(v1_output: dict):
    out = {}
    for k, v in v1_output.items():
        if isinstance(v, str):
            out[k] = split_inline_keys(v)
        else:
            out[k] = v
    return out


def ach_parser_v1(narr: str):
    marks = find_keys(narr, KEYS)

    idx = [0] + list(marks.keys()) + [len(narr)]
    out = {}

    out["META"] = narr[:idx[1]].strip()

    for i in range(1, len(idx) - 1):
        start, end = idx[i], idx[i + 1]
        raw_k = marks[start]
        k = normalize_key(raw_k)

        z = start + len(raw_k)
        while z < len(narr) and not narr[z].isalnum():
            z += 1

        out[k] = narr[z:end].strip()

    return out


def ach_parser(narr: str):
    rtn = ach_return_parser(narr)
    if rtn:
        return rtn

    v1 = ach_parser_v1(narr)
    v2 = ach_parser_v2(v1)
    return {
        "RAW": narr,
        **v2
    }
