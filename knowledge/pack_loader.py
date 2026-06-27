import os, glob

def load_pack(dir="knowledge"):
    """Load every card under dir/<folder>/<stem>.md into {f'{folder}:{stem}': text}.
    Top-level files like rules.md are intentionally NOT loaded here (rules.md is the
    system prompt, handled separately by the generator)."""
    pack = {}
    for path in glob.glob(os.path.join(dir, "*", "*.md")):
        folder = os.path.basename(os.path.dirname(path))
        stem = os.path.splitext(os.path.basename(path))[0]
        with open(path) as fh:
            pack[f"{folder}:{stem}"] = fh.read()
    return pack

def card_keys(pack):
    return set(pack.keys())
