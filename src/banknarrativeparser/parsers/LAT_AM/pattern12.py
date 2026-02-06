import re
import json


def normalize_narrative(line: str) -> str:
    if not line:
        return ""
    line = line.upper()
    line = re.sub(r"[\\|,]+", " ", line)
    line = re.sub(r"\s+", " ", line)
    return line.strip()


pattern12 = re.compile(r"\bSPEI\b", re.IGNORECASE)


def is_pattern12(line: str) -> bool:
    if not line:
        return False
    txt = normalize_narrative(line)
    return "SPEI" in txt


def infer_direction(txt: str) -> str | None:
    if any(x in txt for x in ["ENVIADO", "SALIENTE"]):
        return "OUTGOING"
    if any(x in txt for x in ["RECIBIDO", "ABONO", "INGRESO"]):
        return "INCOMING"
    if any(x in txt for x in ["DEVUELTO", "RECHAZADO", "REVERSO"]):
        return "RETURNED"
    return None


def extract_reference(txt: str) -> str | None:
    nums = re.findall(r"\b([0-9]{10,})\b", txt)
    if not nums:
        return None
    return max(nums, key=len)


def extract_originating_bank(txt: str) -> str | None:
    m = re.search(
        r"SPEI\s+(ENVIADO|SALIENTE|RECIBIDO|ABONO|INGRESO|DEVUELTO|RECHAZADO|REVERSO)\s+(.+?)\s+[0-9]",
        txt
    )
    if m:
        return m.group(2).strip()
    return None


def extract_counterparty(txt: str, reference: str | None) -> str | None:
    if not reference:
        return None

    m = re.search(reference + r"\s+(.+)$", txt)
    if not m:
        return None

    tail = m.group(1).strip()
    tokens = tail.split()

    ctpty = []
    for t in tokens:
        # purely numeric long token → stop
        if re.match(r"^[0-9]{6,}$", t):
            break
        # extremely long alphanumeric code → stop
        if re.match(r"^[A-Z0-9]{12,}$", t):
            break
        ctpty.append(t)

    return " ".join(ctpty) if ctpty else None


def parse_pattern12(line: str) -> dict | None:
    if not line:
        return None

    txt = normalize_narrative(line)

    if not is_pattern12(txt):
        return None

    direction = infer_direction(txt)
    reference = extract_reference(txt)
    bank = extract_originating_bank(txt)
    counterparty = extract_counterparty(txt, reference)

    return {
        "transaction_type": "SPEI_TRANSFER",
        "direction": direction,
        "originating_bank": bank,
        "ENTITY": counterparty,
        "reference_id": reference
    }


if __name__ == "__main__":
    pass
