import math
from pipeline.diversity import shannon, richness, evenness, diversity_from_metaphlan

def test_shannon_even_community():
    # 4 species each 25% -> Shannon = ln(4)
    assert math.isclose(shannon([25, 25, 25, 25]), math.log(4), rel_tol=1e-9)

def test_richness_ignores_zeros():
    assert richness([50, 50, 0, 0]) == 2

def test_evenness_even_community_is_one():
    assert math.isclose(evenness([25, 25, 25, 25]), 1.0, rel_tol=1e-9)

# Realistic MetaPhlAn4 output: 4 columns (clade, NCBI_tax_id, relative_abundance, additional_species).
# The relative abundance is column 3, NOT the last column.
REAL_TSV = (
    "#mpa_vJun23_CHOCOPhlAnSGB_202403\n"
    "#clade_name\tNCBI_tax_id\trelative_abundance\tadditional_species\n"
    "k__Bacteria\t2\t100.0\t\n"
    "k__Bacteria|p__Firmicutes|s__Faecalibacterium_prausnitzii\t2|1239|853\t30.0\t\n"
    "k__Bacteria|p__Bacteroidetes|s__Bacteroides_uniformis\t2|976|820\t70.0\t\n"
    "k__Bacteria|p__Bacteroidetes|s__Bacteroides_uniformis|t__SGB1836\t2|976|820|0\t70.0\t\n"
)

def test_diversity_reads_relative_abundance_column_not_last(tmp_path):
    p = tmp_path / "mp.tsv"; p.write_text(REAL_TSV)
    div = diversity_from_metaphlan(str(p))
    # only 2 species rows (kingdom + SGB t__ row excluded)
    assert div["richness"] == 2
    # Shannon of 30/70 split, computed from the real-abundance column (rounded to 3dp)
    assert div["shannon"] == round(shannon([30.0, 70.0]), 3)
