def infer_counterparty(payer, payee, amount, narrative):
    text = (narrative or "").upper()

    # if "ACH" in text and "RECEIVED" in text:
    if "ACH" in text:
        if "CREDIT" in text:
            return payer
        if "DEBIT" in text:
            return payee

    if amount is not None:
        if amount > 0:
            return payer
        if amount < 0:
            return payee

    return None