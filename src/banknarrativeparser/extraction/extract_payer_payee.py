import re
from typing import Any, Dict, Optional
from banknarrativeparser.util import norm2
from banknarrativeparser.extraction.infer_counterparty import infer_counterparty
from banknarrativeparser.extraction.clean import getEntity


# these keys will be used to tell who is the payer, who is the payee after parsing.
PAYER_KEYS = [
    "ordering customer","sending co name","ordering cust","company name","sender name","debtor name","from account","comp name","entry desc","orig co name","from acct","originator","debtor","sender","comp name","orig","org"]

PAYEE_KEYS = [
    "individual or receiving company name","receiver name","creditor name","customer name","ulti bene","recv name","beneficiary","cust name","creditor","receiver","bn f","bnf","bn"]


COUNTERPARTY_KEYS = [
    "entity", "counterparty_name", "related entity", "related party", "from_account", "to_account", "entity_name", "counterparty", "original_counterparty"
]


def is_account_like(v: str) -> bool:
    """Checks if a string looks like a bank account number (mostly digits/non-alpha).

    Args:
        v: The string to check.

    Returns:
        True if the string looks like an account number, False otherwise.
    """
    if not v:
        return False

    has_digit = bool(re.search(r"\d", v))
    mostly_non_alpha = len(re.findall(r"[A-Z]", v)) <= 2
    return has_digit and mostly_non_alpha


def _finalize(payer, payee, amount, narrative, reason):
    """Finalizes the counterparty extraction result.

    Args:
        payer: The extracted payer name.
        payee: The extracted payee name.
        amount: The transaction amount.
        narrative: The original narrative.
        reason: The reason string explaining the extraction logic.

    Returns:
        A dictionary containing the final extracted data.
    """
    # remove noise and get entity name using my spacy based cleaner
    payer = getEntity(payer) or payer
    payee = getEntity(payee) or payee

    return {
        "payer": payer,
        "payee": payee,
        "counterparty": infer_counterparty(payer, payee, amount, narrative),
        "amount": amount,
        "reason": reason,
    }


def extract_payor_payee(
    parsed: Dict[str, Any],
    amount: Optional[float] = None,
    narrative: Optional[str] = None,
) -> Dict[str, Any]:
    """Extracts payer and payee from parsed narrative data using various rules.

    Args:
        parsed: The dictionary of parsed narrative fields.
        amount: The transaction amount (optional).
        narrative: The original narrative string (optional).

    Returns:
        A dictionary with keys 'payer', 'payee', 'counterparty', 'amount', and 'reason'.
    """

    data = {k.lower(): v for k, v in parsed.items()}

    payer = None
    payee = None
    payer_source_key = None
    payee_source_key = None


    # Rule 1: Structured explicit payer / payee fields
    for k in PAYER_KEYS:
        if k in data:
            v = data[k]
            payer = norm2(v.get("value") if isinstance(v, dict) else v)
            if payer:
                payer_source_key = k
                break

    for k in PAYEE_KEYS:
        if k in data:
            v = data[k]
            payee = norm2(v.get("value") if isinstance(v, dict) else v)
            if payee:
                payee_source_key = k
                break


    # Rule 2: ACH RECEIVED override
    ach_text = norm2(narrative) or norm2(data.get("raw")) or ""
    ach_u = ach_text.upper()

    if "ACH" in ach_u and "RECEIVED" in ach_u:
        cust = norm2(data.get("cust name"))
        comp = norm2(data.get("comp name"))

        # if cust and comp:
        if "DEBIT" in ach_u:
            return _finalize(cust, comp, amount, narrative, "Inferred from ACH Received Debit transaction type")
        if "CREDIT" in ach_u:
            return _finalize(comp, cust, amount, narrative, "Inferred from ACH Received Credit transaction type")
            
    # Rule 2b: ACH Disbursement Funding Debit
    if "ACH" in ach_u and "DISBURSEMENT" in ach_u and "DEBIT" in ach_u:
        comp = norm2(data.get("comp name") or data.get("sending co name"))
        recv = norm2(data.get("recv name") or data.get("receiver name") or data.get("cust name"))

        # if comp and recv:
            # Customer paid out → customer is payer, company is payee
        return _finalize(recv, comp, amount, narrative, "Inferred from ACH Disbursement Funding Debit transaction type")

    # Rule 2c: ACH credit return - money comes back from the original receiver, so they are the payer.
    if "ACH" in ach_u and "RETURN DETAIL" in ach_u:
        recv = norm2(data.get("receiver name"))
        if recv:
            return _finalize(recv, None, amount, narrative, "Inferred from ACH Credit Return: receiver is payer")

    # Rule 3: Both roles known
    if payer and payee:
        return _finalize(payer, payee, amount, narrative, f"Found explicit payer (key: {payer_source_key}) and explicit payee (key: {payee_source_key})")

    # Rule 4: Only one role known
    if payer and not payee:
        return _finalize(payer, None, amount, narrative, f"Found explicit payer (key: {payer_source_key})")

    if payee and not payer:
        return _finalize(None, payee, amount, narrative, f"Found explicit payee (key: {payee_source_key})")

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
                    return _finalize(ctpty, None, amount, narrative, "Inferred Counterparty from PIX Credit text")

                return _finalize(None, ctpty, amount, narrative, "Inferred Counterparty from PIX Debit text")

    # Rule 6: Generic counterparty fields
    ctpty = None
    ctpty_key = None
    for k in COUNTERPARTY_KEYS:
        if k in data:
            ctpty = norm2(data[k])
            if ctpty:
                ctpty_key = k
                break

    if ctpty:
        reason_base = f"Found generic counterparty field (key: {ctpty_key})"
        if amount is not None and amount < 0:
            return _finalize(None, ctpty, amount, narrative, f"{reason_base}, inferred as Payee (Amount Negative)")

        if amount is not None and amount >= 0:
            return _finalize(ctpty, None, amount, narrative, f"{reason_base}, inferred as Payer (Amount Positive)")

        return _finalize(None, ctpty, amount, narrative, reason_base)

    # Rule 7: Amount-only inference
    if amount is not None:
        if amount < 0:
            return _finalize(None, None, amount, narrative, "Inferred undefined Payee based on negative amount")

        return _finalize(None, None, amount, narrative, "Inferred undefined Payer based on positive amount")

    # Rule 8: Nothing resolved
    return _finalize(None, None, amount, narrative, "No counterparty could be inferred from narrative or amount")
