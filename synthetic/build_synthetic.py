"""Build a designed synthetic gut community: fetch real reference genomes from NCBI
for a chosen species list, then emit a combined FASTA + per-record abundance file
that InSilicoSeq turns into synthetic shotgun reads.

This produces SIMULATED data (labelled as such). Reads are generated from real
reference genomes at a designed composition, so MetaPhlAn can classify them and we
can check the pipeline recovers what we put in.
"""
import os, subprocess, glob, zipfile, shutil
from collections import defaultdict

# Designed composition (relative %, normalized later). A plausible plant-forward
# young-adult gut: Bacteroides/Prevotella backbone, good Bifidobacteria, a spread of
# butyrate producers, a methanogen + sulfidogen in the tail.
COMMUNITY = {
    "Bacteroides uniformis": 14,
    "Prevotella copri": 12,
    "Bacteroides thetaiotaomicron": 9,
    "Bifidobacterium longum": 8,
    "Agathobacter rectalis": 7,        # formerly Eubacterium rectale
    "Faecalibacterium prausnitzii": 6,
    "Roseburia intestinalis": 6,
    "Ruminococcus bromii": 6,
    "Bifidobacterium adolescentis": 5,
    "Blautia wexlerae": 5,
    "Akkermansia muciniphila": 4,
    "Bacteroides fragilis": 3,
    "Anaerostipes hadrus": 3,
    "Methanobrevibacter smithii": 3,   # methanogen (gas/bloating)
    "Escherichia coli": 1.5,
    "Desulfovibrio piger": 1.5,        # sulfidogen
}

WORK = "data/synth"
GEN = f"{WORK}/genomes"
DATASETS = "/tmp/datasets"
os.makedirs(GEN, exist_ok=True)


def fetch(species):
    """Download the reference genome for `species`, relabel headers with a species
    tag, return the path to the per-species .fna (or None on failure)."""
    safe = species.replace(" ", "_")
    out_fna = f"{GEN}/{safe}.fna"
    if os.path.exists(out_fna):
        return out_fna
    zippath = f"{GEN}/{safe}.zip"
    try:
        subprocess.run([DATASETS, "download", "genome", "taxon", species,
                        "--reference", "--include", "genome",
                        "--assembly-source", "RefSeq", "--filename", zippath],
                       check=True, capture_output=True)
        with zipfile.ZipFile(zippath) as z:
            z.extractall(f"{GEN}/{safe}_x")
        fnas = glob.glob(f"{GEN}/{safe}_x/ncbi_dataset/data/*/*.fna")
        if not fnas:
            print(f"  !! no genome for {species}, skipping")
            return None
        with open(out_fna, "w") as out:
            for fna in fnas:
                with open(fna) as fh:
                    for line in fh:
                        if line.startswith(">"):
                            rec = line[1:].split()[0]
                            out.write(f">{safe}__{rec}\n")
                        else:
                            out.write(line)
        return out_fna
    except subprocess.CalledProcessError:
        print(f"  !! download failed for {species}, skipping")
        return None
    finally:
        shutil.rmtree(f"{GEN}/{safe}_x", ignore_errors=True)
        if os.path.exists(zippath):
            os.remove(zippath)


def main():
    records = {}  # record_id -> species
    with open(f"{WORK}/genomes.fasta", "w") as combined:
        for sp in COMMUNITY:
            print(f"fetching {sp} ...")
            fna = fetch(sp)
            if not fna:
                continue
            with open(fna) as fh:
                for line in fh:
                    combined.write(line)
                    if line.startswith(">"):
                        records[line[1:].strip()] = sp

    # abundance per record = species target split across its records, then normalized
    sp_records = defaultdict(list)
    for rec, sp in records.items():
        sp_records[sp].append(rec)
    raw = {}
    for sp, recs in sp_records.items():
        per = COMMUNITY[sp] / len(recs)
        for rec in recs:
            raw[rec] = per
    total = sum(raw.values())
    with open(f"{WORK}/abundance.txt", "w") as ab:
        for rec, val in raw.items():
            ab.write(f"{rec}\t{val / total:.8f}\n")

    # human-readable record of the DESIGNED composition (provenance: simulated)
    with open(f"{WORK}/design.tsv", "w") as d:
        d.write("species\tdesigned_pct\n")
        for sp in sp_records:
            d.write(f"{sp}\t{COMMUNITY[sp]}\n")

    print(f"\nbuilt community: {len(sp_records)}/{len(COMMUNITY)} species, "
          f"{len(records)} records")
    print("wrote data/synth/genomes.fasta, abundance.txt, design.tsv")


if __name__ == "__main__":
    main()
