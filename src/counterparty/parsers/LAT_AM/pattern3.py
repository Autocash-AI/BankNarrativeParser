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


pattern3 = re.compile(
    r"^/?(MERCHANT PAYMENT|TRANSACTION REVERSAL)\s*RRN",
    re.IGNORECASE
)


def is_pattern3(line: str) -> bool:
    if not line:
        return False
    return bool(pattern3.search(normalize_narrative(line)))


pattern3_parse = re.compile(
    r"""
    ^/?(MERCHANT\ PAYMENT|TRANSACTION\ REVERSAL)\s*RRN\ 
    ([0-9]+)              # rrn
    \s+
    ([0-9]+)              # merchant id
    \s+
    ([0-9]{6})$           # ddmmyy
    """,
    re.IGNORECASE | re.VERBOSE
)


def parse_pattern3(line: str) -> dict | None:
    if not line:
        return None

    line_n = normalize_narrative(line)
    match = pattern3_parse.match(line_n)
    if not match:
        return None

    prefix, rrn, merchant_id, ddmmyy = match.groups()

    # convert DDMMYY => YYYY-MM-DD
    day   = ddmmyy[0:2]
    month = ddmmyy[2:4]
    year  = "20" + ddmmyy[4:6]
    date_fmt = f"{year}-{month}-{day}"

    # dynamic classification:
    if prefix == "TRANSACTION REVERSAL":
        category = "MERCHANT_REVERSAL"
        direction = "INCOMING"
    else:
        category = "MERCHANT_PAYMENT"
        direction = "OUTGOING"

    return {
        "transaction_category": category,
        "direction": direction,
        "rrn": rrn,
        "merchant_id": merchant_id,
        "processing_date": date_fmt
    }


if __name__ == "__main__":
    pass
