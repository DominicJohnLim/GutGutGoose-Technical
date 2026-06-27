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

def _rel_value(parts):
    """The relative-abundance float from a MetaPhlAn row's tab-split columns.
    On a species row it is the only plain-float column: the clade name and the
    NCBI lineage id contain pipes, and additional_species is text/empty."""
    for field in parts[1:]:
        try:
            return float(field.strip())
        except ValueError:
            continue
    return None

def parse_species_rows(path):
    """(species_name, rel_abundance_pct) for species-level rows only.
    Excludes higher ranks (k__/p__/.../g__) and sub-species SGB rows (t__)."""
    rows = []
    with open(path) as fh:
        for line in fh:
            if line.startswith("#") or "\t" not in line:
                continue
            parts = line.rstrip("\n").split("\t")
            leaf = parts[0].split("|")[-1]
            if not leaf.startswith("s__"):
                continue
            rel = _rel_value(parts)
            if rel is None:
                continue
            rows.append((leaf[3:].replace("_", " "), rel))
    return rows

def diversity_from_metaphlan(path):
    abundances = [rel for _, rel in parse_species_rows(path)]
    return {
        "shannon": round(shannon(abundances), 3),
        "richness": richness(abundances),
        "evenness": round(evenness(abundances), 3),
    }
