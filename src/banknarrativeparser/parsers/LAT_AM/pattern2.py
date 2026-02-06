import re
import json

def normalize_narrative(line: str) -> str:
    if not line:
        return ""
    line = line.upper()
    line = re.sub(r"^[,|\\]+", "", line)
    line = re.sub(r"[\\|,]+$", "", line)
    line = re.sub(r"\s+", " ", line)
    return line.strip()

pattern2 = re.compile(
    r"^/[A-Z]{3}/\d{4}-PAGO TRANSFERENCIA",
    re.IGNORECASE
)

def is_pattern2(line: str) -> bool:
    if not line:
        return False
    line_n = normalize_narrative(line)
    return bool(pattern2.search(line_n))

pattern2_parse = re.compile(
    r"""
    ^
    /([A-Z]{3})                 # ledger class
    /([0-9]{4})-PAGO\sTRANSFERENCIA\s
    ([A-Z]+)                    # clearing system (SPEI)
    /([A-Z]+)                   # channel marker (HTC)
    /([A-Z]+)                   # operation type (TRF)
    /([A-Z]+)                   # account flag (AIN)
    /(.+)$                      # data block
    """,
    re.IGNORECASE | re.VERBOSE
)

RESERVED_TOKENS = {"RFC", "IVA", "REF", "TAX", "NUM", "ID"}

def extract_counterparty(raw: str) -> str | None:
    tokens = raw.split()
    clean = []
    for t in tokens:
        if t in RESERVED_TOKENS:
            break
        clean.append(t)
    if not clean:
        return None
    return " ".join(clean).strip()

def extract_rfc(raw: str) -> str | None:
    match = re.search(r"RFC\s+([A-Z0-9]+)", raw)
    return match.group(1) if match else None

def extract_iva(raw: str) -> str | None:
    match = re.search(r"IVA\s+([0-9]+)", raw)
    return match.group(1) if match else None

def parse_pattern2(line: str) -> dict | None:
    if not line:
        return None

    line_n = normalize_narrative(line)
    match = pattern2_parse.match(line_n)
    if not match:
        return None

    (
        ledger_class,
        txn_code,
        clearing_system,
        channel_marker,
        op_code,
        acct_flag,
        raw
    ) = match.groups()

    result = {
        "ledger_class": ledger_class,
        "transaction_code": txn_code,
        "transaction_category": "PAYMENT",
        "transaction_type": "ACCOUNT_TRANSFER",
        "operation_type": "TRANSFER",
        "clearing_system": clearing_system,
        "is_interbank": True,
        "account_based": (acct_flag == "AIN"),
        "channel_marker": channel_marker,
        "ENTITY": extract_counterparty(raw)
    }

    rfc = extract_rfc(raw)
    if rfc:
        result["ENTITY_TAX_ID"] = rfc

    iva = extract_iva(raw)
    if iva:
        result["tax_rate"] = iva

    return result

if __name__ == "__main__":
    pass
