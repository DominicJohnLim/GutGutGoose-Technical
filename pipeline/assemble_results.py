import json, subprocess, datetime
from pipeline.diversity import parse_species_rows, diversity_from_metaphlan

def parse_abundance(path):
    return [{"species": sp, "rel_abundance_pct": rel}
            for sp, rel in parse_species_rows(path)]

def sanity_check(abundance, pathways):
    total = sum(r["rel_abundance_pct"] for r in abundance)
    if not (99.0 <= total <= 101.0):
        raise ValueError(f"abundance sums to {total:.2f}, expected ~100")
    if len(abundance) <= 20:
        raise ValueError(f"only {len(abundance)} species — looks like noise, not a real profile")

def _tool_version(cmd):
    try:
        out = subprocess.run(cmd, capture_output=True, text=True)
        return (out.stdout or out.stderr).strip().split("\n")[0]
    except Exception:
        return "unknown"

def build_results(metaphlan_tsv, sample_acc, source, read_pairs, pathways=None):
    abundance = parse_abundance(metaphlan_tsv)
    pathways = pathways or []
    sanity_check(abundance, pathways)
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
