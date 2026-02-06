import re
import json


def normalize_narrative(line: str) -> str:
    if not line:
        return ""
    line = line.upper()
    line = re.sub(r"[\\|,]+", " ", line)
    line = re.sub(r"\s+", " ", line)
    return line.strip()


pattern10 = re.compile(
    r"/IDCODE/",
    re.IGNORECASE
)


def is_pattern10(line: str) -> bool:
    if not line:
        return False
    txt = normalize_narrative(line)
    return bool(pattern10.search(txt))


def extract_payer_id(txt: str) -> str | None:
    m = re.search(r"/IDCODE/([A-Z0-9]+)/", txt)
    return m.group(1) if m else None


def extract_collection_code(txt: str) -> str | None:
    m = re.search(r"/COLLEC/([A-Z0-9]+)/", txt)
    return m.group(1) if m else None


def extract_payer_name(txt: str) -> str | None:
    m = re.search(r"/PAYER/([^/]+)/", txt)
    if m:
        return m.group(1).strip()
    return None


def extract_info(txt: str) -> str | None:
    m = re.search(r"/INFO/(.+)$", txt)
    if m:
        return m.group(1).strip()
    return None


def parse_pattern10(line: str) -> dict | None:
    if not line:
        return None

    txt = normalize_narrative(line)

    if not is_pattern10(txt):
        return None

    payer_id = extract_payer_id(txt)
    coll = extract_collection_code(txt)
    name = extract_payer_name(txt)
    info = extract_info(txt)

    return {
        "transaction_type": "ACH_COLLECTION",
        "direction": "INCOMING",
        "payer_name": name,
        "payer_id": payer_id,
        "collection_code": coll,
        "info_text": info
    }


if __name__ == "__main__":
    pass
