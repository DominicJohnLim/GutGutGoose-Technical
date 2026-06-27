import json, sys
from knowledge.pack_loader import load_pack, card_keys

def validate(report, keys):
    """Return the list of citation keys used by findings that are NOT in the pack.
    Empty list == every health claim is grounded."""
    return [f.get("citation") for f in report.get("findings", [])
            if f.get("citation") not in keys]

if __name__ == "__main__":
    report = json.load(open("data/results/report.json"))
    missing = validate(report, card_keys(load_pack()))
    if missing:
        print("UNGROUNDED claims cite missing cards:", missing)
        sys.exit(1)
    print("report grounding OK")
