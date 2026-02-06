import re

# 1. NORMALIZATION
def normalize_narrative(line: str) -> str:
    if not line:
        return ""
    line = line.lstrip(",")
    line = re.sub(r"\s+", " ", line)
    return line.strip().upper()



# 2. RECOGNIZER 
FUNDS_TRANSFER_RECOGNISE_RE = re.compile(
    r"\b(FUNDS|SWEEP)\b.*\b(TO|FROM|FRMDEP)\b"
)

def is_funds_transfer_frmdep(line: str) -> bool:
    return bool(FUNDS_TRANSFER_RECOGNISE_RE.search(normalize_narrative(line)))



# 3. PARSER 
FUNDS_TRANSFER_PARSE_RE = re.compile(
    r"""
    (?:REF\s+(?P<REF_NO>\w+)\s+)?              
    (?:FUNDS|SWEEP)\s+
    (?:TRANSF(?:ER|R)\s+)?                     

    (?:
        FRMDEP\s+(?P<FROM_ACCOUNT>\d+|[X*]+\d+) |
        FROM\s+.*?(?P<FROM_ACCOUNT2>\d+|[X*]+\d+) |
        TO\s+.*?(?P<TO_ACCOUNT>\d+|[X*]+\d+)
    )
    """,
    re.VERBOSE
)


# 4. FEE NORMALIZATION
def normalize_fee_text(text: str) -> str:
    t = re.sub(r"\s+", " ", text.upper())
    t = re.sub(r"\bMONTH\s*LY\b", "MONTHLY", t)
    t = re.sub(
        r"\b(MGMT|MGM|MANAG(E|EMENT)?)\s*(FEE|FE|EE)\b",
        "MANAGEMENT FEE",
        t
    )
    return t.strip()



# 5. FINAL PARSER
def parse_funds_transfer_frmdep(line: str) -> dict:
    norm = normalize_narrative(line)
    m = FUNDS_TRANSFER_PARSE_RE.search(norm)

    if not m:
        return {}

    out = {
        "RAW": line,
        "TRANS_TYPE": "INTERNAL_FUNDS_TRANSFER",
    }

    if m.group("REF_NO"):
        out["REF_NO"] = m.group("REF_NO")

    from_acct = m.group("FROM_ACCOUNT") or m.group("FROM_ACCOUNT2")
    to_acct = m.group("TO_ACCOUNT")

    if from_acct:
        out["FROM_ACCOUNT"] = from_acct
        out["DIRECTION"] = "DEBIT"

    if to_acct:
        out["TO_ACCOUNT"] = to_acct
        out["DIRECTION"] = "CREDIT"

    return out
