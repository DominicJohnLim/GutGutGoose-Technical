"""Generate a small cohort of randomized synthetic gut communities by reusing the
already-fetched genomes (data/synth/genomes.fasta). Each sample gets a random subset
of species with random (Dirichlet) abundances, then goes through ISS -> fastp ->
MetaPhlAn. These serve as a comparison cohort for percentiles and a robustness demo.
"""
import sys, os, subprocess
from collections import defaultdict
import numpy as np

GENOMES = "data/synth/genomes.fasta"
N = int(sys.argv[1]) if len(sys.argv) > 1 else 4
START = int(sys.argv[2]) if len(sys.argv) > 2 else 0
READS = 1_000_000
OUT = "data/random"
os.makedirs(OUT, exist_ok=True)
os.environ["PATH"] = os.path.expanduser("~/miniforge3/envs/gutgoose/bin") + ":" + os.environ["PATH"]

# species -> list of contig record ids (headers are "Species_name__contig")
recs = defaultdict(list)
for line in open(GENOMES):
    if line.startswith(">"):
        rid = line[1:].strip()
        recs[rid.split("__")[0]].append(rid)
species = list(recs)

for i in range(START, START + N):
    rng = np.random.default_rng(1000 + i)
    keep = [s for s in species if rng.random() < 0.85] or species
    if len(keep) < 6:
        keep = species
    weights = rng.dirichlet(np.ones(len(keep)))
    abund = {}
    for s, w in zip(keep, weights):
        per = w / len(recs[s])
        for r in recs[s]:
            abund[r] = per
    total = sum(abund.values())
    afile = f"{OUT}/abund_{i}.txt"
    with open(afile, "w") as fh:
        for r, v in abund.items():
            fh.write(f"{r}\t{v / total:.8f}\n")

    base = f"{OUT}/sample_{i}"
    subprocess.run(["iss", "generate", "--genomes", GENOMES, "--abundance_file", afile,
                    "--model", "novaseq", "--n_reads", str(READS), "--cpus", "4",
                    "--output", base, "--compress"], check=True)
    subprocess.run(["fastp", "-i", f"{base}_R1.fastq.gz", "-I", f"{base}_R2.fastq.gz",
                    "-o", f"{base}_c1.fastq.gz", "-O", f"{base}_c2.fastq.gz",
                    "--detect_adapter_for_pe", "-j", f"{base}_fastp.json",
                    "-h", f"{base}_fastp.html"], check=True)
    subprocess.run(["metaphlan", f"{base}_c1.fastq.gz,{base}_c2.fastq.gz",
                    "--input_type", "fastq", "--db_dir", "data/db/metaphlan", "--offline",
                    "--mapout", f"{base}.map.bz2", "--nproc", "4",
                    "-o", f"{base}_profile.tsv"], check=True)
    print(f"sample {i}: {len(keep)} species designed -> {base}_profile.tsv")

print("RANDOM_DONE")
