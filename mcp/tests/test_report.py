import json

import pytest

from eh_mcp.core import HarnessError, Workspace

CCBY = "https://creativecommons.org/licenses/by/4.0/"
STEPS = [
    {"id": "s1", "does": "push one coffee through a tiny network", "concepts": ["matrix-multiplication"],
     "strong_version_shows": ["shapes named"]},
    {"id": "s2", "does": "send the error back with the chain rule", "concepts": ["chain-rule"],
     "strong_version_shows": ["one derivative by hand"], "requires": ["s1"], "standards_cited": ["MP7", "HSF-BF.A.1.c"]},
]


@pytest.fixture
def ws(tmp_path):
    w = Workspace(tmp_path / "learning")
    w.ensure_workspace()
    kg = tmp_path / "kg"
    kg.mkdir()
    (kg / "StandardsFrameworkItem.json").write_text(json.dumps({
        "caseIdentifierUUID": "u-mp7", "statementCode": "MP7", "description": "Look for and make use of structure.",
        "jurisdiction": "Multi-State", "academicSubject": "Mathematics", "license": CCBY,
        "attributionStatement": "attr"}) + "\n")
    w.knowledge.load_standards(str(kg))
    w.orient.set_arc("Read transformer papers at work", [{"title": "A tiny network", "project": "net"},
                                                         {"title": "A tiny transformer"}], why="to help my team",
                     lens="math")
    w.orient.write_plan("net", "Can three numbers tell good coffee from bad?", STEPS)
    return w


def test_evidence_covers_growth_strengths_sociability_and_opportunities(ws):
    j = ws.journal
    q = j.annotate("why does the error go backwards??", kind="confusion", anchor="step", project="net", step="s2")
    ws.record_attempt("net", "s1", "a 1x3 times a 3x2 gives a 1x2")
    ws.set_status("net", "s1", "drafted", "tutor")
    j.annotate("each layer only needs the slope after it", kind="insight", project="net", responds_to=q["saved"])
    j.annotate("is momentum like a ball rolling?", kind="question")
    j.record_error("net", "s2", "added slopes instead of multiplying", "procedure", helped="boxes")
    j.record_error("net", "s2", "dropped a minus sign", "arithmetic")
    ws.record_attempt("net", "s2", "dL/dw is the product of the local slopes")
    ws.set_status("net", "s2", "drafted", "tutor")
    ws.reports.record_shared("explained", "Walked my sister through the boxes picture", who="my sister",
                             project="net", step="s2")
    e = ws.reports.report_evidence()
    g = e["growth"]
    assert [b["step"] for b in g["built"]] == ["s1", "s2"]
    assert g["confusions_answered"][0]["then"] == "why does the error go backwards??"
    assert e["sociability"]["count"] == 1 and e["sociability"]["shared"][0]["who"] == "my sister"
    assert {"text": "is momentum like a ball rolling?"}.items() <= e["opportunities"]["still_open"][0].items()
    assert e["opportunities"]["concepts_with_repeated_slips"] == {"chain-rule": 2}
    assert e["opportunities"]["next_on_arc"] == "A tiny transformer"
    assert e["where_it_leads"]["why"] == "to help my team"
    assert e["strengths_evidence"]["practices_touched"] == [{"code": "MP7", "text": "Look for and make use of structure."}]
    assert "HSF-BF.A.1.c" in e["standards_touched"] and e["attribution"]
    assert "score" not in json.dumps(e).lower() and "grade" not in json.dumps(e["growth"]).lower()


def test_reports_save_list_and_set_the_next_period(ws):
    r = ws.reports.save_report("You built your first network...", "2026-10-01", "2026-11-12", project="net")
    assert ws.reports.list_reports()["reports"][0]["until"] == "2026-11-12"
    assert ws.reports.report_evidence()["period"]["since"] == "2026-11-12"   # next report starts here
    assert ws.search_memory("first network", scope="reflection")["results"][0]["kind"] == "report"
    with pytest.raises(HarnessError):
        ws.reports.save_report(" ", "a", "b")
    with pytest.raises(HarnessError):
        ws.reports.record_shared("bragged", "x")
