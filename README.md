# Patient-Facing Gut Microbiome Report

A shotgun stool sample → a plain-language patient report. The reporting LLM can only state
claims the cited knowledge base backs — an unsupported sentence fails the build instead of
reaching the patient.

## Result

**A grounded, 10-finding patient report** — backed by **47 species**, **433 MetaCyc
pathways**, and a metabolic model that predicts how the gut's **butyrate output shifts with
diet**.

The pipeline is validated blind against ground truth — 30 synthetic communities of known
composition, scored on recovery: **96% mean species recall at 100% precision (zero false
positives), ρ = 0.78** abundance correlation (n = 30). Deterministic, so reproducible by
construction.

## Scope

Scoped to what can be defended, not to maximum surface area.

- **Validation covers the taxonomic/abundance step** — the core measurement. HUMAnN
  (function) and MICOM (metabolics) run on the one real sample as demonstrations, not
  benchmarks; extending the known-truth benchmark to them is the obvious next step.
- **The metabolic output is a directional counterfactual,** not an absolute clinical value:
  hold the measured community fixed, swap the diet, report which way butyrate moves. Gross
  production is reported because net boundary flux cancels through cross-feeding.
- **Every health claim in the report cites a knowledge-base card,** and a validator fails the
  build on any claim that doesn't — so the failure mode is a broken build, not a confident
  wrong sentence.

Details, reasoning, and citations in `methodology.md`.

## How it works

A staged reduction: gigabytes of reads collapse, stage by stage, into a small table with
meaning, which an LLM then translates under a hard grounding constraint.

```
real FASTQ → fastp → Bowtie2 host-removal → MetaPhlAn4 → HUMAnN3 → diversity → MICOM
          → results.json → grounded LLM (+ validator) → report.json
```

1. **Preprocess** — `fastp` trims adapters/low-quality reads; `Bowtie2` drops anything that
   aligns to GRCh38, leaving microbial reads (privacy + correctness).
2. **Taxonomy** — `MetaPhlAn4`, marker-gene rather than k-mer: it returns the relative
   abundances a report needs and carries a lower false-positive rate. A sanity gate asserts
   species + the explicit *unclassified* fraction sum to ~100% before anything proceeds —
   which is how the unclassified fraction got handled instead of silently dropped.
3. **Function** — `HUMAnN3` for gene families and MetaCyc pathways (what the community *does*,
   not just who's present). Requires a version-matched MetaPhlAn DB for its prescreen.
4. **Diversity** — Shannon / richness / evenness from the abundance table, reported with the
   explicit caveat that low diversity isn't inherently unhealthy (kept in the report rules,
   not the math, because it's a judgment call).
5. **Metabolic model** — `MICOM` builds a community constraint-based model from `AGORA`
   reconstructions and grows it on curated `VMH` diet media. SCFA output is read per diet;
   the diet swap is the counterfactual that makes a recommendation defensible.
6. **Grounded report** — a curated knowledge base (taxon + concept cards, with ranges and
   citations) is the *only* source the LLM may claim from; it attaches a card id to each
   finding, and `validate_report.py` rejects any unmatched citation. Grounding, not model
   size, is the safety mechanism.
7. **Validation** — `InSilicoSeq` generates reads from real genomes at compositions I design,
   so the answer is known; recovery is measured across the 30-community benchmark.

## Run

```bash
conda env create -f environment.yml            # pinned env (native arm64; no Docker)
bash pipeline/run_pipeline.sh                   # → data/results/results.json (+ fastp.html)
PYTHONPATH=. python -m pipeline.micom_predict   # → metabolic SCFA-by-diet
python -m report.generate_report                # → report.json   (needs OPENROUTER_API_KEY)
python -m report.validate_report                # grounding gate
python -m pytest -q                             # unit tests
```

## Layout

| Path | What |
|---|---|
| `data/results/` | the deliverables — `results.json`, `report.json`, `fastp.html` |
| `pipeline/` | run_pipeline, diversity, results assembly, MICOM |
| `knowledge/` | the cited knowledge base the LLM is allowed to use |
| `report/` | grounded generation + the validator |
| `synthetic/` | InSilicoSeq generation + the validation benchmark |
| `tests/` | unit tests |
| `methodology.md` | formal technical write-up + citations |
