import pytest

from eh_mcp.core import HarnessError, Workspace


@pytest.fixture
def ws(tmp_path):
    w = Workspace(tmp_path / "learning")
    w.ensure_workspace()
    return w


STEPS = [
    {"id": "s1", "does": "plot eight pairs of brew time and bitterness", "concepts": ["scatter-plot"],
     "strong_version_shows": ["axes named with units"]},
    {"id": "s2", "does": "fit a line by eye and read its slope", "concepts": ["slope-as-rate"],
     "strong_version_shows": ["slope said as a rate"], "requires": ["s1"]},
    {"id": "s3", "does": "ask whether brew time causes bitterness", "concepts": ["correlation-vs-cause"],
     "strong_version_shows": ["one confound named"], "requires": ["s2"]},
]


def accept_interests(w):
    p = w.propose_profile_change("propose", {"interests": ["coffee"]})["proposed"]
    w.propose_profile_change("accept", proposal_id=p)


def test_a_fresh_learner_starts_learning_at_once(ws):
    s = ws.orient.where_am_i()
    assert s["suggested"]["move"] == "begin" and s["suggested"]["say"] == "Let's go"
    assert s["program"][0]["id"] == "calculus-foundations" and s["ask_later"][:4] == ["lesson_mode", "sociability", "mastery_mode", "depth_mode"]
    assert "learning_context" in s["ask_later"]
    assert s["onboarding_choices"]["lesson_mode"]["semi-structured"].startswith("short segments")
    assert s["onboarding_choices"]["sociability"]["guided"].startswith("work with a tutor")
    assert s["onboarding_choices"]["mastery_mode"]["both"].startswith("use written")
    assert "no calculus or code" in s["onboarding_choices"]["depth_mode"]["civic-overview"]
    assert s["onboarding_choices"]["learning_context"]["professional-growth"].startswith("build capability")
    assert (ws.root / "MAP.md").exists() and "What you can say" in (ws.root / "MAP.md").read_text()
    ws.orient.write_plan("rule", "How does the chain rule work?", STEPS)       # a plan without a goal is fine
    s = ws.orient.where_am_i()
    assert s["suggested"]["move"] == "continue" and "goal" in s["ask_later"] and "audience" in s["ask_later"]
    assert s["plan"]["steps"][0]["does"] == STEPS[0]["does"]


def test_fresh_topic_focus_calibrates_and_surfaces_relevant_standards(ws):
    ws.index.upsert("std:vectors", "standard", "HSN-VM.C.8 vectors matrices transformations",
                    {"scope": "reference", "tier": "pinned", "code": "HSN-VM.C.8",
                     "statement": "Represent transformations using vectors and matrices.",
                     "grade": "9-12", "domain": ["Geometry", "Transformations"],
                     "jurisdiction": "Multi-State", "license": "https://creativecommons.org/licenses/by/4.0/",
                     "attribution": "Example standards source"}, "standards:test")
    state = ws.knowledge._state()
    state["standards_source"] = {"folder": "/tmp/test-standards", "subject": "Mathematics", "pinned": 1}
    ws.knowledge._save(state)

    s = ws.orient.where_am_i(focus="Intro to Transformers and neural networks",
                             space="Intro to Transformers and NN")

    assert s["suggested"]["move"] == "begin"
    assert s["focus"] == "Intro to Transformers and neural networks"
    assert s["standards"]["loaded"]
    assert s["standards"]["matches"][0]["code"] == "HSN-VM.C.8"
    assert "vectors and matrices" in s["standards"]["matches"][0]["statement"]


def test_fresh_orientation_is_explicit_when_standards_are_not_loaded(ws):
    s = ws.orient.where_am_i(focus="transformers")
    assert s["suggested"]["move"] == "begin"
    assert s["standards"] == {"loaded": False, "query": "transformers", "matches": [],
                              "note": "No standards are loaded; do not claim they were checked."}


def test_reveal_without_a_prewritten_solution(ws):
    ws.orient.write_plan("rule", "q", STEPS)
    r = ws.reveal_solution("rule", "s1", "answer")
    assert r["content"] is None and "work it out now" in r["next"]
    assert ws.orient.where_am_i()["plan"]["steps"][0]["follow_on_owed"]
    ws.record_attempt("rule", "s1", "a sibling with other numbers", follow_on="sibling")
    assert not ws.orient.where_am_i()["plan"]["steps"][0]["follow_on_owed"]


def test_arc_then_plan_then_continue(ws):
    accept_interests(ws)
    ws.orient.set_arc("Understand the math inside a transformer",
                      [{"title": "Trace rates of change", "idea": "data-scientist:calculus-foundations", "project": "coffee"},
                       {"title": "Compare vectors", "idea": "data-scientist:vectors-dot-products"}], why="to read papers at work")
    s = ws.orient.where_am_i()
    assert s["suggested"]["move"] == "plan" and "rates of change" in s["suggested"]["why"].lower()
    ws.orient.write_plan("coffee", "Does a longer brew taste more bitter?", STEPS,
                         idea="data-scientist:calculus-foundations")
    s = ws.orient.where_am_i()
    assert s["suggested"] == {"move": "continue", "say": "Let's go",
                              "why": "pick up where you left off: plot eight pairs of brew time and bitterness"}
    ws.record_attempt("coffee", "s1", "x is minutes, y is bitterness 1-10")
    ws.set_status("coffee", "s1", "drafted", "tutor")
    c = ws.orient.where_am_i()["current"]
    assert [d["step"] for d in c["done"]] == ["s1"] and c["now"]["step"] == "s2" and c["next"]["step"] == "s3"
    assert ws.orient.where_am_i()["arc"]["path"][0]["state"] == "in progress"
    m = (ws.root / "MAP.md").read_text()
    assert "Understand the math inside a transformer" in m and "[~] Trace rates of change" in m


def test_arc_checks_ideas_and_keeps_history(ws):
    with pytest.raises(HarnessError):
        ws.orient.set_arc("x", [{"title": "y", "idea": "data-scientist:nope"}])
    ws.orient.set_arc("a", [{"title": "one"}])
    ws.orient.set_arc("b", [{"title": "two"}], change="Learner swapped the order")
    assert [h["change"] for h in ws.orient.get_arc()["arc"]["history"]] == ["Arc set.", "Learner swapped the order"]


def test_plan_revision_keeps_worked_steps(ws):
    ws.orient.write_plan("coffee", "q", STEPS)
    ws.record_attempt("coffee", "s2", "slope is about one point per minute")
    r = ws.orient.write_plan("coffee", "q", [STEPS[0], {**STEPS[2], "requires": ["s1"]}])
    assert r["kept_as_retired"] == ["s2"]
    prog = ws.get_progress("coffee")["steps"]
    assert prog["s2"]["retired"] and prog["s2"]["attempts"] == 1 and "s3" in prog
    with pytest.raises(HarnessError):
        ws.orient.write_plan("coffee", "q", [{**STEPS[1], "requires": ["s9"]}])
    with pytest.raises(HarnessError):
        ws.orient.write_plan("coffee", "q", [{"id": "s1", "does": "x", "concepts": ["c"]}])  # no strong version


def test_checkpoints_save_list_reopen_and_search(ws):
    ws.orient.write_plan("coffee", "q", STEPS)
    ws.record_attempt("coffee", "s2", "maybe the slope is bitterness per minute?")
    ws.orient.save_checkpoint("slope puzzle", "I think the slope is a rate but the units confuse me",
                              "work out the units of the slope together", project="coffee", step="s2",
                              open_question="why minutes on the bottom?")
    ws.orient.save_checkpoint("stopping", "done for today", "start s3", auto=True)
    lst = ws.orient.list_checkpoints()["checkpoints"]
    assert [c["label"] for c in lst] == ["stopping", "slope puzzle"]
    back = ws.orient.open_checkpoint("slope")
    assert back["checkpoint"]["open_question"] == "why minutes on the bottom?"
    assert back["step_now"]["attempts"] == 1 and back["recent_attempts"]
    hit = ws.search_memory("units confuse", scope="meta")["results"][0]
    assert hit["kind"] == "checkpoint"
    ws.orient.where_am_i()
    assert "**slope puzzle**" in (ws.root / "MAP.md").read_text()
    with pytest.raises(HarnessError):
        ws.orient.open_checkpoint("nothing like this")
    with pytest.raises(HarnessError):
        ws.orient.save_checkpoint("x", "", "y")


def test_program_lists_ideas_without_solutions(ws):
    p = ws.orient.get_program()
    assert [i["id"] for i in p["ideas"]][:2] == ["calculus-foundations", "vectors-dot-products"]
    assert p["title"] == "Mathematical data science for recommendation and post-training"
    assert all(i["foundation"] and i["converges_on_transformers"] for i in p["ideas"])
    assert len(p["modules"]) == 6 and [s["id"] for s in p["learning_stages"]] == ["math", "scratch", "package", "parity"]
    assert all(set(i["practice"]) == {"scratch", "package", "parity"} for i in p["ideas"])
    assert set(p["anchor_project"]["milestones"]) == {i["id"] for i in p["ideas"]}
    assert p["depth_modes"]["civic-overview"]["stages"] == ["math"] and p["civic_lens"]["recurring_questions"]
    assert p["default_arc"]["path"][-3]["idea"] == "dpo"
    assert "solution" not in str(p).lower()


def test_commitment_counts_as_cadence(ws):
    ws.orient.write_plan("coffee", "q", STEPS)
    assert not ws.orient.where_am_i()["setup"]["cadence"]
    ws.orient.set_commitment("coffee", "only when I ask")
    assert ws.orient.where_am_i()["setup"]["cadence"]
    assert "only when I ask" in (ws.project_dir("coffee") / "commitment.md").read_text()


def test_bookmarks_stay_few_and_can_be_refreshed_and_removed(ws):
    ws.orient.write_plan("coffee", "q", STEPS)
    for i in range(3):  # three stops: still one "where you stopped"
        r = ws.orient.save_checkpoint("stopped", f"stop {i}", "start s2", project="coffee", auto=True)
    assert r["replaced"] == ["stopped"]
    autos = [c for c in ws.orient.list_checkpoints()["checkpoints"] if c["auto"]]
    assert len(autos) == 1
    assert len([x for x in ws.search_memory("stop", scope="meta", kinds=["checkpoint"])["results"]]) == 1
    ws.orient.save_checkpoint("slope units", "units confuse me", "units together", project="coffee", step="s1")
    ws.orient.update_checkpoint("slope units", thinking="units make sense now", next_move="read the slope")
    assert ws.orient.open_checkpoint("slope units")["checkpoint"]["thinking"] == "units make sense now"
    ws.record_attempt("coffee", "s1", "done plotting")
    ws.set_status("coffee", "s1", "drafted", "tutor")
    lst = {c["label"]: c for c in ws.orient.list_checkpoints()["checkpoints"]}
    assert lst["slope units"]["resolved"]
    assert "slope units" not in (ws.orient.where_am_i() and (ws.root / "MAP.md").read_text())
    ask = ws.orient.remove_checkpoints(resolved=True)
    assert ask["would_remove"] == ["slope units"] and len(ws.orient.list_checkpoints()["checkpoints"]) == 2
    ws.orient.remove_checkpoints(resolved=True, learner_confirmed=True)
    assert [c["label"] for c in ws.orient.list_checkpoints()["checkpoints"]] == ["stopped"]


def test_many_named_bookmarks_suggest_tidying_but_still_save(ws):
    for i in range(13):
        r = ws.orient.save_checkpoint(f"b{i}", "t", "n")
    assert "consider_tidying" in r and r["saved"]
    assert len(ws.orient.list_checkpoints(limit=100)["checkpoints"]) == 13
