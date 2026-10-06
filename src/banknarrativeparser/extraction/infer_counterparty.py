def infer_counterparty(payer, payee, amount, narrative):
    # Amount sign is authoritative: money in -> payer, money out -> payee.
    # Keywords can mislead, e.g. "ACH CREDIT DETAIL" is an originated (outgoing) credit.
    if amount is not None:
        if amount > 0:
            return payer
        if amount < 0:
            return payee

    text = (narrative or "").upper()

    # if "ACH" in text and "RECEIVED" in text:
    if "ACH" in text:
        if "CREDIT" in text:
            return payer
        if "DEBIT" in text:
            return payee

    return None
