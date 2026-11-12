import pytest

from eh_mcp.core import HarnessError, Workspace


@pytest.fixture
def ws(tmp_path):
    w = Workspace(tmp_path / "learning")
    w.ensure_workspace()
    w.orient.write_plan("network", "Can three numbers tell a good coffee from a bad one?", [
        {"id": "s1", "does": "push one example through a tiny network", "concepts": ["matrix-multiplication"],
         "strong_version_shows": ["shapes named"]},
        {"id": "s2", "does": "send the error back with the chain rule", "concepts": ["chain-rule", "backpropagation"],
         "strong_version_shows": ["one derivative by hand"], "requires": ["s1"]}])
    return w


def test_remember_then_recall_by_plain_name(ws):
    ws.board.remember("chain rule", "Derivatives multiply along the path: outer times inner.", "network", "s2")
    r = ws.board.recall("the chain rule")
    assert r["concept"] == "chain-rule"
    assert r["your_notes"][0]["text"].startswith("Derivatives multiply")
    assert r["seen_in"] == [{"project": "network", "step": "s2", "does": "send the error back with the chain rule",
                             "status": "not started"}]
    assert isinstance(r["builds_on"], list)
    hit = ws.search_memory("outer times inner", scope="reflection")["results"][0]
    assert hit["kind"] == "concept_note"
    assert ws.board.list_concepts()["concepts"][0]["concept"] == "chain-rule"


def test_recall_of_something_new_says_so(ws):
    assert "Nothing yet" in ws.board.recall("fourier transform")["note"]


def test_concept_notes_survive_a_rebuild(ws):
    ws.board.remember("chain-rule", "outer times inner")
    (ws.private / "index/memory.sqlite").unlink()
    ws.rebuild_index()
    assert ws.search_memory("outer inner", scope="reflection")["results"][0]["kind"] == "concept_note"


def test_plain_names_map_without_guessing(ws):
    assert ws.board._slug("partial derivatives") == "partial-derivative"
    assert ws.board._slug("rate") == "rate"            # one word never captures 'slope as a rate'
