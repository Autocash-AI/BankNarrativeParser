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


# ========================
# IDENTIFICATION PATTERNS
# ========================
pattern4_qrs = re.compile(
    r"^PIX QRS",
    re.IGNORECASE
)

pattern4_qrcode = re.compile(
    r"PIX.*QR CODE|PIX-RECEB|PIX-ENVIADO|PIX-RECEBIMENTO|PIX DEVOLVID",
    re.IGNORECASE
)


def is_pattern4(line: str) -> bool:
    if not line:
        return False
    txt = normalize_narrative(line)
    return bool(pattern4_qrs.search(txt) or pattern4_qrcode.search(txt))


# ========================
# QRS PAYLOAD PARSER
# ========================
def parse_qrs_payload(txt: str):
    raw = txt.replace("PIX QRS", "").strip()
    tokens = raw.split()

    # 1️⃣ counterparty
    name = []
    idx = 0
    for idx, t in enumerate(tokens):
        if re.search(r"[0-9/]", t):
            break
        name.append(t)
    counterparty = " ".join(name).strip() if name else None

    # 2️⃣ movement date
    movement_date = None
    for t in tokens:
        m = re.match(r"[A-Z]*([0-9]{2})/([0-9]{2})", t)
        if m:
            dd, mm = m.groups()
            movement_date = f"2025-{mm}-{dd}"
            break

    # 3️⃣ capture the code + the aux
    remainder = tokens[len(name):]

    codes = [x for x in remainder if not re.search(r"[A-Z]*[0-9]{2}/[0-9]{2}", x)]

    pix_reference_code = codes[0] if len(codes) >= 1 else None
    pix_aux_code = codes[1] if len(codes) >= 2 else None

    return counterparty, movement_date, pix_reference_code, pix_aux_code


# ========================
# MAIN PARSER
# ========================
def parse_pattern4(line: str) -> dict | None:
    if not line:
        return None

    txt = normalize_narrative(line)

    # ----------------------
    # QRS static pattern
    # ----------------------
    if pattern4_qrs.search(txt):
        counterparty, movement_date, ref, aux = parse_qrs_payload(txt)
        return {
            "ENTITY": counterparty,
            "payment_system": "PIX",
            "direction": None,
            "payment_method": "PIX_QR_STATIC",
            "transaction_type": "INSTANT_PAYMENT",
            "movement_date": movement_date,
            "pix_reference_code": ref,
            "pix_aux_code": aux
        }

    # ----------------------
    # QR directional or devolvido
    # ----------------------
    if pattern4_qrcode.search(txt):

        if "DEVOLVID" in txt:
            direction = "REVERSAL"
        elif "RECEB" in txt:
            direction = "INCOMING"
        elif "ENVIADO" in txt:
            direction = "OUTGOING"
        else:
            direction = None

        payment_method = "QR_CODE" if "QR CODE" in txt else None

        return {
            "ENTITY": None,
            "payment_system": "PIX",
            "direction": direction,
            "payment_method": payment_method,
            "transaction_type": "INSTANT_PAYMENT",
            "movement_date": None,
            "pix_reference_code": None,
            "pix_aux_code": None
        }

    return None


if __name__ == "__main__":
    pass
