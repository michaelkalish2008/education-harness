import pytest

from eh_mcp.core import HarnessError, Workspace

STEPS = [{"id": "s1", "does": "count clicks", "concepts": ["click-rate"], "strong_version_shows": ["a rate"]}]


@pytest.fixture
def ws(tmp_path):
    w = Workspace(tmp_path / "learning")
    w.ensure_workspace()
    w.orient.write_plan("clicks", "How sure is a click rate?", STEPS)
    return w


def test_empty_deck_says_what_becomes_a_card(ws):
    d = ws.review.deck()
    assert d["cards"] == [] and "note" in d


def test_deck_groups_by_concept_and_skips_open_questions(ws):
    ws.board.remember("shrinkage", "few views get pulled toward the prior", "clicks", "s1")
    ws.journal.annotate("pretend views weigh more when real views are few", "insight", "concept", "shrinkage")
    q = ws.journal.annotate("why root n?", "confusion", "concept", "standard error")
    ws.journal.annotate("variance is area, SE is the side", "insight", "concept", "standard error",
                        responds_to=q["saved"])
    ws.journal.annotate("still unsure about priors", "question", "concept", "prior")
    ws.journal.annotate("a click is not a preference", "insight", "step", "", "clicks", "s1")
    d = ws.review.deck()
    ids = {c["card"] for c in d["cards"]}
    shrink = next(c for c in d["cards"] if c["card"].endswith("shrinkage"))
    assert shrink["your_words"] and shrink["insights"] and shrink["projects"] == ["clicks"]
    se = next(c for c in d["cards"] if "standard" in c["card"])
    assert se["then_and_now"][0]["then"] == "why root n?"
    assert not any(c["card"].endswith(":prior") for c in d["cards"])   # an open question isn't a card
    assert any(c.startswith("note:") for c in ids)                     # a step insight is its own card
    assert d["never_reviewed"] == d["total"] == len(ids)


def test_marking_moves_a_card_to_the_back_and_keeps_their_words(ws):
    ws.board.remember("shrinkage", "pulled toward the prior")
    ws.board.remember("standard error", "shrinks with root n")
    first = ws.review.deck()["cards"][0]["card"]
    out = ws.review.mark(first, "said it again, shorter")
    assert out["times_reviewed"] == 1 and "kept" in out
    d = ws.review.deck()
    assert d["cards"][0]["card"] != first and d["cards"][-1]["card"] == first
    assert d["never_reviewed"] == 1
    assert any(w["text"].startswith("Run-through:") for w in d["cards"][-1]["your_words"])


def test_filters_and_unknown_card(ws):
    ws.board.remember("shrinkage", "pulled toward the prior", "clicks")
    ws.board.remember("variance", "average squared distance")
    assert [c["card"] for c in ws.review.deck(concept="shrinkage")["cards"]] == ["concept:shrinkage"]
    assert [c["card"] for c in ws.review.deck(project="clicks")["cards"]] == ["concept:shrinkage"]
    with pytest.raises(HarnessError):
        ws.review.mark("concept:nope")
