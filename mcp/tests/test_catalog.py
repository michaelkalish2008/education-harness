import json

from eh_mcp.catalog import PLACEHOLDER, template_path
from eh_mcp.core import Workspace


STEPS = [{"id": "s1", "does": "observe a falling apple", "concepts": ["gravity"],
          "strong_version_shows": ["separates observation from explanation"]}]


def test_catalog_classifies_and_organizes_learning(tmp_path):
    ws = Workspace(tmp_path / "learning")
    ws.orient.write_plan("gravity", "Why does an apple fall?", STEPS)
    first = ws.catalog.data()
    lesson = next(x for x in first["items"] if x["id"] == "project:gravity")
    assert lesson["kind"] == "developing" and first["analytics"]["portfolio_shape"] == "not enough evidence yet"
    ws.catalog.manage("prioritize", "gravity", priority="now")
    ws.catalog.manage("rank", "gravity", rank=1)
    ws.catalog.manage("archive", "gravity")
    changed = next(x for x in ws.catalog.data()["items"] if x["id"] == "project:gravity")
    assert changed["priority"] == "now" and changed["rank"] == 1 and changed["archived"] is True
    ws.catalog.manage("restore", "gravity")
    assert next(x for x in ws.catalog.data()["items"] if x["id"] == "project:gravity")["archived"] is False


def test_catalog_accepts_learner_reported_external_learning(tmp_path):
    ws = Workspace(tmp_path / "learning")
    ws.catalog.manage("add_external", title="Energy Economics", provider="Coursera",
                      progress="Week 3 of 8", notes="Studying electricity markets", priority="next")
    item = next(x for x in ws.catalog.data()["items"] if x["entity"] == "external")
    assert item["provider"] == "Coursera" and item["progress"] == "Week 3 of 8"


def test_catalog_page_embeds_data_and_where_am_i_refreshes_it(tmp_path):
    ws = Workspace(tmp_path / "learning")
    ws.orient.write_plan("gravity", "Why does an apple fall?", STEPS)
    ws.orient.where_am_i()
    page = (ws.root / "CATALOG.html").read_text()
    assert PLACEHOLDER not in page and "Your learning catalog" in page
    raw = page.split('id="catalog-data" type="application/json">', 1)[1].split("</script>", 1)[0]
    assert json.loads(raw)["items"][0]["slug"] == "gravity"
    assert PLACEHOLDER in template_path().read_text()


def test_three_trajectories_can_show_a_renaissance_pattern(tmp_path):
    ws = Workspace(tmp_path / "learning")
    for name in ("gravity", "poetry", "economics"):
        ws.orient.write_plan(name, f"Learn {name}", STEPS)
        ws.orient.set_arc(f"Explore {name}", [{"title": name, "project": name}], name=name)
    analytics = ws.catalog.data()["analytics"]
    assert analytics["enough_evidence"] is True
    assert analytics["portfolio_shape"] == "renaissance pattern"
