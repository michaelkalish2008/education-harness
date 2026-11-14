"""The tool surface, called through MCP as the app calls it."""
import asyncio
import json
import time

import pytest

from eh_mcp.server import build_server


def call(s, name, **kw):
    r = asyncio.run(s.call_tool(name, kw))
    content = r.content if hasattr(r, "content") else r[0]
    return json.loads(content[0].text)


@pytest.fixture
def s(tmp_path):
    return build_server(tmp_path / "learning")


def test_the_surface_is_small(s):
    names = {t.name for t in asyncio.run(s.list_tools())}
    assert names == {"where_am_i", "set_arc", "write_plan", "note", "look_back", "reveal", "set_status",
                     "bookmark", "save_doc", "profile", "library", "setup", "check_links", "catalog"}


def test_lazy_first_session_then_coming_back(s):
    first = call(s, "where_am_i")
    assert first["suggested"]["move"] == "begin"
    steps = [{"id": "s1", "does": "differentiate (3x+1)^2 by the chain rule", "concepts": ["chain-rule"],
              "strong_version_shows": ["outer and inner named"]},
             {"id": "s2", "does": "explain it to a coworker", "concepts": ["chain-rule"], "format": "share-out",
              "strong_version_shows": ["own words"], "requires": ["s1"]}]
    call(s, "write_plan", project="chain", question="Why does the chain rule multiply?", steps=steps,
         audience="a coworker")
    call(s, "note", kind="confusion", text="why multiply and not add?", project="chain", step="s1")
    call(s, "note", kind="attempt", text="2(3x+1) times 3", project="chain", step="s1")
    assert call(s, "reveal", project="chain", step="s1", what="answer")["content"] is None
    call(s, "set_status", project="chain", step="s1", status="drafted")
    call(s, "note", kind="keep", concept="chain rule", text="outer slope times inner slope")
    call(s, "bookmark", action="save", label="stopped", thinking="multiplying makes sense now",
         next_move="explain it to a coworker", project="chain", step="s2", auto=True)
    back = call(s, "where_am_i")
    assert back["suggested"]["move"] == "continue" and back["current"]["now"]["step"] == "s2"
    assert back["open_questions"]["open"][0]["text"] == "why multiply and not add?"
    assert back["checkpoints"][0]["label"] == "stopped"
    assert "goal" in back["ask_later"]
    assert call(s, "look_back", concept="chain rule")["your_notes"][0]["text"] == "outer slope times inner slope"
    assert call(s, "look_back", query="multiply")["results"]
    call(s, "note", kind="shared", text="walked my coworker through it", who="a coworker", how="explained",
         project="chain")
    assert call(s, "look_back", kind="report", project="chain")["sociability"]["count"] >= 1
    assert call(s, "note", kind="poem", text="x")["refused"]


def test_plan_preserves_public_source_provenance(s):
    steps = [{"id": "s1", "does": "compare two classifiers", "concepts": ["classification"],
              "strong_version_shows": ["explains the different boundaries"]}]
    call(s, "write_plan", project="source-plan", question="How do classifiers differ?", steps=steps,
         sources=[{"url": "https://open.example.edu/course/", "title": "ML course", "library_id": "u123"}])
    back = call(s, "where_am_i")
    assert back["current"]["question"] == "How do classifiers differ?"


def test_calls_are_fast(s):
    call(s, "write_plan", project="p", question="q", steps=[{"id": "s1", "does": "d", "concepts": ["c"],
                                                            "strong_version_shows": ["x"]}])
    for i in range(20):
        call(s, "note", kind="thought", text=f"thought {i}", project="p", step="s1")
    t = time.perf_counter()
    for _ in range(10):
        call(s, "where_am_i")
        call(s, "note", kind="attempt", text="work", project="p", step="s1")
    per_call = (time.perf_counter() - t) / 20
    assert per_call < 0.15, per_call


def test_review_run_through_through_the_tools(s):
    call(s, "note", kind="keep", concept="shrinkage", text="few views get pulled toward the prior")
    deck = call(s, "look_back", kind="review")
    card = deck["cards"][0]["card"]
    assert card == "concept:shrinkage" and deck["never_reviewed"] == 1
    out = call(s, "note", kind="review", responds_to=card, text="sparse items lean on the prior")
    assert out["times_reviewed"] == 1
    assert call(s, "look_back", kind="review")["never_reviewed"] == 0
