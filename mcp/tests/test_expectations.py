import pytest

from eh_mcp.core import HarnessError, Workspace
from eh_mcp.neutrality import check

STEPS = [{"id": "s1", "does": "estimate a click rate and its margin of error", "concepts": ["sample proportion"],
          "strong_version_shows": ["interval in words"]}]
SRC = {"kind": "document", "title": "STAT 20 syllabus, Fall 2026", "accessed_on": "2026-11-14"}


@pytest.fixture
def ws(tmp_path):
    w = Workspace(tmp_path / "learning")
    w.ensure_workspace()
    return w


def test_external_set_needs_issuer_and_source_and_confirmation(ws):
    with pytest.raises(HarnessError):
        ws.expectations.manage("create", set="stat20", origin="external", issuer="City College")
    ws.expectations.manage("create", set="stat20", origin="external", title="Intro statistics",
                           issuer="City College", context={"class": "STAT 20", "level": "college"}, source=SRC)
    items = [{"statement": "Construct and interpret a confidence interval for a population proportion.",
              "area": "Inference", "level": "requirement", "where_in_source": "Learning outcome 4"}]
    with pytest.raises(HarnessError):
        ws.expectations.manage("add", set="stat20", items=items)
    out = ws.expectations.manage("add", set="stat20", items=items, confirmed=True)
    assert out["added"] == ["EXT-STAT20.1"] and out["indexed"] == 1


def test_expectations_are_searchable_by_origin_and_reach_planning(ws):
    ws.expectations.manage("create", set="stat20", origin="external", issuer="City College", source=SRC)
    ws.expectations.manage("add", set="stat20", confirmed=True, items=[
        {"statement": "Construct and interpret a confidence interval for a population proportion; margin of error."}])
    ws.expectations.manage("create", set="my-bar", origin="personal", title="How I hold myself")
    ws.expectations.manage("add", set="my-bar", confirmed=True, items=[
        {"statement": "I can explain every number I report to a coworker without notes.", "level": "aspiration"}])
    ext = ws.expectations.search("confidence interval proportion", origin="external")["results"]
    assert ext[0]["code"] == "EXT-STAT20.1" and ext[0]["origin"] == "external"
    mine = ws.expectations.search("explain number coworker", origin="personal")["results"]
    assert mine[0]["code"] == "ME-MY-BAR.1"
    out = ws.orient.write_plan("clicks", "Will a user click?", STEPS)
    cands = {c["code"] for c in out["standards"]["candidates_to_review"]}
    assert "EXT-STAT20.1" in cands
    ws.alignment.manage("review", "clicks", code="EXT-STAT20.1", decision="accept")
    rec = next(r for r in ws.alignment.read("clicks")["standards"] if r["code"] == "EXT-STAT20.1")
    assert rec["origin"] == "external" and rec["set"] == "stat20"


def test_expectations_survive_a_rebuild_and_retired_items_drop_from_search(ws):
    ws.expectations.manage("create", set="my-bar", origin="personal")
    ws.expectations.manage("add", set="my-bar", confirmed=True, items=[{"statement": "I finish what I start."}])
    ws.rebuild_index()
    assert ws.expectations.search("finish start")["results"][0]["code"] == "ME-MY-BAR.1"
    ws.expectations.manage("retire", set="my-bar", code="ME-MY-BAR.1")
    assert ws.expectations.search("finish start")["results"] == []


@pytest.mark.parametrize("text", [
    "Students will believe that the nation's founders were never wrong.",
    "Accept that the official account is the only true one.",
    "Learners will support the party's program.",
    "Condemn the opposing movement.",
])
def test_belief_and_allegiance_are_refused(text):
    assert check(text)


@pytest.mark.parametrize("text", [
    "Explain why some economists believe minimum wages reduce employment, with sources.",
    "Support claims with evidence from at least two reliable sources.",
    "Evaluate the evidence for and against a policy.",
    "Construct and interpret a confidence interval.",
])
def test_capabilities_pass(text):
    assert check(text) is None


def test_plans_and_external_sets_are_gated(ws):
    with pytest.raises(HarnessError, match="principle 19"):
        ws.orient.write_plan("x", "Why is our party right?", [
            {"id": "s1", "does": "accept that the party is always right", "concepts": ["loyalty"],
             "strong_version_shows": ["agreement"]}])
    ws.expectations.manage("create", set="camp", origin="external", issuer="Some camp", source=SRC)
    with pytest.raises(HarnessError, match="principle 19"):
        ws.expectations.manage("add", set="camp", confirmed=True,
                               items=[{"statement": "Pupils will be loyal to the movement."}])
