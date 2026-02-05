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


pattern6 = re.compile(
    r"^066|^MOV POS",
    re.IGNORECASE
)


def is_pattern6(line: str) -> bool:
    if not line:
        return False
    return bool(pattern6.search(normalize_narrative(line)))


def parse_mov_pos(txt: str) -> dict | None:
    """
    Handles: MOV POS IVALEY6380 4747130055
    → merchant: IVALEY
    → merchant_id: 4747130055
    """

    if not txt.startswith("MOV POS"):
        return None

    parts = txt.split()

    # must have at least: MOV POS <merchant+num> <merchant_id>
    if len(parts) < 4:
        return None

    merchant_token = parts[2]
    merchant_id = None

    # last token must be merchant id (large numeric)
    tail = parts[-1]
    if re.match(r"^[0-9]{6,}$", tail):
        merchant_id = tail

    # strip trailing digits from merchant_token
    m = re.match(r"([A-Z]+)", merchant_token)
    merchant = m.group(1) if m else merchant_token

    return {
        "transaction_type": "CARD_PAYMENT",
        "direction": "OUTGOING",
        "channel": "POS",
        "merchant": merchant,
        "merchant_id": merchant_id,
        "card_type": "DEBIT",
        "card_network": None,
        "is_ecommerce": False,
        "is_domestic": True
    }


def parse_pattern6(line: str) -> dict | None:
    if not line:
        return None

    txt = normalize_narrative(line)

    if not is_pattern6(txt):
        return None

    # MOV POS mode (new feature)
    if txt.startswith("MOV POS"):
        return parse_mov_pos(txt)

    # ===== existing 066 mode below =====
    bank_txn_code = "066"
    direction = "OUTGOING"

    # POS indicator (with or without dots)
    pos_match = bool(re.search(r"P\.?O\.?S", txt))

    # SERVICE PAYMENT POS
    if "PAGO SERVICIO" in txt:
        return {
            "transaction_type": "SERVICE_PAYMENT",
            "direction": direction,
            "channel": "POS",
            "payment_instrument": "CARD",
            "bank_txn_code": bank_txn_code
        }

    # E-COMMERCE
    if "E-COMMERCE" in txt:
        return {
            "transaction_type": "CARD_PAYMENT",
            "direction": direction,
            "card_type": "DEBIT",
            "channel": "ECOMMERCE",
            "card_network": None,
            "is_ecommerce": True,
            "is_domestic": True,
            "bank_txn_code": bank_txn_code
        }

    # POS + BANCARD
    if pos_match and "BANCARD" in txt:
        return {
            "transaction_type": "CARD_PAYMENT",
            "direction": direction,
            "card_type": "DEBIT",
            "channel": "POS",
            "card_network": "BANCARD",
            "is_ecommerce": False,
            "is_domestic": True,
            "bank_txn_code": bank_txn_code
        }

    # generic POS
    if pos_match:
        return {
            "transaction_type": "CARD_PAYMENT",
            "direction": direction,
            "card_type": "DEBIT",
            "channel": "POS",
            "card_network": None,
            "is_ecommerce": False,
            "is_domestic": True,
            "bank_txn_code": bank_txn_code
        }

    return None


if __name__ == "__main__":
    pass
