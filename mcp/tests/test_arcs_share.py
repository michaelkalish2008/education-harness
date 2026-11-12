import pytest
import yaml

from eh_mcp.core import HarnessError, Workspace

STEP = lambda i, does, extra=None: {"id": f"s{i}", "does": does, "concepts": ["chain-rule"],
                                    "strong_version_shows": ["x"], **(extra or {})}


@pytest.fixture
def ws(tmp_path):
    w = Workspace(tmp_path / "learning")
    w.ensure_workspace()
    p = w.propose_profile_change("propose", {"interests": ["coffee"]})["proposed"]
    w.propose_profile_change("accept", proposal_id=p)
    return w


def two_arcs(w):
    w.orient.set_arc("Understand fine-tuning, RL and SFT", [{"title": "SFT on ten examples", "project": "sft"}],
                     name="fine-tuning")
    w.orient.set_arc("Know why causal claims hold", [{"title": "Confounding in my coffee", "project": "confound"}],
                     name="causal-inference")
    w.orient.write_plan("sft", "What does SFT change?", [STEP(1, "label ten prompts")])
    w.orient.write_plan("confound", "Does brew time cause bitterness?", [STEP(1, "draw the causal graph")])


def test_several_arcs_each_chat_focuses_on_one(ws):
    two_arcs(ws)
    s = ws.orient.where_am_i()
    assert s["suggested"]["move"] == "choose" and s["suggested"]["say"].startswith("Let's go on ")
    assert {a["name"] for a in s["arcs"]} == {"fine-tuning", "causal-inference"}
    c = ws.orient.where_am_i(focus="causal")                 # words from the name are enough
    assert c["focus"] == "causal-inference" and c["current"]["project"] == "confound"
    assert c["suggested"]["why"].endswith("draw the causal graph")
    ws.record_attempt("sft", "s1", "label them by hand")      # work elsewhere doesn't move this chat
    assert ws.orient.where_am_i(focus="causal-inference")["current"]["project"] == "confound"
    m = (ws.root / "MAP.md").read_text()
    assert "## fine-tuning:" in m and "## causal-inference:" in m and "Let's go on <arc>" in m
    with pytest.raises(HarnessError):
        ws.orient.set_arc("a third", [{"title": "x"}])        # several arcs: a name is needed
    with pytest.raises(HarnessError):
        ws.orient.get_arc("nothing-like-it")


def test_one_arc_workspaces_migrate(ws):
    (ws.private / "arc.yaml").write_text(yaml.safe_dump({"schema": 1, "goal": "Read transformer papers",
                                                         "path": [{"title": "fit"}]}))
    a = ws.orient.get_arc()["arc"]
    assert a["name"] == "read-transformer-papers" and not (ws.private / "arc.yaml").exists()


def test_share_out_closes_the_last_step_and_feeds_the_report(ws):
    ws.orient.set_arc("Fine-tuning", [{"title": "SFT", "project": "sft"}], name="fine-tuning")
    ws.orient.write_plan("sft", "What does SFT change?", [
        STEP(1, "label ten prompts"),
        STEP(2, "show my team what changed", {"format": "share-out", "requires": ["s1"]})])
    ws.share.set_audience("sft", "my team at work", kind="group", format="explainer")
    with pytest.raises(HarnessError):
        ws.share.set_audience("sft", "x", format="tiktok")
    ws.share.save_share_draft("sft", "SFT nudges the model toward my ten labeled answers ...")
    ws.share.save_share_draft("sft", "SFT nudges the model toward ten answers I labeled by hand ...")
    g = ws.share.get_share("sft")
    assert len(g["drafts"]) == 2 and "by hand" in g["latest_draft"]
    r = ws.share.mark_shared("sft", "presented", where="team meeting", who="my team")
    assert r["step"] == {"s2": "drafted"}
    ws.share.heard_back("sft", "A coworker asked how many examples you need before it helps.", "a coworker")
    e = ws.reports.report_evidence(project="sft")
    assert e["sociability"]["count"] == 2
    assert e["share_out"]["audience"]["audience"] == "my team at work"
    assert "how many examples" in e["share_out"]["heard_back"][0]["text"]


def test_retrospective_is_due_when_a_project_is_done(ws):
    ws.orient.set_arc("Fine-tuning", [{"title": "SFT", "project": "sft"}, {"title": "RLHF"}], name="fine-tuning")
    ws.orient.write_plan("sft", "q", [STEP(1, "label ten prompts")])
    ws.record_attempt("sft", "s1", "done")
    ws.set_status("sft", "s1", "drafted", "tutor")
    s = ws.orient.where_am_i(focus="fine-tuning")
    assert s["suggested"]["move"] == "retro" and s["waiting"]["retrospective_due"] == ["sft"]
    with pytest.raises(HarnessError):
        ws.share.save_retrospective({"went_well": "  "}, project="sft")
    ws.share.save_retrospective({"went_well": "labeling by hand made it concrete",
                                 "differently": "start with fewer examples", "next": "try RLHF"}, project="sft")
    assert ws.orient.where_am_i(focus="fine-tuning")["suggested"]["move"] == "plan"
    assert ws.reports.report_evidence(project="sft")["retrospectives"][0]["answers"]["next"] == "try RLHF"
    assert ws.search_memory("labeling by hand concrete", scope="reflection")["results"][0]["kind"] == "retro"


def test_spaces_keep_each_claude_project_to_its_own_arcs(ws):
    ws.orient.set_arc("Backprop math", [{"title": "chain rule", "idea": "data-scientist:backprop"}],
                      name="backprop-math", space="Intro to Transformers and NN")
    ws.orient.set_arc("Heidegger and attention", [{"title": "care and attention", "project": "care"}],
                      name="phenomenology-llms", space="Computational Phenomenology", lens="philosophy")
    ws.orient.write_plan("care", "Can attention be read as care?", [STEP(1, "read one passage on care")])
    s = ws.orient.where_am_i(space="Computational Phenomenology")
    assert [a["name"] for a in s["arcs"]] == ["phenomenology-llms"]          # one arc here: no 'choose'
    assert s["current"]["project"] == "care" and s["arc"]["lens"] == "philosophy"
    assert "cite the passage" in " ".join(s["arc"]["lens_detail"]["checks"])
    t = ws.orient.where_am_i(space="Intro to Transformers and NN")
    assert [a["name"] for a in t["arcs"]] == ["backprop-math"] and t["arc"]["lens"] == "math"
    m = (ws.root / "MAP.md").read_text()
    assert "# Computational Phenomenology" in m and "# Intro to Transformers and NN" in m
    # recall stays shared across spaces
    ws.board.remember("chain rule", "outer times inner")
    assert ws.board.recall("chain rule")["your_notes"]
    e = ws.reports.report_evidence(project="care")
    assert e["lens"]["name"] == "philosophy" and e["strengths_evidence"]["practices_touched"] == []


def test_older_arcs_without_a_space_can_be_placed(ws):
    ws.orient.set_arc("Fine-tuning", [{"title": "SFT"}], name="fine-tuning")
    s = ws.orient.where_am_i(space="Intro to Transformers and NN")
    assert s["unplaced_arcs"] == ["fine-tuning"] and s["arcs"][0]["name"] == "fine-tuning"   # still visible
    ws.orient.set_arc_space("fine-tuning", space="Intro to Transformers and NN", lens="math")
    assert ws.orient.where_am_i(space="Intro to Transformers and NN")["unplaced_arcs"] == []
    assert ws.orient.where_am_i(space="Computational Phenomenology")["arcs"] == []
    with pytest.raises(HarnessError):
        ws.orient.set_arc_space("fine-tuning", lens="astrology")
