# routes to respective parsers

from banknarrativeparser.parsers.disbursement.disb_parser import parse_disbursement_narrative,is_disbursement_narrative
from banknarrativeparser.parsers.fundsTransfer.fundsTrans_parser import parse_funds_transfer_frmdep,is_funds_transfer_frmdep
from banknarrativeparser.parsers.vendorpay.vp_parser import parse_vendor_pay_narrative,is_vendor_pay_narrative
from banknarrativeparser.parsers.vendorpymt.vpymt_parser import parse_vendor_payment_rmr, parse_vendor_payment_remittance,is_vendor_payment_remittance,is_vendor_payment_rmr
from banknarrativeparser.parsers.avidpay.avidp_check_parser import parse_avidpay_check,is_avidpay_check
from banknarrativeparser.parsers.avidpay.avidp_gen_parser import parse_avidpay_generic,is_avidpay_generic
from banknarrativeparser.parsers.misc.cardp import parse_card_payment,is_card_payment
from banknarrativeparser.parsers.misc.invo import parse_invoice_reference,is_invoice_reference
from banknarrativeparser.parsers.misc.webt import parse_web_transfer,is_web_transfer
from banknarrativeparser.parsers.remittance.remi import parse_remittance_advice,is_remittance_advice
from banknarrativeparser.parsers.merchref.merch_ref_parser import parse_merchant_reference,is_merchant_reference
from banknarrativeparser.parsers.paypal.paypal import parse_paypal,classify_paypal
from banknarrativeparser.parsers.processor_eft.peft import parse_processor_eft,is_processor_eft
from banknarrativeparser.parsers.directdebit.directdeb import parse_direct_debit,is_direct_debit
from banknarrativeparser.parsers.LAT_AM.LAT_AM_Entry import LATAM_parse,is_LATAM

from banknarrativeparser.parsers.wire.wire_parser import wire_parser,is_wire
from banknarrativeparser.parsers.ach.ach_parser import ach_parser,is_ach
from banknarrativeparser.parsers.swift.swift_parser import swift_parser,is_swift

from banknarrativeparser.parsers.generic.all_parser import all_parser

from banknarrativeparser.key_engine.key_detector import KeyDetector
from banknarrativeparser.routines import routine1
from banknarrativeparser.util import normalize_spaces

key_detector = KeyDetector()

def route_to_parser(narr: str):
    
    # I call key detector to fix keys before delimiter based parsing
    rewritten_narr, hitl = key_detector.rewrite(normalize_spaces(narr))
    
    # if a new key is found.
    if hitl: routine1(hitl)

    if is_wire(narr):
        res = wire_parser(rewritten_narr)
        res["RAW"] = narr
        return res, "wire"

    if is_ach(narr):
        res = ach_parser(rewritten_narr)
        res["RAW"] = narr
        return res, "ach"

    if is_swift(narr):
        res = swift_parser(rewritten_narr)
        res["RAW"] = narr
        return res, "swift"
    
    #  LATAM 
    if is_LATAM(narr) is not None:
        return LATAM_parse(narr), "LATAM"

    #  Paypal
    if classify_paypal(narr) is not None:
        return parse_paypal(narr), "PAYPAL"

    #  Disbursement 
    if is_disbursement_narrative(narr):
        return parse_disbursement_narrative(narr), "disbursement"

    #  Funds transfer 
    if is_funds_transfer_frmdep(narr):
        return parse_funds_transfer_frmdep(narr), "fundstr"

    #  Vendor payments 
    if is_vendor_payment_remittance(narr):
        return parse_vendor_payment_remittance(narr), "vpay_remit"

    if is_vendor_payment_rmr(narr):
        return parse_vendor_payment_rmr(narr), "vpymt"

    if is_vendor_pay_narrative(narr):
        return parse_vendor_pay_narrative(narr), "vpay"

    #  AvidPay 
    if is_avidpay_check(narr):
        return parse_avidpay_check(narr), "avp_check"

    if is_avidpay_generic(narr):
        return parse_avidpay_generic(narr), "avp_gen"

    #  Card 
    if is_card_payment(narr):
        return parse_card_payment(narr), "card"

    #  Invoice / Web 
    if is_invoice_reference(narr):
        return parse_invoice_reference(narr), "invo"

    if is_web_transfer(narr):
        return parse_web_transfer(narr), "webt"

    #  Processor / EFT 
    if is_processor_eft(narr):
        return parse_processor_eft(narr), "peft"

    #  Remittance / Merchant 
    if is_remittance_advice(narr):
        return parse_remittance_advice(narr), "remi"

    if is_merchant_reference(narr):
        return parse_merchant_reference(narr), "merch"

    #  Direct Debit 
    if is_direct_debit(narr):
        return parse_direct_debit(narr), "ddbt"


    res = all_parser(rewritten_narr)
    res["RAW"] = narr
    return res, "generic"
