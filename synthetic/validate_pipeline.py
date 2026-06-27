"""Pipeline validation benchmark.

For each synthetic community we KNOW the designed composition (abund_*.txt). This
runs the designed-vs-recovered comparison across all of them and reports aggregate
accuracy + reproducibility statistics — the statistical proof that the taxonomic
pipeline recovers truth reliably across many samples.

Matching is by species epithet (last word) so genus renames (Prevotella->Segatella,
Eubacterium->Agathobacter) still line up.
"""
import glob, json, math, statistics
from collections import defaultdict
from pipeline.diversity import parse_species_rows


def designed(abund_file):
    sp = defaultdict(float)
    for line in open(abund_file):
        rec, frac = line.rstrip("\n").split("\t")
        sp[rec.split("__")[0].replace("_", " ")] += float(frac)
    total = sum(sp.values())
    return {k: v / total * 100 for k, v in sp.items()}


def _spearman(x, y):
    def ranks(a):
        order = sorted(range(len(a)), key=lambda i: a[i])
        r = [0] * len(a)
        for k, i in enumerate(order):
            r[i] = k
        return r
    rx, ry = ranks(x), ranks(y)
    n = len(x); mx = sum(rx) / n; my = sum(ry) / n
    cov = sum((rx[i] - mx) * (ry[i] - my) for i in range(n))
    sx = math.sqrt(sum((rx[i] - mx) ** 2 for i in range(n)))
    sy = math.sqrt(sum((ry[i] - my) ** 2 for i in range(n)))
    return cov / (sx * sy) if sx and sy else float("nan")


def main():
    per_sample = []
    for prof in sorted(glob.glob("data/random/sample_*_profile.tsv")):
        i = prof.split("sample_")[1].split("_")[0]
        des = {k.split()[-1].lower(): v for k, v in designed(f"data/random/abund_{i}.txt").items()}
        rec = {k.split()[-1].lower(): v for k, v in dict(parse_species_rows(prof)).items()}
        dset, rset = set(des), set(rec)
        tp = len(dset & rset)
        recall = tp / len(dset) if dset else 0.0
        precision = tp / len(rset) if rset else 0.0
        common = sorted(dset & rset)
        rho = _spearman([des[e] for e in common], [rec[e] for e in common]) if len(common) >= 3 else float("nan")
        per_sample.append({"sample": i, "designed_species": len(dset),
                           "recall": round(recall, 3), "precision": round(precision, 3),
                           "spearman": None if math.isnan(rho) else round(rho, 3)})

    recalls = [r["recall"] for r in per_sample]
    precs = [r["precision"] for r in per_sample]
    rhos = [r["spearman"] for r in per_sample if r["spearman"] is not None]
    summary = {
        "n_samples": len(per_sample),
        "mean_recall": round(statistics.mean(recalls), 3) if recalls else None,
        "mean_precision": round(statistics.mean(precs), 3) if precs else None,
        "mean_spearman": round(statistics.mean(rhos), 3) if rhos else None,
        "spearman_sd": round(statistics.pstdev(rhos), 3) if len(rhos) > 1 else 0,
    }
    json.dump({"summary": summary, "per_sample": per_sample},
              open("synthetic/validation.json", "w"), indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
