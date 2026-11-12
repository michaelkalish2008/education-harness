import datetime as dt
import json

import pytest
import yaml

from eh_mcp.core import HarnessError, Workspace

LATER = dt.date.today() + dt.timedelta(days=120)
MUCH_LATER = dt.date.today() + dt.timedelta(days=500)
CCBY = "https://creativecommons.org/licenses/by/4.0/"


@pytest.fixture
def ws(tmp_path):
    w = Workspace(tmp_path / "learning")
    w.ensure_workspace()
    docs = tmp_path / "docs"
    docs.mkdir()
    ids = {}
    for name, concept, text in [
        ("slopes.md", "slope-as-rate", "Slope as a rate of change between two measured quantities in a line."),
        ("gradients.md", "gradient", "The gradient points uphill; stepping against it lowers the loss."),
        ("rinds.md", None, "How the rind forms on aging cheese and why humidity in the cave matters."),
    ]:
        (docs / name).write_text(text + "\n")
        rid = w.library.add(str(docs / name), "notes", concepts=[concept] if concept else [])["needs_summary"][0]["id"]
        w.library.write_summary(rid, name, text)
        ids[name] = f"lib:{rid}"
    w.add_diary_entry("I finally get what a slope means.", title="slope")
    return w, ids


def tier(w, doc_id):
    return w.index.doc(doc_id)["meta"]["tier"]


def test_scopes_are_a_hard_filter(ws):
    w, ids = ws
    assert all(r["kind"] == "library" for r in w.search_memory("slope")["results"])
    assert [r["kind"] for r in w.search_memory("slope", scope="reflection")["results"]] == ["diary"]
    assert {r["kind"] for r in w.search_memory("slope", scope="all")["results"]} == {"library", "diary"}
    with pytest.raises(HarnessError):
        w.search_memory("slope", scope="everything")


def test_new_items_stay_active_then_cool(ws):
    w, ids = ws
    assert w.knowledge.sweep()["cooled"] == []
    r = w.knowledge.sweep(today=LATER)
    assert set(r["cooled"]) == set(ids.values())
    assert tier(w, ids["slopes.md"]) == "cold"
    assert w.search_memory("slope")["results"]          # cold is still keyword-searchable


def test_use_keeps_items_active_and_rewarms(ws):
    w, ids = ws
    w.knowledge.sweep(today=LATER)
    r = w.knowledge.record_use([ids["rinds.md"]], "opened")
    assert r["rewarmed"] == [ids["rinds.md"]] and tier(w, ids["rinds.md"]) == "active"


def test_plan_demand_rewarms_prerequisites_just_in_time(ws):
    w, ids = ws
    w.knowledge.sweep(today=LATER)
    assert tier(w, ids["slopes.md"]) == "cold"
    w.init_project("descent", question="How fast does a wheel lose water?")
    p = w.root / "projects/descent/program.yaml"
    plan = yaml.safe_load(p.read_text())
    plan["steps"] = [{"id": "s1", "concepts": ["gradient"]}]
    p.write_text(yaml.safe_dump(plan))
    r = w.knowledge.sweep(today=LATER)
    assert "slope-as-rate" in r["demanded_concepts"]       # gradient requires the ideas of fitting a line
    assert set(r["rewarmed"]) == {ids["slopes.md"], ids["gradients.md"]}
    assert tier(w, ids["rinds.md"]) == "cold"


def test_forgetting_is_only_proposed_then_confirmed(ws):
    w, ids = ws
    r = w.knowledge.sweep(today=MUCH_LATER)
    assert {f["id"] for f in r["forget_proposals"]} == set(ids.values())
    assert w.library._load(ids["rinds.md"].removeprefix("lib:"))   # nothing removed yet
    with pytest.raises(HarnessError):
        w.knowledge.forget(ids["rinds.md"], learner_confirmed=False)
    w.knowledge.forget(ids["rinds.md"], learner_confirmed=True)
    assert w.index.doc(ids["rinds.md"]) is None
    markers = yaml.safe_load((w.private / "library/forgotten.yaml").read_text())
    assert markers[0]["title"] == "rinds.md"


def test_clusters_by_concept(ws):
    w, ids = ws
    c = w.knowledge.clusters("notes")["clusters"]
    labels = {x["label"] for x in c}
    assert {"slope-as-rate", "gradient"} <= labels and any(l.startswith("similar") for l in labels)


def test_set_tier_moves_a_cluster(ws):
    w, ids = ws
    w.knowledge.set_tier([ids["rinds.md"]], "cold")
    assert tier(w, ids["rinds.md"]) == "cold"
    w.rebuild_index()
    assert tier(w, ids["rinds.md"]) == "cold"                # tiers survive a rebuild


def write_standards(folder, rows):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "StandardsFrameworkItem.jsonl").write_text("\n".join(json.dumps(r) for r in rows))


def std(code, text, lic=CCBY, jur="Multi-State", subject="Mathematics"):
    return {"identifier": code.lower(), "statementCode": code, "description": text, "academicSubject": subject,
            "jurisdiction": jur, "license": lic, "gradeLevel": ["9", "10", "11", "12"],
            "attributionStatement": "Knowledge Graph is provided by Learning Commons under the CC BY-4.0 license."}


def test_standards_are_pinned_attributed_and_license_checked(ws, tmp_path):
    w, ids = ws
    write_standards(tmp_path / "kg", [
        std("HSS-ID.C.7", "Interpret the slope and the intercept of a linear model in the context of the data."),
        std("HSF-LE.A.2", "Construct linear and exponential functions given a graph or a description."),
        std("HSX-NO.1", "A record without an open license.", lic="All rights reserved"),
        std("TX.1", "A state standard outside the chosen jurisdiction.", jur="Texas"),
        std("ELA.1", "A reading standard.", subject="English Language Arts"),
    ])
    r = w.knowledge.load_standards(str(tmp_path / "kg"))
    assert r["pinned"] == 2 and r["skipped_without_open_license"] == 1
    assert list(r["attributions"].values()) == [2]
    hit = w.search_memory("slope intercept", scope="reference")["results"][0]
    assert hit["kind"] == "standard" and tier(w, hit["id"]) == "pinned"
    w.knowledge.sweep(today=MUCH_LATER)
    assert tier(w, hit["id"]) == "pinned"                    # never cooled
    assert w.search_memory("slope intercept")["results"] == [] or all(
        x["kind"] != "standard" for x in w.search_memory("slope intercept")["results"])  # not mixed into domain


def test_standards_reload_on_rebuild(ws, tmp_path):
    w, ids = ws
    write_standards(tmp_path / "kg", [std("HSS-ID.C.7", "Interpret the slope and the intercept of a linear model.")])
    w.knowledge.load_standards(str(tmp_path / "kg"))
    (w.private / "index/memory.sqlite").unlink()
    w.rebuild_index()
    assert w.search_memory("intercept", scope="reference")["results"]


def test_standards_in_the_published_shape(ws, tmp_path):
    """NDJSON items keyed by caseIdentifierUUID, code-less headings, and a separate
    Relationships file with hasChild and buildsTowards rows."""
    w, ids = ws
    attr = "Knowledge Graph is provided by CZI-E under the CC BY-4.0 license."

    def item(uid, code, text, kind="Standard"):
        return {"identifier": "x" + uid, "caseIdentifierUUID": uid, "statementCode": code, "description": text,
                "normalizedStatementType": kind, "jurisdiction": "Multi-State", "academicSubject": "Mathematics",
                "gradeLevel": ["9"], "license": CCBY, "attributionStatement": attr}

    def rel(kind, s, t):
        return {"relationshipType": kind, "sourceEntity": "StandardsFrameworkItem", "sourceEntityKey":
                "caseIdentifierUUID", "sourceEntityValue": s, "targetEntity": "StandardsFrameworkItem",
                "targetEntityKey": "caseIdentifierUUID", "targetEntityValue": t, "license": CCBY}
    kg = tmp_path / "kg"
    kg.mkdir()
    rows = [item("u-fn", None, "Functions", "Standard Grouping"),
            item("u-le", None, "Linear, Quadratic, & Exponential Models", "Standard Grouping"),
            item("u-lea", "HSF-LE.A", "Construct and compare linear, quadratic, and exponential models.",
                 "Standard Grouping"),
            item("u-1b", "HSF-LE.A.1.b", "Recognize situations in which one quantity changes at a constant rate."),
            item("u-4", "HSF-LE.A.4", "For exponential models, express as a logarithm the solution.")]
    (kg / "StandardsFrameworkItem.json").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    (kg / "Relationships.json").write_text("\n".join(json.dumps(r) for r in [
        rel("hasChild", "u-fn", "u-le"), rel("hasChild", "u-le", "u-lea"), rel("hasChild", "u-lea", "u-1b"),
        rel("hasChild", "u-lea", "u-4"), rel("buildsTowards", "u-1b", "u-4"),
        rel("buildsTowards", "u-1b", "u-elsewhere")]) + "\n")
    r = w.knowledge.load_standards(str(kg))
    assert r["pinned"] == 3                                   # headings are not pinned
    assert r["progression_edges"] == 1 and r["structure_edges"] == 2
    assert "HSF-LE.A.1b" not in r["program_codes_missing"]    # 1b finds 1.b
    hit = w.search_memory("logarithm exponential", scope="reference")["results"][0]
    assert hit["id"] == "std:u-4"
    doc = w.index.doc("std:u-4")
    assert doc["meta"]["domain"] == ["Functions", "Linear, Quadratic, & Exponential Models"]
    assert doc["meta"]["attribution"] == attr
    w.ensure_workspace()                                      # reloading the program keeps citations
    import sqlite3
    with sqlite3.connect(w.index.path) as c:
        assert c.execute("SELECT count(*) FROM edges WHERE rel='cites' AND dst='std:u-1b'").fetchone()[0] > 0
