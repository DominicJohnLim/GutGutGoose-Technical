"""MICOM metabolic prediction.

Build a community-scale metabolic model from a MetaPhlAn profile (genus level,
AGORA models), simulate growth on real VMH diets, and report predicted gross
short-chain-fatty-acid production — including the high-fiber what-if.

We report GROSS production (what the producer taxa make) rather than net flux to
the lumen: butyrate is heavily cross-fed (produced then partly consumed by
neighbours), so net nets to ~0 while gross is the meaningful "production capacity".
"""
import json, os, sys
import pandas as pd
from micom.workflows import build, grow
from micom.qiime_formats import load_qiime_medium
from pipeline.diversity import parse_species_rows

DB = "data/db/micom/agora103_genus.qza"
MEDIA = {
    "average":    "data/db/micom/media/vmh_eu_average_agora.qza",
    "high_fiber": "data/db/micom/media/vmh_high_fiber_agora.qza",
    "low_fiber":  "data/db/micom/media/vmh_high_fat_low_carb_agora.qza",
}
SCFA = {"butyrate": "but", "propionate": "ppa", "acetate": "ac"}


def _genus_taxonomy(tsv, sample_id):
    rows = [{"genus": sp.split()[0], "abundance": rel} for sp, rel in parse_species_rows(tsv)]
    tax = pd.DataFrame(rows).groupby("genus", as_index=False)["abundance"].sum()
    tax["id"] = tax["genus"]
    tax["sample_id"] = sample_id
    return tax


def _gross_production(res, met):
    """Abundance-weighted sum of per-taxon export flux for metabolite `met`."""
    ex = res.exchanges
    b = ex[(ex["reaction"] == f"EX_{met}(e)") & (ex["direction"] == "export")]
    return round(float((b["flux"] * b["abundance"]).sum()), 2)


def predict(tsv, sample_id, out_dir):
    tax = _genus_taxonomy(tsv, sample_id)
    manifest = build(tax, model_db=DB, out_folder=out_dir, cutoff=1e-4, threads=4)
    coverage = round(float(manifest["found_abundance_fraction"].iloc[0]), 3)
    out = {"sample": sample_id, "model_coverage": coverage, "diets": {}}
    for diet, path in MEDIA.items():
        res = grow(manifest, model_folder=out_dir, medium=load_qiime_medium(path),
                   tradeoff=0.5, threads=4)
        out["diets"][diet] = {name: _gross_production(res, met) for name, met in SCFA.items()}
    base = out["diets"]["average"]["butyrate"]
    out["butyrate_vs_average_pct"] = {
        "high_fiber": round((out["diets"]["high_fiber"]["butyrate"] / base - 1) * 100, 1) if base else None,
        "low_fiber": round((out["diets"]["low_fiber"]["butyrate"] / base - 1) * 100, 1) if base else None,
    }
    return out


if __name__ == "__main__":
    tsv = sys.argv[1] if len(sys.argv) > 1 else "data/profile/metaphlan.tsv"
    sid = sys.argv[2] if len(sys.argv) > 2 else "maya_real"
    odir = sys.argv[3] if len(sys.argv) > 3 else "data/micom_real"
    result = predict(tsv, sid, odir)
    os.makedirs(odir, exist_ok=True)
    json.dump(result, open(f"{odir}/micom_{sid}.json", "w"), indent=2)
    print(json.dumps(result, indent=2))
