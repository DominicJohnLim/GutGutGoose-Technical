#!/usr/bin/env bash
# Offline metagenomics pipeline: real FASTQ -> abundance + diversity -> results.json
# Run from repo root. Requires the `gutgoose` conda env and the databases in data/db/.
set -euo pipefail

SAMPLE_ACC="${SAMPLE_ACC:-DRR042265}"
SAMPLE_SOURCE="${SAMPLE_SOURCE:-ENA PRJDB3601 (Metagenomics of Japanese gut microbiomes)}"
READ_PAIRS="${READ_PAIRS:-1500000}"
THREADS="${THREADS:-4}"

# Use the gutgoose env tools without needing an activated shell.
export PATH="$HOME/miniforge3/envs/gutgoose/bin:$PATH"

mkdir -p data/raw data/clean data/microbe data/profile data/results

# --- stage 0: acquire + subsample (idempotent) ---
if [ ! -s data/raw/sample_R1.fastq.gz ]; then
  echo ">> stage 0: download + subsample $SAMPLE_ACC"
  prefetch "$SAMPLE_ACC" -O data/raw --max-size 30g
  fasterq-dump "$SAMPLE_ACC" -O data/raw --split-files -e "$THREADS" -p
  seqtk sample -s100 "data/raw/${SAMPLE_ACC}_1.fastq" "$READ_PAIRS" | gzip > data/raw/sample_R1.fastq.gz
  seqtk sample -s100 "data/raw/${SAMPLE_ACC}_2.fastq" "$READ_PAIRS" | gzip > data/raw/sample_R2.fastq.gz
fi

# --- stage 1: clean reads (fastp) ---
echo ">> stage 1: fastp"
fastp \
  -i data/raw/sample_R1.fastq.gz -I data/raw/sample_R2.fastq.gz \
  -o data/clean/clean_R1.fastq.gz -O data/clean/clean_R2.fastq.gz \
  --detect_adapter_for_pe --html data/results/fastp.html --json data/clean/fastp.json

# --- stage 2: remove human DNA (bowtie2; keep unaligned = microbial) ---
echo ">> stage 2: bowtie2 human-read removal"
bowtie2 -x data/db/human/GRCh38_noalt_as \
  -1 data/clean/clean_R1.fastq.gz -2 data/clean/clean_R2.fastq.gz \
  --un-conc-gz "data/microbe/microbe_R%.fastq.gz" \
  -p "$THREADS" -S /dev/null 2> data/microbe/bowtie2.log
echo "   human alignment summary:"; tail -1 data/microbe/bowtie2.log

# --- stage 3: identify taxa (MetaPhlAn4; --db_dir on 4.2.4) ---
echo ">> stage 3: MetaPhlAn4"
metaphlan data/microbe/microbe_R1.fastq.gz,data/microbe/microbe_R2.fastq.gz \
  --input_type fastq --db_dir data/db/metaphlan \
  --bowtie2out data/profile/metaphlan.bowtie2.bz2 \
  --nproc "$THREADS" -o data/profile/metaphlan.tsv
echo "   species detected: $(grep -c 's__' data/profile/metaphlan.tsv || true)"

# --- stage 6: assemble results.json (+ sanity gate) ---
echo ">> stage 6: assemble results.json"
SAMPLE_ACC="$SAMPLE_ACC" SAMPLE_SOURCE="$SAMPLE_SOURCE" READ_PAIRS="$READ_PAIRS" \
  python -m pipeline.assemble_results

echo ">> pipeline complete: data/results/results.json"
