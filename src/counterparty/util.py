import re
from typing import Optional, Dict, Any
import unicodedata

# this is used in extract payer/payee logic
def norm2(v):
    if v is None: return None
    if isinstance(v, dict): v = v.get("value") or v.get("name")
    s = str(v).strip()
    s = unicodedata.normalize("NFKD", s)
    s = s.encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"\s+", " ", s)
    return s if s else None

# This one is for aliasing.
def normalize(text: str) -> str:
    if not text: return ""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ASCII", "ignore").decode("ASCII")
    text = text.upper()
    text = re.sub(r"[.,/\\]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# This one is for wire/ach/swift detection
def norm(text: Optional[str]) -> str:
    if not text: return ""
    text = re.sub(r"^[,|]+", "", text)
    text = re.sub(r"[\\|,]+$", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip().upper()

# This one is when i want to run key_detector
def normalize_spaces(text: str) -> str:
    text = text.replace('.','')
    text = text.replace(',',' ')
    # add space BEFORE and AFTER delimiter if missing
    text = re.sub(r"(?<!\s)([:,=;#])", r" \1", text)
    text = re.sub(r"([:,=;#])(?!\s)", r"\1 ", text)
    return " ".join(text.split())