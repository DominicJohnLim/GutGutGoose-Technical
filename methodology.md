# Methodology

A patient-facing gut-health report was generated from a real shotgun-metagenomic stool
sample through a reproducible, version-pinned pipeline spanning quality control,
taxonomic and functional profiling, community-scale metabolic modeling, and a grounded
natural-language reporting layer. The clinical persona is synthetic; all measurements
derive from a real public sequencing sample.

## 1. Sequence data and preprocessing

A publicly available human stool whole-genome shotgun metagenome (NCBI SRA / ENA accession
`DRR042265`, study PRJDB3601) was used as the measured input. Generating reads de novo was
explicitly avoided: synthetic reads lacking true marker-gene content do not classify and
would yield an empty profile, so only the patient persona is synthetic while the sequencing
data is authentic. Reads were subsampled with `seqtk` for rapid iteration and quality- and
adapter-trimmed with **fastp** [1]. Host (human) reads were removed by alignment to the
GRCh38 reference with **Bowtie2** [2], retaining unaligned (microbial) reads; this also
functions as a privacy step. The sample was found to be largely host-depleted upstream,
consistent with common practice for public stool datasets.

## 2. Taxonomic profiling

Species-level composition was determined with **MetaPhlAn 4** [3], which maps reads to
clade-specific marker genes. The marker-gene approach was selected over k-mer classification
because it yields the relative-abundance estimates required downstream and exhibits a lower
false-positive rate. Profiling recovered 47 species, with ~93% of reads classified and the
remaining fraction reported explicitly as unclassified. An automated sanity gate enforces
that abundances and the unclassified fraction sum to ~100% before any report is produced.

## 3. Functional profiling

Community functional potential was characterized with **HUMAnN 3** [4], which quantifies
gene families and MetaCyc metabolic pathways. To satisfy HUMAnN's taxonomic-profile
dependency, a version-matched MetaPhlAn database (`vJun23`) was used for the prescreen.
Profiling yielded 433 pathways spanning amino-acid biosynthesis, central carbohydrate
metabolism, and nucleotide salvage.

## 4. Community diversity

Alpha-diversity (Shannon index, species richness, evenness) was computed directly from the
species abundance table. Diversity is reported with explicit context that reduced diversity
is not inherently pathological, consistent with dietary and population variation reported in
the literature.

## 5. Genome-scale metabolic modeling

Predicted metabolic output was estimated with **MICOM** [5], which constructs a
community-scale constraint-based model from the abundance table using the **AGORA**
genome-scale reconstructions [6]. Community models were built at genus level and covered
~85% of the sample by abundance. Growth was simulated under curated **Virtual Metabolic
Human** diet media [7] (average, high-fiber, and low-fiber/high-fat) using a cooperative
trade-off objective. Short-chain fatty acid output, in particular butyrate, was quantified
as gross community production; net boundary flux is suppressed by intra-community
cross-feeding and is therefore not an informative production signal. The metabolic layer is
framed as a dietary counterfactual: holding the measured community fixed, predicted SCFA
output is compared across diets to estimate the directional effect of a fiber-oriented
intervention. Predictions are presented as modeled, not prescriptive.

## 6. In silico validation

Pipeline accuracy was assessed against known ground truth using simulated data.
**InSilicoSeq** [8] generated synthetic shotgun reads from real reference genomes at
defined compositions. A benchmark cohort of 30 independent communities (n ≥ 30) was
generated, processed through the taxonomic pipeline, and compared to the designed input.
Across the cohort, mean species recall was **96%** at **100% precision** (no false
positives), with a mean abundance rank correlation of **ρ = 0.78** (SD 0.10). Because
MetaPhlAn profiling is deterministic, identical inputs
yield identical profiles, establishing reproducibility. Validation at scale is scoped to
the taxonomic/abundance step; the functional and metabolic layers are presented as
demonstrations on the measured sample.

## 7. Report generation

Quantitative results were translated into a plain-language report by a large language model
under a constrained, grounded generation protocol. Rather than fine-tuning or live
retrieval, a curated knowledge base of taxon and concept cards (each with reference ranges
and citations) was supplied at generation time, and the model was instructed to assert
health claims only from this base, attaching a card identifier to each claim. An automated
validator rejects any report whose claims reference an absent card, ensuring every statement
is grounded. This design treats hallucination as a verifiable correctness constraint rather
than a probabilistic risk; grounding, not model scale, is the safety mechanism. Knowledge
claims regarding individual taxa (e.g., *Faecalibacterium prausnitzii* as a primary butyrate
producer [9, 10]; *Ruminococcus bromii* as a keystone resistant-starch degrader [11]) are
drawn from the curated, cited knowledge base.

## References

1. Chen S, Zhou Y, Chen Y, Gu J. fastp: an ultra-fast all-in-one FASTQ preprocessor.
   *Bioinformatics.* 2018;34(17):i884–i890.
2. Langmead B, Salzberg SL. Fast gapped-read alignment with Bowtie 2. *Nat Methods.*
   2012;9(4):357–359.
3. Blanco-Míguez A, et al. Extending and improving metagenomic taxonomic profiling with
   uncharacterized species using MetaPhlAn 4. *Nat Biotechnol.* 2023;41:1633–1644.
4. Beghini F, et al. Integrating taxonomic, functional, and strain-level profiling of
   diverse microbial communities with bioBakery 3. *eLife.* 2021;10:e65088.
5. Diener C, Gibbons SM, Resendis-Antonio O. MICOM: Metagenome-Scale Modeling To Infer
   Metabolic Interactions in the Gut Microbiota. *mSystems.* 2020;5(1):e00606-19.
6. Magnúsdóttir S, et al. Generation of genome-scale metabolic reconstructions for 773
   members of the human gut microbiota. *Nat Biotechnol.* 2017;35(1):81–89.
7. Noronha A, et al. The Virtual Metabolic Human database: integrating human and gut
   microbiome metabolism with nutrition and disease. *Nucleic Acids Res.*
   2019;47(D1):D614–D624.
8. Gourlé H, Karlsson-Lindsjö OE, Hayer J, Bongcam-Rudloff E. Simulating Illumina
   metagenomic data with InSilicoSeq. *Bioinformatics.* 2019;35(3):521–522.
9. Sokol H, et al. Faecalibacterium prausnitzii is an anti-inflammatory commensal bacterium
   identified by gut microbiota analysis of Crohn disease patients. *PNAS.*
   2008;105(43):16731–16736.
10. Lopez-Siles M, Duncan SH, Garcia-Gil LJ, Martinez-Medina M. Faecalibacterium
    prausnitzii: from microbiology to diagnostics and prognostics. *ISME J.*
    2017;11:841–852.
11. Ze X, Duncan SH, Louis P, Flint HJ. Ruminococcus bromii is a keystone species for the
    degradation of resistant starch in the human colon. *ISME J.* 2012;6(8):1535–1543.
