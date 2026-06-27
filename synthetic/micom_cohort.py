"""Run MICOM metabolic prediction across the randomized synthetic cohort, so Maya's
predicted butyrate can be placed against a distribution ("higher than most")."""
import json, glob, os
from pipeline.micom_predict import predict

results = []
for tsv in sorted(glob.glob("data/random/sample_*_profile.tsv")):
    i = tsv.split("sample_")[1].split("_")[0]
    odir = f"data/micom_random/sample_{i}"
    r = predict(tsv, f"random_{i}", odir)
    os.makedirs(odir, exist_ok=True)
    json.dump(r, open(f"{odir}/micom.json", "w"), indent=2)
    print(f"random_{i}: butyrate(avg diet) = {r['diets']['average']['butyrate']}, coverage = {r['model_coverage']}")
    results.append(r)

os.makedirs("data/micom_random", exist_ok=True)
json.dump(results, open("data/micom_random/cohort_micom.json", "w"), indent=2)
print("COHORT_MICOM_DONE")
