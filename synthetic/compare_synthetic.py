"""Validate the pipeline: compare what MetaPhlAn recovered from the synthetic reads
against the composition we designed. Matches by species epithet (last word) so genus
renames (Prevotella -> Segatella, Eubacterium -> Agathobacter) still line up.
"""
import json, math, os
from pipeline.assemble_results import build_results
from pipeline.diversity import parse_species_rows

TSV = "data/synth/profile/metaphlan.tsv"
OUT = "synthetic"
os.makedirs(OUT, exist_ok=True)

# synthetic results.json (relaxed species floor: a designed 16-species set is not noise)
res = build_results(TSV, sample_acc="SYNTHETIC-ISS",
                    source="InSilicoSeq simulated community (16 designed species)",
                    read_pairs=2000000, min_species=10)
res["simulated"] = True
json.dump(res, open(f"{OUT}/synth_results.json", "w"), indent=2)

# designed composition (normalized to %)
design = {}
for line in open("data/synth/design.tsv").read().splitlines()[1:]:
    sp, pct = line.split("\t"); design[sp] = float(pct)
dtot = sum(design.values())

recovered = dict(parse_species_rows(TSV))
rec_by_epithet = {sp.split()[-1].lower(): (sp, v) for sp, v in recovered.items()}

designed_vals, recovered_vals = [], []
with open(f"{OUT}/comparison.tsv", "w") as out:
    out.write("designed_species\tdesigned_pct\trecovered_species\trecovered_pct\n")
    for sp in sorted(design, key=lambda s: -design[s]):
        ep = sp.split()[-1].lower()
        d = design[sp] / dtot * 100
        rname, rv = rec_by_epithet.get(ep, ("(not detected)", 0.0))
        out.write(f"{sp}\t{d:.1f}\t{rname}\t{rv:.1f}\n")
        designed_vals.append(d); recovered_vals.append(rv)

detected = sum(1 for v in recovered_vals if v > 0)

def _ranks(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0] * len(xs)
    for rank, i in enumerate(order):
        r[i] = rank
    return r

dr, rr = _ranks(designed_vals), _ranks(recovered_vals)
n = len(dr); md = sum(dr) / n; mr = sum(rr) / n
cov = sum((dr[i] - md) * (rr[i] - mr) for i in range(n))
sd = math.sqrt(sum((dr[i] - md) ** 2 for i in range(n)))
sr = math.sqrt(sum((rr[i] - mr) ** 2 for i in range(n)))
spearman = cov / (sd * sr) if sd and sr else 0.0

print(f"designed species: {len(design)}, detected: {detected}/{len(design)}")
print(f"Spearman rank correlation (designed vs recovered abundance): {spearman:.2f}")
print(f"wrote {OUT}/synth_results.json, {OUT}/comparison.tsv")
