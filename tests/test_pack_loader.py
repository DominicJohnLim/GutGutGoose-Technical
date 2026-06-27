from knowledge.pack_loader import load_pack, card_keys

def test_load_pack_keys_are_namespaced(tmp_path):
    (tmp_path / "taxa").mkdir()
    (tmp_path / "taxa" / "bacteroides_uniformis.md").write_text(
        "# B. uniformis\n- key: taxa:bacteroides_uniformis\n")
    pack = load_pack(str(tmp_path))
    assert "taxa:bacteroides_uniformis" in card_keys(pack)

def test_top_level_files_are_not_cards(tmp_path):
    (tmp_path / "taxa").mkdir()
    (tmp_path / "taxa" / "x.md").write_text("# x\n")
    (tmp_path / "rules.md").write_text("# rules\n")  # top-level, not a card
    keys = card_keys(load_pack(str(tmp_path)))
    assert keys == {"taxa:x"}
