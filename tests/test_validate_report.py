from report.validate_report import validate

def test_flags_missing_citation():
    report = {"findings": [{"claim": "x", "citation": "taxa:ghost"}]}
    assert validate(report, {"taxa:real"}) == ["taxa:ghost"]

def test_passes_when_all_cited():
    report = {"findings": [{"claim": "x", "citation": "taxa:real"}]}
    assert validate(report, {"taxa:real"}) == []

def test_multiple_findings_flags_only_ungrounded():
    report = {"findings": [
        {"claim": "a", "citation": "taxa:real"},
        {"claim": "b", "citation": "taxa:ghost"},
    ]}
    assert validate(report, {"taxa:real"}) == ["taxa:ghost"]
