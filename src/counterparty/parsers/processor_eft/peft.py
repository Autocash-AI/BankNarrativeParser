import re

# NORMALIZATION
def normalize_narrative(line: str) -> str:
    if not line:
        return ""
    line = line.lstrip(",")
    line = re.sub(r"\s+", " ", line)
    return line.strip().upper()



# PROCESSOR EFT REGEX (TIGHTENED)
PROCESSOR_EFT_RECOGNISE_RE = re.compile(
    r"""
    ^
    (?P<proc>[A-Z][A-Z0-9 .,&'-]{0,60})   # processor name
    \s+
    (?P<code>[A-Z]{2,6})                  # processor code (min 2 chars)
    (?P<batch>\d{3,9})?                   # optional batch / id
    (?:
        \s+(?P<date>\d{6}) |              # YYMMDD
        \s+(?P<date_dash>\d{2}-\d{2}-\d{2})
    )?
    (?:\s+(?P<refs>[^:]+))?               # refs, no colon allowed
    $
    """,
    re.VERBOSE
)


_BANK_NAME_PATTERNS = [
    r"PNC",
    r"CHASE",
    r"CITI",
    r"BANK\s+OF\s+AMERICA",
    r"BOFA",
    r"WELLS\s+FARGO",
    r"CAPITAL\s+ONE",
    r"U\.S\.?BANK",
    r"US\s+BANK",
    r"TDBANK",
    r"TD\s+BANK"
]
_BANK_NAME_RE = re.compile(r"^(?:" + r"|".join(_BANK_NAME_PATTERNS) + r")\b")



# PEFT DETECTION (HARDENED)
def is_processor_eft(line: str) -> bool:
    norm = normalize_narrative(line)
    if not norm:
        return False

    if ":" in norm:
        return False

    if re.search(r"\b(NAME|RECEIVER|SENDER)\b", norm):
        return False

    if re.search(r"\b(COMP\s+ID|COMPANY\s+ID|MERCHANT)\b", norm):
        return False

    if re.search(r"\bREMOTE\s+DEPOSIT\b", norm):
        return False

    if re.search(r"\bMOBILE\s+DEPOSIT\b", norm):
        return False

    if re.search(r"\bFUNDS\s+TRANSFER\b", norm):
        return False

    if re.search(r"\bFRMDEP\b", norm):
        return False

    if re.search(r"\b(ACH|WIRE|FED|RDC|CARD)\b", norm):
        return False

    if "INTEREST" in norm and _BANK_NAME_RE.match(norm):
        return False

    # ---- FINAL STRUCTURAL CHECK ----
    return bool(PROCESSOR_EFT_RECOGNISE_RE.fullmatch(norm))



# PEFT PARSER
def parse_processor_eft(line: str) -> dict:
    norm = normalize_narrative(line)
    m = PROCESSOR_EFT_RECOGNISE_RE.fullmatch(norm)

    if not m:
        return {
            "RAW": line,
            "META": norm,
            "ERROR": "PROCESSOR_EFT_PARSE_FAILED"
        }

    ref_block = m.group("refs") or ""
    refs = [r for r in re.split(r"[\s,]+", ref_block) if r]

    return {
        "RAW": line,
        "TRANS_TYPE": "PROCESSOR_EFT",
        "ENTITY": m.group("proc").strip(),
        "PROCESSOR_CODE": m.group("code"),
        "BATCH_ID": m.group("batch"),
        "DATE": m.group("date") or m.group("date_dash"),
        "REFERENCE_IDS": refs,
    }
