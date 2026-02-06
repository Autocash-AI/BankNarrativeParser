import json
from banknarrativeparser.key_engine.keys import KEYS, INLINE_KEYS

KEYS = sorted(set(KEYS), key=len, reverse=True)
INLINE_KEYS = sorted(INLINE_KEYS, key=len, reverse=True)

ALLOWED = {' ', ':', '=',',', '/', '\\', '_', '#','-',';','-'}

def is_standalone(text, i, k_len):
    before = text[i - 1] if i > 0 else ' '
    after  = text[i + k_len] if i + k_len < len(text) else ' '
    return before in ALLOWED and after in ALLOWED

def find_keys(text, key_list):
    found = {}
    reserved = []

    for k in key_list:
        k_len = len(k)
        for i in range(len(text) - k_len + 1):
            if text[i:i + k_len] != k:
                continue
            if not is_standalone(text, i, k_len):
                continue
            if any(s <= i < e for s, e in reserved):
                continue

            found[i] = k
            reserved.append((i, i + k_len))

    return dict(sorted(found.items()))

def split_inline_keys(text: str):
    marks = find_keys(text, INLINE_KEYS)

    if not marks:
        return text.strip()

    idx = [0] + list(marks.keys()) + [len(text)]
    out = {}

    out["value"] = text[:idx[1]].strip()

    for i in range(1, len(idx) - 1):
        start, end = idx[i], idx[i + 1]
        k = marks[start]
        z = start + len(k)
        while z < len(text) and not text[z].isalnum():
            z += 1
        out[k] = text[z:end].strip()
    return out


def all_parser_v2(v1_output: dict):
    out = {}

    for k, v in v1_output.items():
        if isinstance(v, str):
            out[k] = split_inline_keys(v)
        else:
            out[k] = v

    return out


def all_parser_v1(narr: str):
    marks = find_keys(narr, KEYS)

    idx = [0] + list(marks.keys()) + [len(narr)]
    out = {}

    out["META"] = narr[:idx[1]].strip()

    for i in range(1, len(idx) - 1):
        start, end = idx[i], idx[i + 1]
        k = marks[start]
        z = start + len(k)
        while z < len(narr) and not narr[z].isalnum():
            z += 1

        out[k] = narr[z:end].strip()

    return out

def all_parser(narr: str):
    v1 = all_parser_v1(narr)
    v2 = all_parser_v2(v1)
    return {
        "RAW": narr,
        **v2
    }
