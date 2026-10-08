import re
from typing import Optional, Tuple

# Bank-specific counterparty rules, run in extract_payor_payee only after the generic payer/payee rules find no name (lowest priority).
# They read the bank's own narrative layout directly, so they need to know the bank (taken from the account name
# prefix: PNC / US / KEY) and the direction (credit/debit). First match wins, in the order below.
#
#   PNC      1  ACH credit/debit received   "Comp Name"  (SEC: CIE bill-pay -> "Cust ID")
#            2  ACH credit return / detail  "RECEIVER NAME"
#            3  Instant payment (RTP)       "ULT DEBTOR NAME", else "DEBTOR NAME"
#            4  Incoming wire               "DEBTOR"
#            5  Outgoing wire (dom./intl)   "CREDITOR"
#   US Bank  6  ACH credit/debit            "COMPANY NAME"
#            7  Incoming Fedwire            "DEBTOR"
#            8  Outgoing Fedwire / FX       "CREDITOR"
#   KeyBank  9  ACH credit                  first 16 characters of the narrative
#            10 Incoming wire               "ORG="
#            11 Outgoing wire               "BNF="
#   Fixed    12 PNC Merchant, FDMS settlement, PNC loan payments and analysis fees -> FIXED_NAMES below.

# Fixed counterparty names: (bank or None for any, narrative pattern, name). First match wins, before the rules.
FIXED_NAMES = [
    ("PNC", r"^PNC MERCHANT (DEPOSIT|DISCOUNT|CHARGEBACK|ADJUSTMENT)", "PNC Merchant"),
    (None, r"\bFDMS\b", "FDMS"),
    ("PNC", r"^PNC BANK-? ?NJ (LOAN|FEE) PMTS", "PNC Loan"),
    ("PNC", r"ACCOUNT ANALYSIS|ANALYSIS (SERV|CHARGE|FEE)", "PNC Analysis Fee"),
]

BANK_RULES = {
    1: "ACH credit/debit received",
    2: "ACH credit return / detail",
    3: "Instant payment (RTP)",
    4: "Incoming wire",
    5: "Outgoing wire (domestic and international)",
    6: "ACH credit/debit",
    7: "Incoming Fedwire",
    8: "Outgoing Fedwire / FX",
    9: "ACH credit",
    10: "Incoming wire",
    11: "Outgoing wire",
    12: "Fixed counterparty names",
}

# a field value ends where the next "LABEL:" starts (or at end of narrative)
_END = r"(?=\s+[A-Z][A-Za-z /#.]*:|\s*$)"
_WIRE_END = r"(?=\s+AC/|\s+[A-Z][A-Z /]{1,10}:|\s*$)"  # AC/ account, or next label (ADDR:, CTY:, DB BNK: ...)
_LEGAL_SUFFIX = re.compile(r"^(INC|LLC|LTD|CORP|CO|LP|LLP|PLC|NA|N\.A)\b", re.I)


def _field(narrative: str, label: str, end: str = _END) -> Optional[str]:
    m = re.search(rf"{label}\s*(.*?){end}", narrative)
    return m.group(1).strip() or None if m else None


def _clean(name: Optional[str]) -> Optional[str]:
    if not name:
        return None
    name = re.sub(r"\s+", " ", name).strip(" ,;")
    return name or None


def _fedwire_party(raw: Optional[str]) -> Optional[str]:
    """Fedwire party text is '<account> <NAME>, <ADDRESS...>' - drop the account and the address."""
    if not raw:
        return None
    raw = re.sub(r"^[\d\-/ ]{6,}\s+(?=\D)", "", raw)  # leading account number (digits, dashes)
    raw = re.sub(r"^(?=[A-Z0-9]*\d)[A-Z0-9]{10,}\s+(?=\S)", "", raw)  # leading IBAN / alphanumeric account
    raw = re.sub(r",?\s*NO ADDRESS GIVEN.*$", "", raw, flags=re.I)
    parts = [p.strip() for p in raw.split(",")]
    name = parts[0]
    for p in parts[1:]:  # "Foo, Inc." keeps its legal suffix
        if _LEGAL_SUFFIX.match(p):
            name += ", " + re.split(r"\s", p, 1)[0]
        else:
            break
    return name


def bank_of(account_name: Optional[str]) -> Optional[str]:
    """PNC / US / KEY from the account name prefix, or None."""
    m = re.match(r"\s*(PNC|US|KEY)", str(account_name or ""), re.I)
    return m.group(1).upper() if m else None


def direction_of(amount: Optional[float], direction: Optional[str] = None) -> Optional[str]:
    """'credit' or 'debit', from an explicit direction or else the sign of the amount."""
    if direction:
        return direction.lower()
    if amount is None:
        return None
    return "credit" if amount > 0 else "debit" if amount < 0 else None


def derive_bank_counterparty(
    bank: Optional[str], direction: Optional[str], narrative: str, bai_description: Optional[str] = None
) -> Tuple[Optional[str], Optional[int]]:
    """Return (counterparty name, rule number from BANK_RULES) or (None, None).

    A rule can match without finding a name, which returns (None, rule number).
    bank is PNC / US / KEY; direction is 'credit' or 'debit'.
    """
    n = re.sub(r"\s+", " ", str(narrative or "")).strip()
    up = n.upper()
    desc = f"{bai_description or ''} {n}".upper()

    for fixed_bank, pat, name in FIXED_NAMES:
        if (fixed_bank is None or fixed_bank == bank) and re.search(pat, n, re.I):
            return name, 12

    if bank == "PNC":
        if up.startswith(("ACH CREDIT RECEIVED", "ACH DEBIT RECEIVED")):
            if re.search(r"SEC: CIE\b", n):
                return _clean(_field(n, "Cust ID:", r"(?=\s+Desc:|\s*$)")), 1
            return _clean(_field(n, "Comp Name:", r"(?=\s+Comp ID:|\s*$)")), 1
        if up.startswith(("ACH CREDIT RETURN DETAIL", "ACH CREDIT DETAIL", "ACH DEBIT DETAIL", "ACH DEBIT RETURN DETAIL")):
            return _clean(_field(n, "RECEIVER NAME:", r"(?=\s+(?:DESC|COMP NAME|BATCH ID):|\s*$)")), 2
        if up.startswith("INSTANT PAYMENT") and direction == "credit":
            ult = _field(n, "ULT DEBTOR NAME:", r"(?=\s+(?:ADDITIONAL INFORMATION|POST DATE/TIME|UETR):|\s*$)")
            if ult:
                return _clean(ult), 3
            return _clean(_field(n, "DEBTOR NAME:", r"(?=\s+DEBTOR ACCOUNT:|\s*$)")), 3
        if "WIRE TRANSFER" in up:
            if direction == "credit":
                return _clean(_field(n, r"\bDEBTOR:", _WIRE_END)), 4
            return _clean(_field(n, r"\bCREDITOR:", _WIRE_END)), 5

    elif bank == "US":
        if up.startswith("ACH "):
            return _clean(_field(n, "COMPANY NAME:", r"(?=\s+SEC CODE:|\s*$)")), 6
        if up.startswith("INCOMING FEDWIRE"):
            return _clean(_fedwire_party(_field(n, r"\bDEBTOR:", r"(?=\s+DEBTOR AGENT:|\s*$)"))), 7
        if up.startswith(("CUSTOMER INITIATED OUTGOING FEDWIRE", "OUTGOING FX")) or "OUTGOING FEDWIRE" in up:
            raw = _field(n, r"\bCREDITOR:", r"(?=\s+(?:CREDITOR REF|CREDITOR AGENT|REMITTANCE|DEBTOR)\b|\s*$)")
            return _clean(_fedwire_party(raw)), 8

    elif bank == "KEY":
        key_end = r"(?=\s+[A-Z][A-Z0-9/ ]{1,12}=|\s*$)"
        if "WIRE" in desc:
            if direction == "credit":
                return _clean(_field(n, r"\bORG=", key_end)), 10
            return _clean(_field(n, r"\bBNF=", key_end)), 11
        if "ACH" in desc and direction == "credit":
            return _clean(n[:16]), 9

    return None, None
