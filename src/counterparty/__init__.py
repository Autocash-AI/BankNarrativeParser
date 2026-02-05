from counterparty.route import route_to_parser
from counterparty.extraction.extract_payer_payee import extract_payor_payee
from counterparty.util import normalize_spaces

def get_counterparty(narrative: str, amount: float = None) -> dict:
    
    if not narrative:
        return {
            "parsed": {},
            "ctpty": {"payer": None,"payee": None,"amount": amount,"counterparty": None
            }
        }
    
    parsed_result, parser_type = route_to_parser(narrative)
    
    extraction_result = extract_payor_payee(
        parsed=parsed_result,
        amount=amount,
        narrative=narrative
    )
    
    final_result = {
        "parsed": parsed_result,
        "ctpty": extraction_result
    }

    final_result["parsed"]["parser_type"] = parser_type
    
    return final_result
