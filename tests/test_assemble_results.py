import pytest
from pipeline.assemble_results import parse_abundance, sanity_check

# realistic MetaPhlAn4 rows: clade, NCBI_tax_id, relative_abundance, additional_species
REAL_TSV = (
    "#mpa_vJun23\n"
    "#clade_name\tNCBI_tax_id\trelative_abundance\tadditional_species\n"
    "k__Bacteria\t2\t100.0\t\n"
    "k__Bacteria|p__Firmicutes|s__Faecalibacterium_prausnitzii\t2|1239|853\t4.2\t\n"
    "k__Bacteria|p__Bacteroidetes|s__Bacteroides_uniformis\t2|976|820\t8.1\t\n"
    "k__Bacteria|p__Bacteroidetes|s__Bacteroides_uniformis|t__SGB1836\t2|976|820|0\t8.1\t\n"
)

def test_parse_abundance_keeps_species_only(tmp_path):
    p = tmp_path / "mp.tsv"; p.write_text(REAL_TSV)
    rows = parse_abundance(str(p))
    assert {r["species"] for r in rows} == {
        "Faecalibacterium prausnitzii", "Bacteroides uniformis"}

def test_parse_abundance_reads_correct_column(tmp_path):
    p = tmp_path / "mp.tsv"; p.write_text(REAL_TSV)
    rows = parse_abundance(str(p))
    fp = next(r for r in rows if r["species"] == "Faecalibacterium prausnitzii")
    assert fp["rel_abundance_pct"] == 4.2  # column 3, not additional_species

def test_parse_excludes_kingdom_and_sgb_rows(tmp_path):
    p = tmp_path / "mp.tsv"; p.write_text(REAL_TSV)
    assert len(parse_abundance(str(p))) == 2

def test_sanity_check_rejects_too_few_species():
    with pytest.raises(ValueError):
        sanity_check([{"species": "x", "rel_abundance_pct": 100.0}], pathways=[])

def test_sanity_check_rejects_bad_sum():
    abundance = [{"species": f"sp{i}", "rel_abundance_pct": 1.0} for i in range(25)]
    with pytest.raises(ValueError):  # sums to 25, not ~100
        sanity_check(abundance, pathways=[])

def test_sanity_check_passes_realistic():
    abundance = [{"species": f"sp{i}", "rel_abundance_pct": 100 / 25} for i in range(25)]
    sanity_check(abundance, pathways=[])  # 25 species summing to 100 -> no raise
