import re

def normalize_narrative(line: str) -> str:
    if not line:
        return ""
    line = line.lstrip(",")
    line = re.sub(r"[,\s]+$", "", line)
    line = re.sub(r"\s+", " ", line)
    return line.strip().upper()


VENDORPYMT_RMR_RE = re.compile(
    r"VENDORPYMT\s*RMR\*IV\*.+\*\*\d",
)

VENDORPYMT_REMIT_RECOGNISE_RE = re.compile(
    r"VENDORPYMT.*RMR\*IV\*"
)



def is_vendor_payment_rmr(line: str) -> bool:
    return bool(VENDORPYMT_RMR_RE.search(normalize_narrative(line)))


def is_vendor_payment_remittance(line: str) -> bool:
    norm = normalize_narrative(line)
    if not norm:
        return False

    # exclude invoice+amount version (handled elsewhere)
    if "**" in norm:
        return False

    return bool(VENDORPYMT_REMIT_RECOGNISE_RE.search(norm))



# PARSER REGEX
VENDORPYMT_RMR_PARSE_RE = re.compile(
    r"""
    ^
    (?P<COUNTERPARTY_NAME>.+?)
    [\s\-]*
    VENDORPYMT\s*RMR(?:\*IV\*)
    (?P<INVOICE_NO>(?:[A-Z0-9]+\s?)+)
    \*\*
    (?P<AMOUNT>(?:\d+\s+)?\d+(?:\.\d{2})?)
    """,
    re.VERBOSE
)



VENDORPYMT_REMIT_PARSE_RE = re.compile(
    r"""
    ^
    (?P<COUNTERPARTY_NAME>.+?)
    \s+VENDORPYMT\b
    \s*
    (?P<META_BLOCK>.*?)       
    \s*
    RMR\*IV\*
    (?P<REMIT_BLOCK>.+)
    $
    """,
    re.VERBOSE
)



INVOICE_RE = re.compile(r"RMR(?:\*IV\*|IV)([A-Z0-9]+)")
AMOUNT_RE  = re.compile(r"\*\*\s*([\d ]+(?:\.\d{2})?)")


# PARSER
def parse_vendor_payment_rmr(line: str) -> dict:
    norm = normalize_narrative(line).rstrip("\\")
    m = VENDORPYMT_RMR_PARSE_RE.search(norm)
    if not m:
        return {
            "RAW": line,
            "META": norm,
            "ERROR": "VENDORPYMT_RMR_PARSE_FAILED"
        }

    raw_amt = m.group("AMOUNT").replace(" ", "")
    if "." not in raw_amt and len(raw_amt) > 2:
        amt = f"{int(raw_amt[:-2])}.{raw_amt[-2:]}"
    else:
        amt = raw_amt

    invoice_ids = m.group("INVOICE_NO").split()

    return {
        "RAW": line,
        "ENTITY": m.group("COUNTERPARTY_NAME").rstrip("- "),
        "TRANS_TYPE": "VENDOR_PAYMENT_RMR",
        "INVOICE_NO": invoice_ids,
        "AMOUNT": amt,
    }



def parse_vendor_payment_remittance(line: str) -> dict:
    norm = normalize_narrative(line)

    m = VENDORPYMT_REMIT_PARSE_RE.search(norm)
    if not m:
        return {
            "RAW": line,
            "META": norm,
            "ERROR": "VENDORPYMT_REMIT_PARSE_FAILED"
        }

    remit_block = m.group("REMIT_BLOCK")

    remit_ids = re.findall(r"\b\d{4,}\b", remit_block)

    return {
        "RAW": line,
        "ENTITY": m.group("COUNTERPARTY_NAME").strip(),
        "TRANS_TYPE": "VENDOR_PAYMENT_REMITTANCE",
        "VENDOR_META": m.group("META_BLOCK").strip(),
        "REMITTANCE_IDS": remit_ids,
        "RAW_REMIT_BLOCK": remit_block
    }



if __name__=='__main__':
    pass