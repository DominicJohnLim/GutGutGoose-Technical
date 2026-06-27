import math

def _props(abundances):
    vals = [a for a in abundances if a > 0]
    total = sum(vals)
    return [v / total for v in vals] if total else []

def shannon(abundances):
    return -sum(p * math.log(p) for p in _props(abundances))

def richness(abundances):
    return sum(1 for a in abundances if a > 0)

def evenness(abundances):
    r = richness(abundances)
    return shannon(abundances) / math.log(r) if r > 1 else 0.0

def diversity_from_metaphlan(path):
    abundances = []
    with open(path) as fh:
        for line in fh:
            if line.startswith("#") or "\t" not in line:
                continue
            clade, *_, rel = line.rstrip("\n").split("\t")
            if clade.split("|")[-1].startswith("s__"):
                abundances.append(float(rel))
    return {
        "shannon": round(shannon(abundances), 3),
        "richness": richness(abundances),
        "evenness": round(evenness(abundances), 3),
    }
