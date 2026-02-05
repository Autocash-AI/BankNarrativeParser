import re
import json


def normalize_narrative(line: str) -> str:
    if not line:
        return ""
    line = line.upper()
    line = re.sub(r"[\\|,]+", " ", line)
    line = re.sub(r"\s+", " ", line)
    return line.strip()


pattern8 = re.compile(
    r"(CONTRACARGO|CHARGEBACK)",
    re.IGNORECASE
)


def is_pattern8(line: str) -> bool:
    if not line:
        return False
    txt = normalize_narrative(line)
    return bool(pattern8.search(txt))


def extract_merchant(txt: str) -> str | None:
    """
    CC D LOCALREST DIDI 08934620 ...
    → merchant = LOCALREST DIDI
    """
    m = re.search(r"CC\s+D\s+(.+?)\s+[0-9]{4,}", txt)
    if not m:
        return None

    raw = m.group(1).strip()

    # remove known filler tokens if present
    banned = {"AFIL.", "CONTRACARGO", "APLICADO"}
    parts = [w for w in raw.split() if w not in banned]

    merchant = " ".join(parts).strip()
    return merchant if merchant else None


def extract_last4(txt: str) -> str | None:
    # TARJ.NO.42686031
    m = re.search(r"TARJ\.NO\.([0-9]{8,})", txt)
    if not m:
        return None
    digits = m.group(1)
    return digits[-4:]


def extract_date(txt: str) -> str | None:
    # F.TRANS.02-10-2025
    m = re.search(r"F\.TRANS\.([0-9]{2})-([0-9]{2})-([0-9]{4})", txt)
    if not m:
        return None
    dd, mm, yyyy = m.groups()
    return f"{yyyy}-{mm}-{dd}"


def extract_auth(txt: str) -> str | None:
    # NO.AUT.379320
    m = re.search(r"NO\.AUT\.([0-9]+)", txt)
    return m.group(1) if m else None


def extract_reason_code(txt: str) -> str | None:
    # RAZON 0068
    m = re.search(r"RAZON\s+([0-9]{4})", txt)
    return m.group(1) if m else None


def extract_reason(txt: str) -> str | None:
    """
    Capture all text after reason code until TARJREFERENCIA
    Example:
    RAZON 0068 VENTA NO RECONOCIDA POR TARJETAHABIENTE TARJREFERENCIA <num>
    """
    m = re.search(
        r"RAZON\s+[0-9]{4}\s+(.+?)\s+TARJREFERENCIA",
        txt
    )
    if m:
        return m.group(1).strip()

    # fallback: until end
    m = re.search(r"RAZON\s+[0-9]{4}\s+(.+)$", txt)
    if m:
        return m.group(1).strip()

    return None


def extract_reference(txt: str) -> str | None:
    # TARJREFERENCIA 74518995275208389346204
    m = re.search(r"TARJREFERENCIA\s+([0-9]+)", txt)
    return m.group(1) if m else None


def parse_pattern8(line: str) -> dict | None:
    if not line:
        return None

    txt = normalize_narrative(line)

    if not is_pattern8(txt):
        return None

    merchant = extract_merchant(txt)
    last4 = extract_last4(txt)
    date = extract_date(txt)
    auth = extract_auth(txt)
    reason_code = extract_reason_code(txt)
    reason = extract_reason(txt)
    ref = extract_reference(txt)

    return {
        "transaction_type": "CARD_CHARGEBACK",
        "direction": "INCOMING",
        "merchant": merchant,
        "card_last_digits": last4,
        "authorization_code": auth,
        "transaction_date": date,
        "chargeback_reason_code": reason_code,
        "chargeback_reason": reason,
        "network_reference": ref
    }


if __name__ == "__main__":
    pass
