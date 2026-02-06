import re
import json


# NORMALIZATION

def normalize_narrative(line: str) -> str:
    if not line:
        return ""
    line = re.sub(r"^[,|]+", "", line)
    line = re.sub(r"[\\|,]+$", "", line)
    line = re.sub(r"\s+", " ", line)
    return line.strip().upper()



# PAYPAL RECOGNIZERS

PAYPAL_RDC_RE = re.compile(
    r"\bPAYPAL\b.*\bRDC\b.*\bDEP\s+CR\b",
    re.IGNORECASE
)

PAYPAL_ACH_RETURN_PARSE_RE = re.compile(
    r"""
    PAYPAL\s+
    BANKBK\s+
    IBTRANSFER\s+
    ACH\s+RTN
    \s*-\s*
    (?P<RETURN_DATE>\d{1,2}/\d{1,2}/\d{4})
    \s*-\s*
    (?P<TRACE_BLOCK>[\d\s\-]+)
    """,
    re.VERBOSE
)



# CLASSIFIER

def classify_paypal(line: str) -> str | None:
    norm = normalize_narrative(line)

    if "PAYPAL" not in norm:
        return None

    if PAYPAL_ACH_RETURN_PARSE_RE.search(norm):
        return "PAYPAL_ACH_RETURN"

    if PAYPAL_RDC_RE.search(norm):
        return "PAYPAL_RDC_DEPOSIT"

    return "PAYPAL_OTHER"



# PARSERS


def parse_paypal_rdc(line: str) -> dict:
    norm = normalize_narrative(line)

    # find 6-digit token for deposit code
    deposit_code = None
    m = re.search(r"\b(\d{6})\b", norm)
    if m:
        deposit_code = m.group(1)

    return {
        "RAW": line,
        "FORMAT": "PAYPAL_RDC_DEPOSIT",
        "PROCESSOR": "PAYPAL",
        "RAIL": "RDC",
        "DIRECTION": "CREDIT",
        "deposit_code": deposit_code,
    }


def parse_paypal_ach_return(line: str) -> dict:
    norm = normalize_narrative(line)

    m = PAYPAL_ACH_RETURN_PARSE_RE.search(norm)
    if not m:
        return {
            "RAW": line,
            "META": norm,
            "ERROR": "PAYPAL_ACH_RETURN_PARSE_FAILED"
        }

    trace_parts = re.findall(r"\d+", m.group("TRACE_BLOCK"))

    return {
        "RAW": line,
        "TRANS_TYPE": "PAYPAL_ACH_RETURN",
        "RETURN_DATE": m.group("RETURN_DATE"),
        "TRACE_NUMBERS": trace_parts,
        "RAW_TRACE_BLOCK": m.group("TRACE_BLOCK"),
    }


def parse_paypal(line: str) -> dict | None:
    cls = classify_paypal(line)

    if cls == "PAYPAL_RDC_DEPOSIT":
        return parse_paypal_rdc(line)

    if cls == "PAYPAL_ACH_RETURN":
        return parse_paypal_ach_return(line)

    if cls == "PAYPAL_OTHER":
        return {
            "RAW": line,
            "FORMAT": "PAYPAL_OTHER",
        }

    return None

