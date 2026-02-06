import re

# 1. Normalization (run ONCE before any recognition/parsing)
def normalize_narrative(line: str) -> str:
    if not line:
        return ""
    line = line.lstrip(",")
    line = re.sub(r"\s+", " ", line)
    return line.strip().upper()



# 2. Recognition regex
DISBURSEMENT_RECOGNISE_RE = re.compile(
    r"\bDISBURSEME\b\s+\d{6}\s+VAID-\d+(?:VAID-\d+)?"
)



def is_disbursement_narrative(line: str) -> bool:
    norm = normalize_narrative(line)
    if not norm:
        return False
    return bool(DISBURSEMENT_RECOGNISE_RE.search(norm))


# 3. Parsing regex
DISBURSEMENT_PARSE_RE = re.compile(
    r"""
    ^
    (?P<CTPTY_NAME>.+?)\s+
    DISBURSEME\s+
    (?P<DATE>\d{6})\s+
    VAID-(?P<VAID>\d+)
    """,
    re.VERBOSE
)

VAID_ALL_RE = re.compile(r"VAID-(\d+)")

DISBURSEMENT_PARSE_RE = re.compile(
    r"""
    ^
    (?P<CTPTY_NAME>.+?)\s+
    DISBURSEME\s+
    (?P<DATE>\d{6})
    """,
    re.VERBOSE
)

def parse_disbursement_narrative(line: str) -> dict:
    norm = normalize_narrative(line)

    m = DISBURSEMENT_PARSE_RE.search(norm)
    if not m:
        return {}

    vaids = VAID_ALL_RE.findall(norm)

    return {
        "RAW": line,
        "ENTITY": m.group("CTPTY_NAME"),
        "TRANS_TYPE": "DISBURSEMENT",
        "VALUE_DATE": m.group("DATE"),
        "VAID": vaids,              
    }



if __name__=='__main__':
    pass

