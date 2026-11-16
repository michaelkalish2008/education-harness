"""The tour (default first lesson) and optional portfolio pieces."""
import pytest
import yaml

from eh_mcp.core import HarnessError, Workspace
from eh_mcp.tour import TOUR_PROJECT


@pytest.fixture
def ws(tmp_path):
    w = Workspace(tmp_path / "learning")
    w.ensure_workspace()
    return w


def finish_step(ws, step, text):
    ws.record_attempt(TOUR_PROJECT, step, text)
    ws.set_status(TOUR_PROJECT, step, "drafted", "tutor")


def test_new_learner_is_offered_the_tour_lazily(ws):
    s = ws.orient.where_am_i()
    assert s["suggested"]["move"] == "welcome" and s["suggested"]["say"] == "Let's learn"
    assert not ws.project_dir(TOUR_PROJECT).exists()          # nothing written until they start
    assert "Show me how this works" in s["welcome"]["starters"]
    assert "Show me how this works" in (ws.root / "MAP.md").read_text()


def test_tour_runs_as_a_real_lesson_and_then_hands_off(ws):
    out = ws.tour.start()
    assert out["project"] == TOUR_PROJECT and [x["id"] for x in out["plan"]["steps"]] == ["s1", "s2", "s3", "s4", "s5"]
    assert all(x["terms"] for x in out["plan"]["steps"])
    s = ws.orient.where_am_i()
    assert s["suggested"]["move"] == "continue" and s["current"]["project"] == TOUR_PROJECT
    assert s["tour"]["state"] == "started"
    finish_step(ws, "s1", "picked sourdough rise times; worked 2 doubling times by hand")
    ws.reveal_solution(TOUR_PROJECT, "s3", "hint")
    for st in ("s2", "s3", "s4"):
        finish_step(ws, st, f"used it on {st}")
    ws.orient.write_plan("rise", "Why does dough double?", [
        {"id": "s1", "does": "fit an exponential to five rise readings", "concepts": ["exponential"],
         "strong_version_shows": ["rate in own words"]}])
    finish_step(ws, "s5", "I want to understand exponential growth in baking")
    s = ws.orient.where_am_i()
    assert s["tour"]["state"] == "finished"
    assert s["suggested"]["move"] == "continue" and s["current"]["project"] == "rise"
    assert TOUR_PROJECT not in ws.share.retro_due()            # the tour ends in a plan, not a retro


def test_skipping_and_retaking(ws):
    ws.tour.skip()
    assert ws.orient.where_am_i()["suggested"]["move"] == "begin"
    ws.tour.start()                                            # "show me how this works" later
    assert ws.tour.state() == "started"
    ws.tour.start()                                            # idempotent: never re-seeds over work
    assert (ws.project_dir(TOUR_PROJECT) / "program.yaml").exists()


def test_existing_learners_are_not_pushed_into_the_tour(ws):
    ws.orient.write_plan("rule", "How does the chain rule work?", [
        {"id": "s1", "does": "differentiate (3x+1)^2", "concepts": ["chain-rule"],
         "strong_version_shows": ["outer and inner named"]}])
    assert ws.orient.where_am_i()["suggested"]["move"] == "continue"


STEPS = [{"id": "s1", "does": "score items by dot product", "concepts": ["dot-product"],
          "strong_version_shows": ["scores by hand"]},
         {"id": "s2", "does": "show it", "concepts": ["dot-product"], "format": "share-out",
          "strong_version_shows": ["own words"], "requires": ["s1"]}]


def test_github_portfolio_piece_from_learner_work(ws):
    ws.orient.write_plan("recs", "How do I score items?", STEPS)
    (ws.project_dir("recs") / "work" / "score.py").write_text("print(1*2 + 3*4)\n")
    (ws.project_dir("recs") / "solutions" / "s1.yaml").write_text("answer: 14\n")
    out = ws.share.build_portfolio("recs", "github", files={"README.md": "# Scoring\n\nMy words."},
                                   include=["work/score.py"], title="Dot-product scoring")
    dest = ws.project_dir("recs") / "portfolio" / "github"
    assert (dest / "README.md").exists() and (dest / "score.py").exists() and (dest / ".gitignore").exists()
    assert out["privacy_flags"] == [] and any("gh repo create" in x for x in out["publish"])
    man = yaml.safe_load((ws.project_dir("recs") / "portfolio" / "portfolio.yaml").read_text())
    assert man["pieces"]["github"]["title"] == "Dot-product scoring"
    assert ws.get_progress("recs")["steps"]["s2"]["attempts"]   # counts as share-out work
    with pytest.raises(HarnessError, match="Worked solutions"):
        ws.share.build_portfolio("recs", "github", include=["solutions/s1.yaml"])


def test_web_and_post_pieces_need_their_main_file_and_flag_privacy(ws):
    ws.orient.write_plan("recs", "How do I score items?", STEPS[:1])
    with pytest.raises(HarnessError, match="index.html"):
        ws.share.build_portfolio("recs", "web", files={"notes.md": "x"})
    out = ws.share.build_portfolio("recs", "web", files={"index.html": "<p>mail me@example.com</p>"})
    assert out["privacy_flags"] == ["index.html: contains an email address"]
    ws.share.build_portfolio("recs", "post", files={"post.md": "A short post from /Users/alex/learning"})
    with pytest.raises(HarnessError, match="plain path"):
        ws.share.build_portfolio("recs", "other", files={"../escape.md": "x"})
    with pytest.raises(HarnessError, match="target"):
        ws.share.build_portfolio("recs", "tiktok", files={"a.md": "x"})


def test_tour_and_portfolio_through_the_tools(tmp_path):
    from test_server import call
    from eh_mcp.server import build_server
    s = build_server(tmp_path / "learning")
    assert call(s, "where_am_i")["suggested"]["move"] == "welcome"
    started = call(s, "setup", action="tour")
    assert started["project"] == TOUR_PROJECT
    assert call(s, "setup")["tour"]["state"] == "started"
    call(s, "write_plan", project="recs", question="How do I score items?", steps=STEPS,
         audience="anyone on GitHub", audience_format="portfolio", audience_where="github")
    out = call(s, "save_doc", kind="portfolio", project="recs", target="github",
               files={"README.md": "# Scoring"})
    assert out["folder"] == "projects/recs/portfolio/github"
    shared = call(s, "note", kind="shared", project="recs", how="posted", where="GitHub",
                  link="https://github.com/example/recs", text="Posted the repo")
    assert shared["shared"]["link"] == "https://github.com/example/recs"
    chat = build_server(tmp_path / "learning", chatgpt=True)
    import asyncio
    assert {"setup", "save_doc"} <= {t.name for t in asyncio.run(chat.list_tools())}


def test_phrases_are_introduced_once_and_remembered(ws):
    assert ws.orient.where_am_i()["tour"]["introduced"] == []
    ws.tour.introduce("hint")
    out = ws.tour.introduce("Hint")                            # idempotent, case-insensitive
    assert out["introduced"] == ["hint"] and "note this" in out["not_yet"]
    assert ws.orient.where_am_i()["tour"]["introduced"] == ["hint"]
    assert ws.tour.state() == "none"                           # introducing a phrase isn't taking the tour
    with pytest.raises(Exception):
        ws.tour.introduce("teleport")


def test_introduced_through_the_tool(tmp_path):
    from test_server import call
    from eh_mcp.server import build_server
    s = build_server(tmp_path / "learning")
    assert call(s, "setup", action="introduced", feature="note this")["introduced"] == ["note this"]
