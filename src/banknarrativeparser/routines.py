import json
from pathlib import Path

def routine1(data):
    # print("NEW KEY-VALUE PAIRS DETECTED.")
    # print(f"ADD THEM TO THE LIST")
    # for k in data[1]:
    #     print(f"{k} : {data[1][k]}")
    # print()
    pass


def routine2(key, value, inline=False):
    key = key.strip().lower()
    value = value.strip()
    if not key or not value:
        return

    value_up = value.upper()

    base = Path(__file__).resolve().parent     
    gamma = base.parent                        

    # canonical_keys.json
    canon_path = gamma / "key_engine" / "canonical_keys.json"
    with open(canon_path, "r", encoding="utf-8") as f:
        canon = json.load(f)

    canon.setdefault(key, [])
    if value.lower() not in canon[key]:
        canon[key].append(value.lower())
        with open(canon_path, "w", encoding="utf-8") as f:
            json.dump(canon, f, indent=2)

    all_path = gamma / "key_engine" / "keys.py"
    add_to_keys(all_path, value_up, inline)



def add_to_keys(path, value, inline):
    text = path.read_text(encoding="utf-8")
    name = "INLINE_KEYS" if inline else "KEYS"

    start = text.find(f"{name} = [")
    if start == -1:
        raise RuntimeError(f"{name} not found in {path}")

    l = text.find("[", start)
    r = text.find("]", l)
    if l == -1 or r == -1:
        raise RuntimeError(f"Broken {name} list in {path}")

    body = text[l + 1:r]
    items = []

    for x in body.split(","):
        x = x.strip().strip('"').strip("'")
        if x:
            items.append(x)

    if value not in items:
        items.append(value)

    items = sorted(set(items), key=lambda x: (-len(x), x))

    new_list = f"{name} = [\n"
    for x in items:
        new_list += f'    "{x}",\n'
    new_list += "]"

    text = text[:start] + new_list + text[r + 1:]
    path.write_text(text, encoding="utf-8")
