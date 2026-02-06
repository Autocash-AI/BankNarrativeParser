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


pattern5 = re.compile(
    r"^DB.*RV",
    re.IGNORECASE
)


def is_pattern5(line: str) -> bool:
    if not line:
        return False
    return bool(pattern5.search(normalize_narrative(line)))


def parse_pattern5(line: str) -> dict | None:
    if not line:
        return None
    
    txt = normalize_narrative(line)

    if not is_pattern5(txt):
        return None

    # capture last numeric token
    ref = None
    nums = re.findall(r"[0-9]+", txt)
    if nums:
        ref = nums[-1]

    return {
        "transaction_type": "INTERNAL_REVERSAL",
        "entry_side": "DEBIT",
        "is_reversal": True,
        "ledger_bucket": "CF",
        "posting_scope": "INTERNAL",
        "reference_id": ref,
        "ENTITY": None
    }


if __name__ == "__main__":
    pass
