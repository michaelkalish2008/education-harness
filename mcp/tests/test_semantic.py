import hashlib
import re
import time

import numpy as np
import pytest

from eh_mcp.core import Workspace
from eh_mcp.turboquant import TurboQuant

# A stand-in embedder: words in the same group share a direction, so search can
# find meaning without shared words. The real model is tested on the learner's machine.
GROUPS = [{"car", "vehicle", "automobile"}, {"value", "price", "worth"}, {"loses", "loss", "depreciation", "drops"},
          {"tree", "trees", "canopy", "shade"}, {"heat", "temperature", "hot"}]


class FakeEmbedder:
    name, dim, fingerprint = "fake", 384, "f1"

    def embed(self, texts):
        out = []
        for t in texts:
            v = np.zeros(self.dim)
            for w in re.findall(r"\w+", t.lower()):
                g = next((i for i, grp in enumerate(GROUPS) if w in grp), None)
                key = f"g{g}" if g is not None else w
                rng = np.random.default_rng(int(hashlib.md5(key.encode()).hexdigest()[:8], 16))
                v += rng.standard_normal(self.dim)
            out.append(list(v))
        return out


def wait_on(ws, timeout=10):
    t0 = time.time()
    while ws.semantic.state not in ("on", "failed") and time.time() - t0 < timeout:
        time.sleep(0.02)
    return ws.semantic.state


@pytest.fixture
def ws(tmp_path):
    w = Workspace(tmp_path / "learning")
    w.ensure_workspace()
    w.add_diary_entry("How fast does an automobile drop in worth each year?", title="car")
    w.add_diary_entry("Neighborhood canopy and summer temperature looked related.", title="trees")
    w.add_diary_entry("Softmax turns scores into probabilities.", title="softmax")
    return w


def test_turboquant_preserves_similarity():
    rng = np.random.default_rng(1)
    tq = TurboQuant(384, bits=4)
    x = rng.standard_normal((300, 384))
    q = rng.standard_normal(384)
    exact = (x / np.linalg.norm(x, axis=1, keepdims=True)) @ (q / np.linalg.norm(q))
    approx = tq.scores(q, [tq.encode(v)[0] for v in x])
    assert np.corrcoef(exact, approx)[0, 1] > 0.98
    top_exact, top_approx = set(np.argsort(-exact)[:10]), set(np.argsort(-approx)[:10])
    assert len(top_exact & top_approx) >= 8


def test_turboquant_is_compact_and_deterministic():
    tq = TurboQuant(384, bits=4)
    assert tq.code_bytes == 192  # vs 1536 bytes as float32
    v = np.random.default_rng(2).standard_normal(384)
    assert tq.encode(v) == TurboQuant(384, bits=4).encode(v)


def test_keyword_only_until_turned_on(ws):
    assert ws.search_memory("vehicle value", scope="reflection")["mode"] == "keyword"
    assert ws.search_memory("vehicle value", scope="reflection")["results"] == []


def test_semantic_finds_meaning_without_shared_words(ws):
    ws.enable_semantic_search("on", embedder_factory=FakeEmbedder)
    assert wait_on(ws) == "on"
    r = ws.search_memory("vehicle value loss", scope="reflection")
    assert r["mode"] == "semantic"
    assert "car" in r["results"][0]["file"]


def test_writes_stay_in_sync(ws):
    ws.enable_semantic_search("on", embedder_factory=FakeEmbedder)
    wait_on(ws)
    ws.add_diary_entry("Shade from trees made the block less hot.", title="shade")
    assert ws.index.sync() == {"reembedded": 0, "removed": 0}  # embedded on write
    assert "shade" in ws.search_memory("canopy heat", scope="reflection")["results"][0]["file"] or \
        "trees" in ws.search_memory("canopy heat", scope="reflection")["results"][0]["file"]


def test_hand_edit_is_caught_by_sync(ws):
    ws.enable_semantic_search("on", embedder_factory=FakeEmbedder)
    wait_on(ws)
    with ws.index._conn() as c:  # simulate text that changed outside the tools
        c.execute("UPDATE docs SET body = 'tree shade', hash = 'changed' WHERE file LIKE '%softmax%'")
    assert ws.index.sync()["reembedded"] == 1


def test_failure_falls_back_to_keyword(ws):
    def broken():
        raise RuntimeError("no network")
    ws.enable_semantic_search("on", embedder_factory=broken)
    assert wait_on(ws) == "failed"
    s = ws.enable_semantic_search("status")
    assert s["mode"] == "keyword" and "Keyword search still works" in s["detail"]
    assert ws.search_memory("softmax", scope="reflection")["results"]


def test_off_returns_to_keyword(ws):
    ws.enable_semantic_search("on", embedder_factory=FakeEmbedder)
    wait_on(ws)
    ws.enable_semantic_search("off")
    assert ws.search_memory("softmax", scope="reflection")["mode"] == "keyword"


def test_model_change_rebuilds_vectors(ws):
    ws.enable_semantic_search("on", embedder_factory=FakeEmbedder)
    wait_on(ws)

    class Other(FakeEmbedder):
        fingerprint = "f2"
    r = ws.index.enable_semantic(Other())
    assert r["reembedded"] == 3


def test_library_summaries_are_embedded(tmp_path):
    ws = Workspace(tmp_path / "learning")
    ws.ensure_workspace()
    doc = tmp_path / "car.md"
    doc.write_text("A long article about cars.")
    rid = ws.library.add(str(doc), "money")["needs_summary"][0]["id"]
    ws.library.write_summary(rid, "Used cars", "How fast an automobile drops in worth each year after you buy it.")
    ws.enable_semantic_search("on", embedder_factory=FakeEmbedder)
    assert wait_on(ws) == "on"
    hit = ws.search_memory("vehicle value loss", kinds=["library"])["results"][0]
    assert hit["path"].endswith("car.md") and "semantic" in hit["signals"]


def test_turboquant_vectors_project_to_a_private_3d_map(ws):
    ws.enable_semantic_search("on", embedder_factory=FakeEmbedder)
    assert wait_on(ws) == "on"
    out = ws.knowledge_map.write(scope="reflection")
    data = out["data"]
    assert data["count"] == 3 and len(data["explained_variance"]) == 3
    assert data["preprocessing"] == {"row_normalization": "l2", "centered": True, "whitened": False}
    assert all(set(("x", "y", "z", "neighbors")) <= set(p) for p in data["points"])
    page = (ws.root / "KNOWLEDGE-MAP.html").read_text()
    assert "__KNOWLEDGE_MAP_DATA__" not in page and "Knowledge map" in page
    assert "<h1 class=\"title\">TurboQuant" not in page


def test_standard_map_points_use_readable_titles_and_canonical_links(ws):
    ws.enable_semantic_search("on", embedder_factory=FakeEmbedder)
    assert wait_on(ws) == "on"
    ws.index.upsert("std:u1", "standard", "HSS-MD.B Use probability to evaluate outcomes of decisions",
                    {"scope": "reference", "code": "HSS-MD.B",
                     "title": "HSS-MD.B", "statement": "Use probability to evaluate outcomes of decisions",
                     "domain": ["Statistics & Probability", "Using Probability to Make Decisions"],
                     "grade": ["9", "10", "11", "12"]}, "standards:standards")
    point = ws.index.pca_projection("reference")["points"][0]
    assert point["title"] == "Use probability to evaluate outcomes of decisions"
    assert point["code"] == "HSS-MD.B"
    assert point["url"].endswith("/CFItems/u1")
    assert point["domain"][-1] == "Using Probability to Make Decisions"
    ws.index.upsert("std:u2", "standard", "1.OA.C Add and subtract within 20",
                    {"scope": "reference", "code": "1.OA.C", "title": "1.OA.C",
                     "statement": "Add and subtract within 20", "grade": ["1"]}, "standards:standards")
    (ws.private / "learner.yaml").write_text("schema: 1\nlearning_context: job-interview\n")
    adult = ws.knowledge_map.data("all")
    assert adult["standards_min_grade"] == 9
    ids = [p["id"] for p in adult["points"]]
    assert ids.index("std:u1") < ids.index("std:u2")


def test_knowledge_map_requires_smart_search(ws):
    from eh_mcp.core import HarnessError
    with pytest.raises(HarnessError, match="Smart search must be on"):
        ws.knowledge_map.write()
