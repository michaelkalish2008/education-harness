import pytest

from eh_mcp.core import HarnessError, Workspace

STEPS = [
    {"id": "s1", "does": "push one coffee through a two-weight network", "concepts": ["matrix-multiplication"],
     "strong_version_shows": ["shapes named"]},
    {"id": "s2", "does": "send the error back with the chain rule", "concepts": ["chain-rule"],
     "strong_version_shows": ["one derivative by hand"], "requires": ["s1"], "standards_cited": ["HSF-BF.A.1.c"]},
]


@pytest.fixture
def ws(tmp_path):
    w = Workspace(tmp_path / "learning")
    w.ensure_workspace()
    w.orient.write_plan("net", "Can three numbers tell a good coffee from a bad one?", STEPS)
    w.write_solution("net", "s2", ["Start at the output."], "dL/dw = -0.4", "Multiply local slopes.",
                     [{"problem": "Same with w2"}, {"problem": "Three layers"}])
    return w


def test_half_formed_annotations_are_kept_and_can_be_answered_later(ws):
    j = ws.journal
    q = j.annotate("I don't get why the error goes *backwards*", kind="confusion", anchor="step",
                   project="net", step="s2")
    assert q["open"]
    assert j.open_questions()["total"] == 1
    j.annotate("oh: each layer only needs the slope from the layer after it", kind="insight",
               anchor="concept", ref="chain rule", project="net", responds_to=q["saved"])
    assert j.open_questions()["total"] == 0
    hit = ws.search_memory("error backwards", scope="reflection")["results"][0]
    assert hit["kind"] == "annotation" and hit["status"] == "resolved"
    assert ws.search_memory("error backwards")["results"] == []          # not mixed into domain
    with pytest.raises(HarnessError):
        j.annotate("  ")
    with pytest.raises(HarnessError):
        j.annotate("x", kind="grade")


def test_journal_brings_the_day_back_together(ws):
    j = ws.journal
    ws.record_attempt("net", "s2", "I multiplied 0.5 by 0.8 and got 0.4, sign unsure")
    ws.reveal_solution("net", "s2", "method")
    j.record_error("net", "s2", "added the two slopes instead of multiplying them", "procedure",
                   helped="drawing the path as a chain of boxes")
    j.annotate("feels like compound interest?", kind="opinion", project="net")
    ws.add_diary_entry("Long day but the boxes picture helped.")
    out = j.journal(write=True)
    d = out["days"][0]
    assert d["responses"][0]["text"].startswith("I multiplied")
    assert {"project": "net", "step": "s2", "saw": "method", "follow_on": "s2-f1"} in d["exercises"]
    assert d["content"][0]["does"] == "send the error back with the chain rule"
    assert "HSF-BF.A.1.c" in d["standards"]
    assert d["errors"][0]["helped"] == "drawing the path as a chain of boxes"
    assert d["annotations"][0]["text"] == "feels like compound interest?"
    assert d["diary"] == ["Long day but the boxes picture helped."]
    md = (ws.root / out["file"]).read_text()
    assert "Where it went sideways" in md and "feels like compound interest?" in md
    assert j.error_patterns()["by_kind"] == {"procedure": 1}


def test_journal_survives_a_rebuild(ws):
    ws.journal.annotate("gist: gradients flow back", kind="gist")
    ws.journal.record_error("net", "s1", "transposed the matrix", "notation")
    (ws.private / "index/memory.sqlite").unlink()
    ws.rebuild_index()
    kinds = {r["kind"] for r in ws.search_memory("gradients transposed matrix", scope="reflection")["results"]}
    assert kinds == {"annotation", "error"}
