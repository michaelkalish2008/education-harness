import json

import pytest

from eh_mcp.core import HarnessError, Workspace

CCBY = "https://creativecommons.org/licenses/by/4.0/"
STDS = [
    ("u1", "HSS-ID.A.2", "Use statistics appropriate to the shape of the data distribution to compare center "
                         "and spread of two or more different data sets."),
    ("u2", "HSS-CP.A.3", "Understand the conditional probability of A given B as P(A and B)/P(B)."),
    ("u3", "HSS-IC.B.4", "Use data from a sample survey to estimate a population proportion; develop a margin "
                         "of error through the use of simulation models for random sampling."),
    ("u4", "HSG-CO.A.1", "Know precise definitions of angle, circle, perpendicular line, parallel line."),
]
STEPS = [
    {"id": "s1", "does": "compare click spread for two items with a sample survey",
     "concepts": ["conditional probability"], "strong_version_shows": ["names the spread"],
     "standards_cited": ["HSS-ID.A.2"]},
    {"id": "s2", "does": "put a margin of error on the click rate", "concepts": ["sample proportion"],
     "strong_version_shows": ["interval in words"], "requires": ["s1"], "standards_cited": ["HSS-IC.B.4"]},
]


def load(w, tmp_path, rows=STDS):
    kg = tmp_path / "kg"
    kg.mkdir(exist_ok=True)
    (kg / "StandardsFrameworkItem.json").write_text("\n".join(json.dumps({
        "caseIdentifierUUID": u, "statementCode": code, "description": text, "jurisdiction": "Multi-State",
        "academicSubject": "Mathematics", "license": CCBY, "attributionStatement": "attr"})
        for u, code, text in rows) + "\n")
    w.knowledge.load_standards(str(kg))


@pytest.fixture
def ws(tmp_path):
    w = Workspace(tmp_path / "learning")
    w.ensure_workspace()
    load(w, tmp_path)
    return w


def test_planning_writes_the_sidecar_with_cited_and_concept_linked_standards(ws):
    out = ws.orient.write_plan("clicks", "Will a user click?", STEPS)
    aligned = {a["code"]: a for a in out["standards"]["aligned"]}
    assert aligned["HSS-ID.A.2"]["steps"] == ["s1"]
    assert aligned["HSS-CP.A.3"]["steps"] == ["s1"]   # program link for "conditional probability"
    assert (ws.root / "projects/clicks/standards.yaml").exists()
    assert all(c["code"] not in aligned for c in out["standards"]["candidates_to_review"])


def test_candidates_are_retrieved_once_and_reviewed_not_re_searched(ws):
    ws.orient.write_plan("clicks", "Will a user click?", STEPS)
    data = ws.alignment.read("clicks")
    first = [c["code"] for c in data["candidates"]]
    ws.orient.write_plan("clicks", "Will a user click?", STEPS)   # replanning does not search again
    assert [c["code"] for c in ws.alignment.read("clicks")["candidates"]] == first
    if first:
        ws.alignment.manage("review", "clicks", code=first[0], decision="decline")
        assert ws.alignment.summary("clicks")["pending_review"] == [
            {"code": c["code"], "statement": c["statement"], "step": c["step"]}
            for c in ws.alignment.read("clicks")["candidates"] if c["review"] == "pending"]


def test_drafting_marks_exercised_and_reports_read_only_the_sidecar(ws, tmp_path):
    ws.orient.write_plan("clicks", "Will a user click?", STEPS)
    ws.record_attempt("clicks", "s1", "B has more views so less spread")
    r = ws.set_status("clicks", "s1", "drafted", "tutor")
    assert set(r["standards_exercised"]) == {"HSS-ID.A.2", "HSS-CP.A.3"}
    ws.alignment.manage("add", "clicks", step="s1", code="HSG-CO.A.1", evidence="I drew the interval as a line")
    first = ws.reports.report_evidence()["standards"]
    assert {r["code"] for r in first["exercised"]} == {"HSS-ID.A.2", "HSS-CP.A.3", "HSG-CO.A.1"}
    assert first["ahead"] == ["HSS-IC.B.4"]
    added = next(r for r in first["exercised"] if r["code"] == "HSG-CO.A.1")
    assert added["evidence"][0]["text"] == "I drew the interval as a line"
    # A different standards set loaded later does not change what was recorded.
    load(ws, tmp_path, [("u9", "HSS-CP.A.3", "A reworded statement.")])
    again = ws.reports.report_evidence()["standards"]
    assert [(r["code"], r["statement"]) for r in again["exercised"]] == \
           [(r["code"], r["statement"]) for r in first["exercised"]]


def test_catalog_reads_the_sidecar(ws):
    ws.orient.write_plan("clicks", "Will a user click?", STEPS)
    ws.record_attempt("clicks", "s1", "B has more views so less spread")
    ws.set_status("clicks", "s1", "drafted", "tutor")
    data = ws.catalog.data()
    st = next(x for x in data["items"] if x["id"] == "project:clicks")["standards"]
    assert [c["code"] for c in st["covered"]] == ["HSS-CP.A.3", "HSS-ID.A.2"]  # data() keeps statements
    assert [a["code"] for a in st["ahead"]] == ["HSS-IC.B.4"]
    assert data["analytics"]["standards"]["ahead_count"] == 1 and data["analytics"]["standards"]["attribution"]


def test_exercised_history_cannot_be_dropped(ws):
    ws.orient.write_plan("clicks", "Will a user click?", STEPS)
    ws.record_attempt("clicks", "s1", "work")
    ws.set_status("clicks", "s1", "drafted", "tutor")
    with pytest.raises(HarnessError):
        ws.alignment.manage("drop", "clicks", code="HSS-ID.A.2")
    ws.alignment.manage("drop", "clicks", code="HSS-IC.B.4")
    assert "HSS-IC.B.4" not in {r["code"] for r in ws.alignment.read("clicks")["standards"]}


def test_projects_planned_before_sidecars_are_backfilled_once(ws):
    ws.orient.write_plan("clicks", "Will a user click?", STEPS)
    ws.record_attempt("clicks", "s1", "work")
    ws.set_status("clicks", "s1", "drafted", "tutor")
    ws.alignment.path("clicks").unlink()
    sm = ws.alignment.summary("clicks")
    assert sm["backfilled"] and {r["code"] for r in sm["exercised"]} == {"HSS-ID.A.2", "HSS-CP.A.3"}


def test_without_standards_nothing_is_claimed(tmp_path):
    w = Workspace(tmp_path / "learning")
    w.orient.write_plan("clicks", "Will a user click?", STEPS)
    st = next(x for x in w.catalog.data()["items"] if x["id"] == "project:clicks")["standards"]
    assert st["loaded"] is False and st["covered"] == []


def test_a_candidate_goes_to_the_step_that_ranks_it_highest(ws):
    steps = [{"id": "a", "does": "define the click event and conditional probability", "concepts": ["events"],
              "strong_version_shows": ["names the event"]},
             {"id": "b", "does": "estimate a population proportion with a margin of error from a sample survey",
              "concepts": ["margin of error"], "strong_version_shows": ["interval"], "requires": ["a"]}]
    out = ws.orient.write_plan("q", "Will a user click?", steps)
    cand = next(c for c in out["standards"]["candidates_to_review"] if c["code"] == "HSS-IC.B.4")
    assert cand["step"] == "b"
