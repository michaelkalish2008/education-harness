import yaml
import pytest

from eh_mcp.core import HarnessError, Workspace


@pytest.fixture
def ws(tmp_path):
    w = Workspace(tmp_path / "learning")
    w.init_project("trees", question="Do trees cool neighborhoods?")
    p = w.root / "projects/trees/program.yaml"
    plan = yaml.safe_load(p.read_text())
    plan["steps"] = [{"id": "s1", "concepts": ["linear fit"]}, {"id": "s2", "concepts": ["correlation"]}]
    p.write_text(yaml.safe_dump(plan))
    w.write_solution("trees", "s1", ["h1", "h2"], "slope -0.3", "least squares",
                     [{"problem": "other city"}, {"problem": "other year"}])
    return w


def test_layout(ws):
    r = ws.root
    for p in ["inbox", "projects/trees/solutions", "projects/trees/work", ".private/learner.yaml",
              ".private/proposals.yaml", ".private/handoff", ".gitignore"]:
        assert (r / p).exists(), p
    assert ".private/" in (r / ".gitignore").read_text()


def test_init_project_refuses_duplicate(ws):
    with pytest.raises(HarnessError):
        ws.init_project("trees")


def test_write_solution_needs_two_follow_ons(ws):
    with pytest.raises(HarnessError):
        ws.write_solution("trees", "s1", [], "a", "m", [{"problem": "only one"}])


def test_attempt_blank_refused_question_counts(ws):
    with pytest.raises(HarnessError):
        ws.record_attempt("trees", "s1", "  \n")
    assert ws.record_attempt("trees", "s1", "What does slope mean here?")["saved"]


def test_hints_step_down_then_run_out(ws):
    assert ws.reveal_solution("trees", "s1", "hint")["content"] == "h1"
    assert ws.reveal_solution("trees", "s1", "hint")["content"] == "h2"
    assert "No more hints" in ws.reveal_solution("trees", "s1", "hint")["content"]


def test_reveal_answer_masks_method(ws):
    r = ws.reveal_solution("trees", "s1", "answer")
    assert r["content"] == "slope -0.3" and "work backward" in r["next"]
    st = ws.get_progress("trees")["steps"]["s1"]
    assert st["status"] == "seen" and "answer" in st["seen"]


def test_reveal_method_poses_sibling_and_cycles(ws):
    a = ws.reveal_solution("trees", "s1", "method")["follow_on"]["id"]
    b = ws.reveal_solution("trees", "s1", "method")["follow_on"]["id"]
    assert a != b
    assert "follow_on" not in ws.reveal_solution("trees", "s1", "method")  # all used; can move on


def test_drafted_needs_work_but_seeing_a_solution_is_no_toll(ws):
    with pytest.raises(HarnessError):
        ws.set_status("trees", "s1", "drafted", "tutor")
    ws.record_attempt("trees", "s1", "my fit")
    assert ws.reveal_solution("trees", "s1", "method")["follow_on"]["id"]
    assert ws.set_status("trees", "s1", "drafted", "tutor")["status"] == "drafted"   # follow-on offered, not owed


def test_seen_never_blocks(ws):
    assert ws.set_status("trees", "s2", "seen", "tutor")["status"] == "seen"


def test_defended_gate(ws):
    ws.record_attempt("trees", "s1", "my fit")
    full = {"explained": True, "questions_worked": 3, "path_not_taken": True, "limit_named": True}
    with pytest.raises(HarnessError):
        ws.set_status("trees", "s1", "defended", "tutor", full)
    with pytest.raises(HarnessError):
        ws.set_status("trees", "s1", "defended", "validator", {**full, "questions_worked": 2})
    assert ws.set_status("trees", "s1", "defended", "validator", full)["status"] == "defended"


def test_defended_needs_unseen_work_after_reveal(ws):
    ws.record_attempt("trees", "s1", "my fit")
    ws.reveal_solution("trees", "s1", "answer")
    full = {"explained": True, "questions_worked": 4, "path_not_taken": True, "limit_named": True}
    with pytest.raises(HarnessError):
        ws.set_status("trees", "s1", "defended", "validator", full)
    ws.record_attempt("trees", "s1", "found the method myself", follow_on="s1-backward")
    assert ws.set_status("trees", "s1", "defended", "validator", full)["status"] == "defended"


def test_defense_draft_then_reviewed(ws):
    d = ws.record_defense("trees", "s1", "I fit a line because...", parked=["Why not a curve?"])
    assert d["saved"].endswith("defense-draft.md")
    r = ws.record_defense("trees", "s1", "I fit a line because...", reviewed=True)
    hdir = ws.private / "handoff/trees/s1"
    assert not (hdir / "defense-draft.md").exists() and (ws.root / r["saved"]).exists()


def test_notes_by_role_and_marked_read(ws):
    ws.post_note("trees", "s1", "mentor", "validator", "Wrong slope sign, but thoughtful framing.")
    ws.post_note("trees", "s1", "tutor", "validator", "Revisit units.")
    assert [n["text"] for n in ws.get_progress("trees", "mentor")["notes"]] == \
        ["Wrong slope sign, but thoughtful framing."]
    assert ws.get_progress("trees", "mentor")["notes"] == []
    with pytest.raises(HarnessError):
        ws.post_note("trees", "s1", "principal", "validator", "x")


def test_profile_proposals(ws):
    pid = ws.propose_profile_change("propose", {"formats_that_fit": ["diagrams"]}, reason="diary")["proposed"]
    learner = ws.private / "learner.yaml"
    assert "formats_that_fit" not in learner.read_text()
    ws.propose_profile_change("accept", proposal_id=pid)
    assert "diagrams" in learner.read_text()
    with pytest.raises(HarnessError):
        ws.propose_profile_change("accept", proposal_id=pid)


def test_learnings_validate_source_and_tags(ws):
    src = ws.add_diary_entry("The slope finally made sense as degrees per percent canopy.", project="trees")["saved"]
    with pytest.raises(HarnessError):
        ws.extract_learnings("trees", {"what_happened": "x", "source": "nope.md"})
    with pytest.raises(HarnessError):
        ws.extract_learnings("trees", {"what_happened": "x", "source": src, "tags": {"concept": ["calculus"]}})
    ok = ws.extract_learnings("trees", {"id": "slope-meaning", "step": "s1", "concept": "linear fit",
                                        "what_happened": "slope read as a rate", "source": src,
                                        "tags": {"concept": ["linear fit"]}})
    assert ok["saved"]
    with pytest.raises(HarnessError):
        ws.extract_learnings("trees", {"id": "slope-meaning", "what_happened": "again", "source": src})


def test_search_and_rebuild(ws):
    ws.add_diary_entry("Gradient descent felt like walking downhill in fog.", title="fog")
    ws.log_session("Talked through residuals", project="trees")
    hits = ws.search_memory("downhill fog", scope="reflection")["results"]
    assert hits and hits[0]["kind"] == "diary" and "[" in hits[0]["snippet"]
    (ws.private / "index/memory.sqlite").unlink()
    assert ws.search_memory("downhill", scope="reflection")["results"] == []
    assert ws.rebuild_index()["indexed"] >= 2
    assert ws.search_memory("downhill", scope="reflection")["results"]


def test_check_links_rejects_non_http(ws):
    r = ws.check_links(["ftp://x", "not a link"])
    assert r["dead"] == ["ftp://x", "not a link"]
