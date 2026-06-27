import json, subprocess, datetime
from pipeline.diversity import parse_species_rows, diversity_from_metaphlan

def parse_abundance(path):
    return [{"species": sp, "rel_abundance_pct": rel}
            for sp, rel in parse_species_rows(path)]

def parse_unclassified(path):
    """MetaPhlAn4 emits an 'UNCLASSIFIED  -1  <pct>' row for reads matching no
    species marker. relative_abundance is column index 2 (the NCBI id is -1,
    so first-float parsing would wrongly pick it)."""
    with open(path) as fh:
        for line in fh:
            if line.startswith("UNCLASSIFIED\t"):
                return float(line.rstrip("\n").split("\t")[2])
    return 0.0

def sanity_check(abundance, pathways, unclassified_pct=0.0, min_species=20):
    # MetaPhlAn4 splits the community into classified species + an UNCLASSIFIED
    # fraction; together they must sum to ~100. A wrong-column parse would break this.
    total = sum(r["rel_abundance_pct"] for r in abundance) + unclassified_pct
    if not (99.0 <= total <= 101.0):
        raise ValueError(f"species + unclassified = {total:.2f}, expected ~100 (possible parse error)")
    # Real stool samples carry many species; noise classifies to almost none. A designed
    # synthetic community can legitimately have fewer, so the floor is a parameter.
    if len(abundance) < min_species:
        raise ValueError(f"only {len(abundance)} species (< {min_species}) — looks like noise, not a real profile")

def _tool_version(cmd):
    try:
        out = subprocess.run(cmd, capture_output=True, text=True)
        return (out.stdout or out.stderr).strip().split("\n")[0]
    except Exception:
        return "unknown"

def build_results(metaphlan_tsv, sample_acc, source, read_pairs, pathways=None, min_species=20):
    abundance = parse_abundance(metaphlan_tsv)
    unclassified = parse_unclassified(metaphlan_tsv)
    pathways = pathways or []
    sanity_check(abundance, pathways, unclassified, min_species)
    return {
        "provenance": {
            "sample_accession": sample_acc,
            "source": source,
            "subsampled_read_pairs": read_pairs,
            "tool_versions": {
                "fastp": _tool_version(["fastp", "--version"]),
                "metaphlan": _tool_version(["metaphlan", "--version"]),
            },
            "generated_at": datetime.date.today().isoformat(),
        },
        "classified_pct": round(sum(r["rel_abundance_pct"] for r in abundance), 2),
        "unclassified_pct": round(unclassified, 2),
        "abundance": sorted(abundance, key=lambda r: -r["rel_abundance_pct"]),
        "diversity": diversity_from_metaphlan(metaphlan_tsv),
        "pathways": pathways,
        "evidence": {"fastp_html": "data/results/fastp.html"},
    }

if __name__ == "__main__":
    import os
    res = build_results(
        "data/profile/metaphlan.tsv",
        sample_acc=os.environ.get("SAMPLE_ACC", "unknown"),
        source=os.environ.get("SAMPLE_SOURCE", "ENA"),
        read_pairs=int(os.environ.get("READ_PAIRS", "1500000")),
    )
    with open("data/results/results.json", "w") as fh:
        json.dump(res, fh, indent=2)
    print(f"wrote results.json: {len(res['abundance'])} species, "
          f"shannon={res['diversity']['shannon']}")
