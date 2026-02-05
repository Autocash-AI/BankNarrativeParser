import re
from typing import Any, Dict, Optional
from counterparty.util import norm2
from counterparty.extraction.infer_counterparty import infer_counterparty
from counterparty.extraction.clean import getEntity


# these keys will be used to tell who is the payer, who is the payee after parsing.
PAYER_KEYS = [
    "ordering customer","sending co name","ordering cust","company name","sender name","debtor name","from account","comp name","entry desc","orig co name","from acct","originator","debtor","sender","comp name","orig","org"]

PAYEE_KEYS = [
    "individual or receiving company name","receiver name","creditor name","customer name","ulti bene","recv name","beneficiary","cust name","creditor","receiver","bn f","bnf","bn"]


COUNTERPARTY_KEYS = [
    "entity", "counterparty_name", "related entity", "related party", "from_account", "to_account", "entity_name", "counterparty", "original_counterparty"
]


def is_account_like(v: str) -> bool:
    if not v:
        return False

    has_digit = bool(re.search(r"\d", v))
    mostly_non_alpha = len(re.findall(r"[A-Z]", v)) <= 2
    return has_digit and mostly_non_alpha


def _finalize(payer, payee, amount, narrative):

    # remove noise and get entity name using my spacy based cleaner
    payer = getEntity(payer) or payer
    payee = getEntity(payee) or payee



    return {
        "payer": payer,
        "payee": payee,
        "counterparty": infer_counterparty(payer, payee, amount, narrative),
        "amount": amount,
    }


def extract_payor_payee(
    parsed: Dict[str, Any],
    amount: Optional[float] = None,
    narrative: Optional[str] = None,
) -> Dict[str, Any]:

    data = {k.lower(): v for k, v in parsed.items()}

    payer = None
    payee = None


    # Rule 1: Structured explicit payer / payee fields
    for k in PAYER_KEYS:
        if k in data:
            v = data[k]
            payer = norm2(v.get("value") if isinstance(v, dict) else v)
            if payer:
                break

    for k in PAYEE_KEYS:
        if k in data:
            v = data[k]
            payee = norm2(v.get("value") if isinstance(v, dict) else v)
            if payee:
                break

    if payer and is_account_like(payer):
        payer = f"BANK({payer})"

    if payee and is_account_like(payee):
        payee = f"BANK({payee})"

    # Rule 2: ACH RECEIVED override
    ach_text = norm2(narrative) or norm2(data.get("raw")) or ""
    ach_u = ach_text.upper()

    if "ACH" in ach_u and "RECEIVED" in ach_u:
        cust = norm2(data.get("cust name"))
        comp = norm2(data.get("comp name"))

        # if cust and comp:
        if "DEBIT" in ach_u:
            return _finalize(cust, comp, amount, narrative)
        if "CREDIT" in ach_u:
            return _finalize(comp, cust, amount, narrative)
            
    # Rule 2b: ACH Disbursement Funding Debit
    if "ACH" in ach_u and "DISBURSEMENT" in ach_u and "DEBIT" in ach_u:
        comp = norm2(data.get("comp name") or data.get("sending co name"))
        recv = norm2(data.get("recv name") or data.get("receiver name") or data.get("cust name"))

        # if comp and recv:
            # Customer paid out → customer is payer, company is payee
        return _finalize(recv, comp, amount, narrative)

    # Rule 3: Both roles known
    if payer and payee:
        return _finalize(payer, payee, amount, narrative)

    # Rule 4: Only one role known
    if payer and not payee:
        return _finalize(payer, None, amount, narrative)

    if payee and not payer:
        return _finalize(None, payee, amount, narrative)

    # Rule 5: PIX inference
    narrative_text = norm2(parsed.get("narrative") or parsed.get("description"))

    if narrative_text and re.search(r"\bPIX\b", narrative_text, re.IGNORECASE):
        m = re.search(
            r"\bPIX(?:\s+QRS|\s+TRANSF|\s+QR)?\s+([A-Z][A-Z\s]{2,})",
            narrative_text.upper(),
        )

        if m:
            ctpty = norm2(m.group(1))
            ctpty = re.sub(r"\s+\d.*$", "", ctpty).strip()

            if ctpty and not is_account_like(ctpty):
                if re.search(r"\b(RECEB|RECEBIDO|CR|CRED)\b", narrative_text.upper()):
                    return _finalize(ctpty, None, amount, narrative)

                return _finalize(None, ctpty, amount, narrative)

    # Rule 6: Generic counterparty fields
    ctpty = None
    for k in COUNTERPARTY_KEYS:
        if k in data:
            ctpty = norm2(data[k])
            if ctpty:
                break

    if ctpty:
        if is_account_like(ctpty):
            ctpty = f"BANK({ctpty})"

        if amount is not None and amount < 0:
            return _finalize(None, ctpty, amount, narrative)

        if amount is not None and amount >= 0:
            return _finalize(ctpty, None, amount, narrative)

        return _finalize(None, ctpty, amount, narrative)

    # Rule 7: Amount-only inference
    if amount is not None:
        if amount < 0:
            return _finalize(None, None, amount, narrative)

        return _finalize(None, None, amount, narrative)

    # Rule 8: Nothing resolved
    return _finalize(None, None, amount, narrative)
