import re
import json


def normalize_narrative(line: str) -> str:
    if not line:
        return ""
    line = line.upper()
    line = re.sub(r"[\\|,]+", " ", line)
    line = re.sub(r"\s+", " ", line)
    return line.strip()


pattern9 = re.compile(
    r"ACH\s+CREDIT.*CITIDIRECT",
    re.IGNORECASE
)


def is_pattern9(line: str) -> bool:
    if not line:
        return False
    txt = normalize_narrative(line)
    return bool(pattern9.search(txt))


def extract_our_ref(txt: str) -> str | None:
    m = re.search(r"OUR REF\s*#\s*([0-9]+)", txt)
    return m.group(1) if m else None


def extract_aba(txt: str) -> str | None:
    m = re.search(r"RECEIVING BANK\s*#\s*([0-9]+)", txt)
    return m.group(1) if m else None


def extract_receiver_account(txt: str) -> str | None:
    m = re.search(r"RECEIVER\s*A/C\s*#\s*([0-9]+)", txt)
    return m.group(1) if m else None


def extract_receiver_name(txt: str) -> str | None:
    # RECEIVER; GLAMOUR GOODS CORP.
    m = re.search(r"RECEIVER;\s+(.+?)\s+(ADDENDA|RECEIVING|OUR REF|CREDIT|PT/|$)", txt)
    if m:
        return m.group(1).strip()
    return None


def extract_addenda(txt: str) -> str | None:
    # ADDENDA INFORMATION AMAZON/BTN/535428119865
    m = re.search(r"ADDENDA INFORMATION\s+(.+)$", txt)
    if m:
        return m.group(1).strip()
    return None


def parse_pattern9(line: str) -> dict | None:
    if not line:
        return None

    txt = normalize_narrative(line)

    if not is_pattern9(txt):
        return None

    our_ref = extract_our_ref(txt)
    aba = extract_aba(txt)
    acct = extract_receiver_account(txt)
    name = extract_receiver_name(txt)
    addenda = extract_addenda(txt)

    return {
        "transaction_type": "ACH_CREDIT",
        "direction": "OUTGOING",
        "originating_platform": "CITIDIRECT",
        "receiving_bank_aba": aba,
        "receiver_account": acct,
        "receiver_name": name,
        "addenda_information": addenda,
        "our_reference": our_ref
    }


if __name__ == "__main__":
    pass
