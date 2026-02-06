import json
import re
from pathlib import Path
from rapidfuzz import fuzz


BASE_DIR = Path(__file__).parent
CANONICAL_FILE = BASE_DIR / "canonical_keys.json"


class KeyDetector:
    def __init__(self, threshold: int = 85, max_words: int = 7):
        self.threshold = threshold
        self.max_words = max_words
        self._load_keys()

    
    # LOAD CANONICAL KEYS
    
    def _load_keys(self):
        with open(CANONICAL_FILE, "r", encoding="utf-8") as f:
            self.canonical_map = json.load(f)

        self.match_keys = []
        self.all_variants = set()

        for canon, variants in self.canonical_map.items():
            for v in variants:
                self.match_keys.append((canon, v))
                self.all_variants.add(self._clean(v))

    
    # PUBLIC ENTRY
    
    def rewrite(self, text: str):
        text = self._normalize_text(text)

        windows = self._generate_windows(text)
        candidates = self._match_windows(text, windows)
        accepted = self._resolve_conflicts(candidates)

        rewritten_text = self._rewrite_text(text, accepted)

        unknown_hitl = self._collect_unknown_keys_for_hitl(text, windows, accepted)

        if unknown_hitl:
            return rewritten_text.upper(), (True, unknown_hitl)
        else:
            return rewritten_text.upper(), False


    
    # NORMALIZATION
    
    def _normalize_text(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r"\s+", " ", text)
        return text

    
    # CLEAN STRING
    
    def _clean(self, s: str) -> str:
        return re.sub(r"[^a-z0-9]", "", s)

    
    # WINDOW GENERATION
    
    def _generate_windows(self, text: str):
        tokens = []
        for m in re.finditer(r"[a-z0-9]+", text):
            tokens.append((m.group(), m.start(), m.end()))

        windows = []
        for i in range(len(tokens)):
            for w in range(1, self.max_words + 1):
                if i + w <= len(tokens):
                    phrase = " ".join(tokens[j][0] for j in range(i, i + w))
                    start = tokens[i][1]
                    end = tokens[i + w - 1][2]
                    windows.append((phrase, start, end))

        return windows

    
    # DELIMITER CHECK
    def _has_delimiter_after(self, text: str, end: int) -> bool:
        tail = text[end:]

        i = 0
        while i < len(tail) and tail[i].isspace():
            i += 1

        # delimiter immediately → OK
        if i < len(tail) and tail[i] in ":=":
            return True

        # word continues → NOT a key end
        if i < len(tail) and tail[i].isalnum():
            return False

        # skip punctuation, but stop on word
        while i < len(tail):
            if tail[i] in ":=":
                return True
            if tail[i].isalnum():
                return False
            i += 1

        return False

    
    # MATCH WINDOWS AGAINST CANONICAL VARIANTS
    def _match_windows(self, text, windows):
        candidates = []

        for phrase, start, end in windows:
            if not self._has_delimiter_after(text, end):
                continue

            phrase_clean = self._clean(phrase)

            best_canon = None
            best_score = 0

            for canon, variant in self.match_keys:
                score = fuzz.ratio(phrase_clean, self._clean(variant))
                if score >= self.threshold and score > best_score:
                    best_canon = variant
                    best_score = score

            if best_canon:
                candidates.append({
                    "raw": phrase,
                    "canonical": best_canon,   
                    "score": best_score,
                    "start": start,
                    "end": end,
                    "tokens": len(phrase.split())
                })
        # print(json.dumps(candidates,indent=3))
        return candidates



    
    # CONFLICT RESOLUTION
    def _resolve_conflicts(self, candidates):
        """
        Conflict resolution rules:
        1. Higher fuzzy score wins
        2. If score ties, longer (more tokens) wins
        """

        # sort by start position only (grouping purpose)
        candidates.sort(key=lambda c: c["start"])

        accepted = []

        for c in candidates:
            keep = True

            for a in accepted[:]:
                overlap = not (c["end"] <= a["start"] or c["start"] >= a["end"])

                if not overlap:
                    continue

                # -------- conflict detected --------

                # Rule 1: higher score wins
                if c["score"] > a["score"]:
                    accepted.remove(a)
                    continue

                if c["score"] < a["score"]:
                    keep = False
                    break

                # Rule 2: score tie → more tokens wins
                if c["tokens"] > a["tokens"]:
                    accepted.remove(a)
                    continue
                else:
                    keep = False
                    break

            if keep:
                accepted.append(c)

        # optional debug
        # print(json.dumps(accepted, indent=2))

        return accepted



    
    # REWRITE TEXT
    
    def _rewrite_text(self, text: str, accepted):
        accepted.sort(key=lambda c: c["start"], reverse=True)

        for c in accepted:
            text = text[:c["start"]] + c["canonical"] + text[c["end"]:]

        return text

    
    # HITL — AMBIGUOUS MATCHES
    
    def _collect_hitl(self, candidates, accepted, text):
        accepted_spans = [(a["start"], a["end"]) for a in accepted]
        hitl = []

        for phrase, start, end in self._generate_windows(text):
            # must be followed by delimiter
            if not self._has_delimiter_after(text, end):
                continue

            # ignore single-word junk
            if len(phrase.split()) < 2:
                continue

            # ignore non-alpha phrases
            if not re.search(r"[a-z]", phrase):
                continue

            # ignore if fully inside accepted key
            inside = False
            for a_start, a_end in accepted_spans:
                if start >= a_start and end <= a_end:
                    inside = True
                    break
            if inside:
                continue

            # check if this phrase matched ANY canonical key
            matched = False
            phrase_clean = self._clean(phrase)

            for _, variant in self.match_keys:
                if fuzz.ratio(phrase_clean, self._clean(variant)) >= self.threshold:
                    matched = True
                    break

            if matched:
                continue

            # REAL HITL CASE
            hitl.append({
                "type": "NEW_KEY",
                "raw_phrase": phrase.upper(),
                "suggested": None,
                "confidence": None
            })

        return hitl


    
    # HITL — COMPLETELY UNKNOWN KEYS
    
    def _collect_unknown_keys_for_hitl(self, text, windows, accepted):
        accepted_spans = [(a["start"], a["end"]) for a in accepted]
        hitl = {}

        # all canonical words flattened (for NAME vs CUST NAME)
        canonical_tokens = set()
        for v in self.all_variants:
            canonical_tokens.update(re.findall(r"[a-z]+", v))

        for m in re.finditer(r"\b([a-z][a-z0-9]*)\s*[:=]", text):
            key_start, key_end = m.span(1)
            raw_key = m.group(1)

            #  numeric or starts with digit → ignore
            if raw_key[0].isdigit():
                continue

            clean_key = self._clean(raw_key)

            #  already known or part of known key
            if clean_key in self.all_variants:
                continue
            if raw_key in canonical_tokens:
                continue

            #  overlaps accepted canonical match
            overlap = False
            for a_start, a_end in accepted_spans:
                if not (key_end <= a_start or key_start >= a_end):
                    overlap = True
                    break
            if overlap:
                continue

            # tokenize safely
            words = list(re.finditer(r"[a-z0-9]+|[:=]", text))
            idx = None
            for i, w in enumerate(words):
                if w.start() == key_start:
                    idx = i
                    break
            if idx is None:
                continue

            variants = [raw_key]

            # look back max 4 words, stop at delimiter
            back = 0
            j = idx - 1
            while j >= 0 and back < 4:
                if words[j].group() in {":", "="}:
                    break
                variants.append(
                    text[words[j].start():words[idx].end()]
                )
                back += 1
                j -= 1

            # normalize + dedupe
            variants = [
                re.sub(r"\s+", " ", v.strip()).upper()
                for v in variants
            ]
            variants = list(dict.fromkeys(variants))

            hitl[raw_key.upper()] = variants

        return hitl


if __name__=='__main__':
    pass