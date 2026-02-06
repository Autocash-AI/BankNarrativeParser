import re
# no spacy used. recoded to simple plain python logics

LEGAL_SUFFIXES = {
    "LLC", "L.L.C",
    "INC", "INC.",
    "LTD", "LTD.",
    "LLP",
    "CORP", "CORPORATION",
    "CO", "CO.",
    "COMPANY",
    "HOLDINGS", "GROUP", "PLC"
}

O_MARKER_RE = re.compile(r"O/\d*/|O/")

STOP_WORDS = {
    "NOTPROVIDED", "NA", "N/A", "UNKNOWN", "UNAVAILABLE"
}

def is_garbage_token(t: str) -> bool:
    """Check if token is numeric shite (>4 digits) or lacks alpha."""
    t = t.strip()
    if not t: return True
    # If more than 4 digits in a row -> garbage
    if re.search(r"\d{5,}", t): return True
    # If it has no letters at all -> garbage
    if not re.search(r"[A-Za-z]", t): return True
    return False

def getEntity(text):
    """Clean the input text to extract a legal entity name.

    Normalizes whitespace/delimiters, truncates at long numeric tokens (>4 digits),
    and attempts to extract the name using legal suffixes, markers, or clean fallbacks.

    Args:
        text (str): The raw text to process.

    Returns:
        str or None: The cleaned entity name, or None if no valid name found.
    """
    if not text or not text.strip():
        return None

    # light normalization1 - split some delims
    for delim in ["*", "-"]:
        text = text.replace(delim, " ")
    text = re.sub(r"\s+", " ", text).strip()

    # light normalization2 - strip leading alphanumeric garbage shite
    tokens = text.split()
    start_idx = 0
    while start_idx < len(tokens):
        t = tokens[start_idx]
        if any(c.isdigit() for c in t) and not any(c.isalpha() for c in t):
             start_idx += 1
        elif len(re.findall(r"\d", t)) > 4:
             start_idx += 1
        else:
            break

    if start_idx >= len(tokens):
        return None
    
    # Truncate tokens as soon as we hit a long number (>4 digits)
    # This cleans up all "mess" after the number.
    tokens = tokens[start_idx:]
    truncated_tokens = []
    for t in tokens:
        if re.search(r"\d{5,}", t):
            break
        truncated_tokens.append(t)
    
    if not truncated_tokens:
        return None
        
    tokens = truncated_tokens
    text = " ".join(tokens)
    
    # 1. ORG via legal suffix (end-anchored)
    # We look for the last token that is a legal suffix
    for i in range(len(tokens) - 1, -1, -1):
        if tokens[i].upper().strip(".,") in LEGAL_SUFFIXES:
            # Found a suffix, now collect tokens to the left until we hit noise
            name_parts = []
            for j in range(i, -1, -1):
                t = tokens[j]
                # stop if we hit a stop word or something too numeric
                if t.upper() in STOP_WORDS or "/" in t: break
                if len(re.findall(r"\d", t)) > 4: break
                name_parts.append(t)
            
            if len(name_parts) >= 1:
                name_parts.reverse()
                return " ".join(name_parts)

    
    # 2. Name before O/ marker
    m = O_MARKER_RE.search(text)
    if m:
        before = text[:m.start()].strip().split()
        name_parts = []
        for t in reversed(before):
            if not is_garbage_token(t):
                name_parts.append(t)
            else:
                break
        if name_parts:
            name_parts.reverse()
            return " ".join(name_parts)

    
    # 3. Name before STOP words or slash
    for i, tok in enumerate(tokens):
        if tok.upper() in STOP_WORDS or tok == "/":
            before = tokens[:i]
            name_parts = []
            for t in reversed(before):
                if not is_garbage_token(t):
                    name_parts.append(t)
                else:
                    break
            if name_parts:
                name_parts.reverse()
                return " ".join(name_parts)

    
    # 4. Final Fallback: just return the cleaned tokens, stripping long numbers from start/end
    final_tokens = []
    for t in tokens:
        if not is_garbage_token(t):
            final_tokens.append(t)
    
    if len(final_tokens) >= 1:
        return " ".join(final_tokens)

    return None

# def getEntity_spacy_original(text):
#     if not text or not text.strip():
#         return None
#
#     # ... (original spacy logic commented out)
#     doc = nlp(text)
#     # ...
