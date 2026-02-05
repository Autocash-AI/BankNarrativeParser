import re
import json


def normalize_narrative(line: str) -> str:
    if not line:
        return ""
    line = line.upper()
    line = re.sub(r"[\\|,]+", " ", line)
    line = re.sub(r"\s+", " ", line)
    return line.strip()


pattern7 = re.compile(
    r"TRASPASO",
    re.IGNORECASE
)


def is_pattern7(line: str) -> bool:
    if not line:
        return False
    txt = normalize_narrative(line)
    return "TRASPASO" in txt and ("A CTA" in txt or "A CUENTA" in txt)


def extract_reference_account(txt: str) -> str | None:
    m = re.search(r"A CTA\s*:?\s*([0-9]{8,})", txt)
    return m.group(1) if m else None


def extract_tax_amount(txt: str) -> float | None:
    m = re.search(r"IVA\s+([0-9]+\.[0-9]+)", txt)
    if not m:
        return None
    try:
        return float(m.group(1))
    except:
        return None


def extract_beneficiary_account(txt: str) -> str | None:
    m = re.search(r"A CUENTA\s+([0-9]{8,})", txt)
    return m.group(1) if m else None


def extract_rfc(txt: str) -> str | None:
    m = re.search(r"RFC\.?([A-Z0-9]+)", txt)
    if m:
        return m.group(1)
    m = re.search(r"R\.F\.C\.?([A-Z0-9]+)", txt)
    if m:
        return m.group(1)
    return None


def extract_beneficiary_name(txt: str, acct: str | None) -> str | None:
    if not acct:
        return None

    idx = txt.find(acct)
    if idx == -1:
        return None
    tail = txt[idx + len(acct):].strip()

    parts = []
    for t in tail.split():
        if t.startswith(("RFC", "R.F.C", "IVA")):
            break
        if re.match(r"[0-9]{4,}", t):
            break
        parts.append(t)

    if not parts:
        return None

    return " ".join(parts).strip()


def infer_direction(txt: str) -> str:
    incoming_markers = ["CR", "ABONO", "ACRED", "RECIBIDO", "INGRESO"]
    for mark in incoming_markers:
        if mark in txt:
            return "INCOMING"
    return "OUTGOING"


def parse_pattern7(line: str) -> dict | None:
    if not line:
        return None

    txt = normalize_narrative(line)

    if not is_pattern7(txt):
        return None

    direction = infer_direction(txt)
    reference_acct = extract_reference_account(txt)
    tax_amount = extract_tax_amount(txt)
    beneficiary_acct = extract_beneficiary_account(txt)
    rfc = extract_rfc(txt)
    name = extract_beneficiary_name(txt, beneficiary_acct)

    return {
        "transaction_type": "ACCOUNT_TRANSFER",
        "direction": direction,
        "beneficiary_name": name,
        "beneficiary_account": beneficiary_acct,
        "tax_amount": tax_amount,
        "reference_account": reference_acct,
        "rfc": rfc
    }


if __name__ == "__main__":
    pass
