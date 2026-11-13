import json

import pytest

from eh_mcp.core import Workspace
from eh_mcp.journey import PLACEHOLDER, template_path

STEPS = [
    {"id": "s1", "does": "count clicks in ten views", "concepts": ["click-rate"], "strong_version_shows": ["a rate"]},
    {"id": "s2", "does": "square the distances", "concepts": ["variance"], "strong_version_shows": ["a variance"]},
]


@pytest.fixture
def ws(tmp_path):
    w = Workspace(tmp_path / "learning")
    w.ensure_workspace()
    return w


def test_template_ships_with_a_placeholder():
    assert PLACEHOLDER in template_path().read_text()


def test_journey_gathers_goals_steps_and_every_kind_of_note(ws):
    ws.orient.write_plan("clicks", "How sure is a click rate?", STEPS)
    ws.orient.set_arc("Understand recommenders", [{"title": "Probability", "project": "clicks"},
                                                  {"title": "Attention"}], name="recs")
    ws.record_attempt("clicks", "s1", "3 of 10 is 0.3")
    ws.journal.annotate("why square it?", "question", "step", "", "clicks", "s2")
    ws.journal.annotate("explorer: https://claude.ai/artifact/abc.", "gist", "day")
    ws.board.remember("standard error", "shrinks with root n", "clicks", "s2")
    ws.add_diary_entry("walk session", project="clicks")
    d = ws.journey.data()
    arc = d["arcs"][0]
    assert [s["title"] for s in arc["path"]] == ["Probability", "Attention"]
    assert arc["path"][0]["state"] == "in progress" and arc["path"][1]["state"] == "not started"
    assert d["current"] == {"project": "clicks", "step": "s1"}
    kinds = {n["kind"] for n in d["notes"]}
    assert {"attempt", "question", "gist", "keep", "diary"} <= kinds
    assert any(n["open"] for n in d["notes"] if n["kind"] == "question")
    assert d["links"][0]["url"] == "https://claude.ai/artifact/abc"
    assert d["projects"][0]["placed"] is True


def test_where_am_i_writes_a_page_with_the_data_inside(ws):
    ws.orient.write_plan("clicks", "How sure is a click rate? </script>", STEPS)
    ws.orient.where_am_i()
    page = (ws.root / "JOURNEY.html").read_text()
    assert PLACEHOLDER not in page
    raw = page.split('id="journey-data" type="application/json">', 1)[1].split("</script>", 1)[0]
    data = json.loads(raw)                     # the </ in the question is escaped, so the page stays whole
    assert data["projects"][0]["question"].endswith("</script>")
    assert data["projects"][0]["placed"] is False   # not pinned to a goal: shown as a side trail


def test_artifact_link_is_remembered(ws):
    ws.journey.set_link("https://claude.ai/artifact/xyz")
    assert ws.journey.data()["artifact"] == "https://claude.ai/artifact/xyz"


def test_where_am_i_tool_returns_the_journey_on_request(tmp_path):
    import asyncio
    from eh_mcp.server import build_server
    s = build_server(tmp_path / "learning")
    r = asyncio.run(s.call_tool("where_am_i", {"journey": True}))
    content = r.content if hasattr(r, "content") else r[0]
    payload = json.loads(content[0].text)
    assert payload["journey"]["template"].endswith("journey.html")
    assert "arcs" in payload["journey"]["data"]
