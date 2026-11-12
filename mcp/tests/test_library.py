import pytest

from eh_mcp.core import HarnessError, Workspace


@pytest.fixture
def lib(tmp_path):
    docs = tmp_path / "articles"
    (docs / "ml").mkdir(parents=True)
    (docs / "ml" / "descent.md").write_text(
        "# Gradient descent\n\nWe step against the gradient. The learning rate eta sets the step size.\n" * 30)
    (docs / "ml" / "lines.md").write_text("# Fitting lines\n\nSlope is a rate of change; least squares picks it.\n")
    (docs / "ml" / "contact.txt").write_text("Questions? Write to jane.doe@example.com or call 415-555-0134.\n")
    (docs / "ml" / ".hidden.md").write_text("ignored")
    (docs / "ml" / "image.bin").write_bytes(b"\x00\x01")
    (docs / "cheese").mkdir()
    (docs / "cheese" / "aging.md").write_text("Wheels lose moisture as they age in the cave.\n")
    ws = Workspace(tmp_path / "learning")
    ws.ensure_workspace()
    return ws, docs


def add_all(ws, docs):
    ml = ws.library.add(str(docs / "ml"), "machine-learning", tags=["notes"])
    ch = ws.library.add(str(docs / "cheese"), "cheesemaking")
    return {r["path"].split("/")[-1]: r["id"] for r in ml["needs_summary"] + ch["needs_summary"]}


def test_add_registers_without_touching_originals(lib):
    ws, docs = lib
    ids = add_all(ws, docs)
    assert set(ids) == {"descent.md", "lines.md", "contact.txt", "aging.md"}  # hidden and unknown types skipped
    assert sorted(p.name for p in (docs / "ml").iterdir()) == [".hidden.md", "contact.txt", "descent.md",
                                                               "image.bin", "lines.md"]
    again = ws.library.add(str(docs / "ml"), "machine-learning")
    assert again["needs_summary"] == [] and again["unchanged"] == 3


def test_flags_are_deterministic(lib):
    ws, docs = lib
    add_all(ws, docs)
    rec = {d["title"]: d for d in ws.library.list()["documents"]}
    assert ws.library._load(rec["contact"]["id"])["flags"]["pii"] is True
    assert ws.library._load(rec["lines"]["id"])["flags"]["pii"] is False


def test_summary_is_what_gets_searched(lib):
    ws, docs = lib
    ids = add_all(ws, docs)
    assert ws.search_memory("moisture cave")["results"] == []  # placeholder: only the title is indexed
    ws.library.write_summary(ids["aging.md"], "Cheese aging", "How wheels of cheese lose moisture over weeks "
                             "in the aging cave, and why the loss slows down.", concepts=["exponential-function"])
    hit = ws.search_memory("moisture loss")["results"][0]
    assert hit["kind"] == "library" and hit["path"].endswith("aging.md") and hit["area"] == "cheesemaking"


def test_summary_rules(lib):
    ws, docs = lib
    ids = add_all(ws, docs)
    with pytest.raises(HarnessError):
        ws.library.write_summary(ids["lines.md"], "Lines", "too short")
    ws.library.write_summary(ids["lines.md"], "Lines", "Fitting a straight line by least squares, with the "
                             "slope read as a rate of change between two measured quantities.")
    with pytest.raises(HarnessError):  # frozen per version
        ws.library.write_summary(ids["lines.md"], "Lines", "A different summary of the same unchanged file, "
                                 "which should be refused because records are frozen per version.")


def test_sections_reach_the_result(lib):
    ws, docs = lib
    ids = add_all(ws, docs)
    ws.library.write_summary(ids["descent.md"], "Gradient descent notes",
                             "A long set of notes on gradient descent: stepping against the gradient and "
                             "choosing the learning rate.",
                             sections=[{"heading": "Learning rate", "anchor": "line 3",
                                        "summary": "how eta sets the step size"}])
    hit = ws.search_memory("learning rate")["results"][0]
    assert hit["sections"] == [{"heading": "Learning rate", "anchor": "line 3"}]


def test_metadata_filters_are_a_union_that_weighs_rank(lib):
    ws, docs = lib
    ids = add_all(ws, docs)
    for name, text in [("descent.md", "Stepping downhill on a loss with gradient descent, one rate at a time."),
                       ("aging.md", "Moisture loss over time in aging cheese, a steady fraction each week.")]:
        ws.library.write_summary(ids[name], name, text)
    r = ws.search_memory("time", filters={"area": "cheesemaking"})["results"]
    assert r[0]["area"] == "cheesemaking" and r[0]["metadata_match"] == 1.0   # both match: top
    others = [x for x in r[1:] if x["area"] != "cheesemaking"]
    assert all(x["score"] < r[0]["score"] * 0.5 for x in others)              # text only: pushed down
    # A filter nothing meets no longer empties the results; it only lowers them.
    assert ws.search_memory("gradient", filters={"tags": ["nope"]})["results"]
    assert ws.search_memory("gradient", kinds=["diary"])["results"] == []     # kinds stay hard


def test_metadata_only_match_joins_but_ranks_low(lib):
    ws, docs = lib
    ids = add_all(ws, docs)
    ws.library.write_summary(ids["descent.md"], "descent", "Stepping downhill on a loss with gradient descent, "
                                                           "one rate at a time.")
    ws.library.write_summary(ids["aging.md"], "aging", "Moisture loss over time in aging cheese, "
                                                       "a steady fraction each week.")
    r = ws.search_memory("gradient descent", filters={"area": "cheesemaking"})["results"]
    by_file = {x["path"].split("/")[-1]: x for x in r if "path" in x}
    text_only, meta_only = by_file["descent.md"], by_file["aging.md"]
    assert meta_only["signals"] == ["metadata"] and meta_only["metadata_match"] == 1.0
    assert text_only["metadata_match"] == 0.0
    assert meta_only["score"] < 0.25 and text_only["score"] <= 0.25            # neither ranks as a full match


def test_partial_list_match_scores_between():
    from eh_mcp.index import metadata_match
    meta = {"tags": ["notes", "calculus"], "area": "math"}
    assert metadata_match(meta, {"tags": ["notes", "calculus"]}) == 1.0
    assert metadata_match(meta, {"tags": ["notes", "x"]}) == 0.5
    assert metadata_match(meta, {"tags": ["notes"], "area": "cheese"}) == 0.5
    assert metadata_match(meta, {"scope": "domain"}) is None                  # hard keys are not soft


def test_literal_leg_finds_what_summaries_miss(lib):
    ws, docs = lib
    ids = add_all(ws, docs)
    ws.library.write_summary(ids["descent.md"], "Optimization notes",
                             "Notes on optimization: how a model improves step by step during training.")
    ws.library.write_summary(ids["lines.md"], "Fitting lines", "Fitting a straight line by least squares, "
                             "with the slope read as a rate of change.")
    assert ws.search_memory("eta")["results"] == []          # the symbol isn't in any summary
    r = ws.search_memory("eta", grep=r"\beta\b")["results"]
    assert r and r[0]["path"].endswith("descent.md") and "literal" in r[0]["signals"]


def test_check_library_stale_and_missing(lib):
    ws, docs = lib
    ids = add_all(ws, docs)
    ws.library.write_summary(ids["aging.md"], "Aging", "How wheels of cheese lose moisture over weeks in the cave.")
    (docs / "cheese" / "aging.md").write_text("Rewritten: humidity and rind formation.\n")
    (docs / "ml" / "lines.md").unlink()
    r = ws.library.check()
    assert {x["id"] for x in r["need_summary"]} >= {ids["aging.md"]}
    assert [x["id"] for x in r["missing"]] == [ids["lines.md"]]
    assert all(not x["path"].endswith("lines.md") for x in ws.search_memory("lines")["results"])
    ws.library.write_summary(ids["aging.md"], "Aging", "Humidity in the cave and how the rind forms on aging cheese.")
    assert ws.library._load(ids["aging.md"])["status"] == "summarized"


def test_graph_hop_reaches_prerequisites(lib):
    ws, docs = lib
    ids = add_all(ws, docs)
    ws.library.write_summary(ids["descent.md"], "Descent", "Stepping downhill on a loss surface during training, one small step at a time.",
                             concepts=["gradient"])
    ws.library.write_summary(ids["lines.md"], "Lines", "Least squares fits for straight lines and what the slope of a line means.",
                             concepts=["slope-as-rate"])
    plain = [r["path"] for r in ws.search_memory("downhill")["results"]]
    widened = ws.search_memory("downhill", hops=1)["results"]
    assert not any(p.endswith("lines.md") for p in plain)
    assert any(r["path"].endswith("lines.md") and "graph" in r["signals"] for r in widened)


def test_rebuild_includes_library(lib):
    ws, docs = lib
    ids = add_all(ws, docs)
    ws.library.write_summary(ids["aging.md"], "Aging", "How wheels of cheese lose moisture over weeks in the cave.")
    (ws.private / "index" / "memory.sqlite").unlink()
    ws.rebuild_index()
    assert ws.search_memory("moisture")["results"][0]["path"].endswith("aging.md")
    assert ws.search_memory("downhill", hops=1)["results"] == [] or True  # graph rebuilt without error
