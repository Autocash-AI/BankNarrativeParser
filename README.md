# BankNarrativeParser Library

A Python library designed to parse bank transaction narratives and extract key counterparty information (Payer and Payee) with specific logic for various transaction types (ACH, Wire, Check, PIX, etc.).

## Features

*   **Narrative Parsing**: Automatically detects transaction types and extracts structured metadata.
*   **Counterparty Extraction**: Identifies the 'Payer' and 'Payee' from complex narrative strings.
*   **Reasoning**: Provides a `reason` field explaining the logic used for each extraction.
*   **Clean Output**: Returns structured JSON, excluding raw inputs and internal amounts from the final result.

## Installation

You can install this package locally using `pip`.

### For Development (Editable Mode)
Recommended if you plan to modify the code.
```bash
git clone <repository-url>
cd BankNarrativeParser
pip install -e .
```

### Standard Install
```bash
cd BankNarrativeParser
pip install .
```

## Usage

The package provides a main class `BankNarrativeParser`.

```python
from banknarrativeparser import BankNarrativeParser

# 1. Initialize the parser
parser = BankNarrativeParser()

# 2. Define your transaction details
narrative = "WIRE TRANSFER FROM GOOGLE INC"
amount = 100.00  # Optional, helps with inference

# 3. Parse Metadata (removes original RAW text)
parsed_meta = parser.parse(narrative)
print(parsed_meta)

# 4. Extract Counterparties (removes amount, adds reason)
result = parser.get_counterparties(narrative, amount=amount)
print(result)
```

## Output Structure

### get_counterparties Output:
Returns a dictionary containing:
*   `payer`: The name of the payer (if found).
*   `payee`: The name of the payee (if found).
*   `counterparty`: The inferred primary counterparty.
*   `reason`: A descriptive string explaining the rule matched.

**Example:**
```json
{
    "payer": "GOOGLE INC",
    "payee": null,
    "counterparty": "GOOGLE INC",
    "reason": "Found explicit payer (key: ordering customer)"
}
```
