from banknarrativeparser.route import route_to_parser
from banknarrativeparser.extraction.extract_payer_payee import extract_payor_payee
from banknarrativeparser.util import normalize_spaces
from typing import Optional

class BankNarrativeParser:
    """A parser for bank narratives to extract metadata and counterparties."""

    def parse(self, narrative: str) -> dict:
        """Parses the narrative using the appropriate parser (ach, wire, etc).

        Args:
            narrative: The raw bank narrative string.

        Returns:
            A dictionary containing parsed metadata, extracting specific fields
            based on the narrative format. The 'RAW' input is excluded.
        """
        parsed_result, parser_type = route_to_parser(narrative)
        
        result = parsed_result.copy()
        result["parser_type"] = parser_type
        
        # Remove RAW
        if "RAW" in result:
            del result["RAW"]
        if "raw" in result:
            del result["raw"]
            
        return result

    def get_counterparties(self, narrative: str, amount: Optional[float] = None) -> dict:
        """Extracts counterparties from the narrative.

        Args:
            narrative: The raw bank narrative string.
            amount: The transaction amount (optional), used for inference.

        Returns:
            A dictionary containing:
                - payer: The payer entity name (if found)
                - payee: The payee entity name (if found)
                - counterparty: The inferred counterparty
                - reason: The logic rule used for inference
            The 'amount' field is excluded from the return value.
        """
        
        parsed_result, parser_type = route_to_parser(narrative)
        
        extraction_result = extract_payor_payee(
            parsed=parsed_result,
            amount=amount,
            narrative=narrative
        )
        
        # Removeing amount from result
        if "amount" in extraction_result:
            del extraction_result["amount"]
            
        return extraction_result
