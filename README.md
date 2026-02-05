# Counterparty Extraction Library

A Python library designed to parse financial transaction narratives and extract key counterparty information (Payer, Payee, and Counterparty Name).

## Features

*   **Narrative Parsing**: Automatically detects transaction types (Wire, ACH, Check, etc.).
*   **Entity Extraction**: Identifies the 'Payer' and 'Payee' from complex strings.
*   **Clean Output**: Returns a structured JSON response separating parsing metadata from extraction results.

## Installation

You can install this package locally using `pip`.

### For Development (Editable Mode)
Recommended if you plan to modify the code.
```bash
git clone <repository-url>
cd counterparty
pip install -e .
```

### Standard Install
```bash
cd counterparty
pip install .
```

## Usage

The package provides a simple entry point `get_counterparty`.

```python
from counterparty import get_counterparty

# 1. Define your transaction details
narrative = "WIRE TRANSFER. Orig : GOOGLE INC"
amount = 100.00  # Optional, but helps infer direction (Credit vs Debit)

# 2. Extract info
result = get_counterparty(narrative, amount=amount)

# 3. Use the result
print(result)
```

## Output Structure

The output is a nested dictionary with two main sections:

*   `parsed`: Contains the raw parsing details and metadata (e.g., transaction type).
*   `ctpty`: Contains the extracted entity information.

**Example Output:**
```json
{
    "parsed": {
        "RAW": "WIRE TRANSFER. Orig: GOOGLE INC",
        "ORIG": "GOOGLE INC",
        "META": "WIRE TRANSFER",
        "parser_type": "wire"
    },
    "ctpty": {
        "payer": "GOOGLE INC",
        "payee": null,
        "counterparty": "GOOGLE INC",
        "amount": 100.0
    }
}
```
