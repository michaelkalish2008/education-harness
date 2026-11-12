import re
from pathlib import Path

import yaml

TRACK = yaml.safe_load((Path(__file__).parents[1] / "src/eh_mcp/programs/data-scientist/track.yaml").read_text())
CODE = re.compile(r"^(HS[NAFGS]-[A-Z]{2,3}\.[A-C]\.\d+[a-e]?|\d\.[A-Z]{1,3}\.[A-C]\.\d+[a-e]?)$")


def test_modular_data_science_path_in_order():
    assert [i["order"] for i in TRACK["ideas"]] == list(range(1, 25))
    assert [i["id"] for i in TRACK["ideas"]] == [
        "calculus-foundations", "vectors-dot-products", "matrix-multiplication", "activations",
        "exponentials-softmax", "unit-circle-signals", "linear-regression", "logistic-regression",
        "tree-models", "tf-idf", "cosine-similarity", "pca", "sqlite", "mapreduce",
        "feed-forward-network", "backpropagation", "positional-encoding", "attention", "transformer",
        "hyperparameter-optimization", "supervised-fine-tuning", "reinforcement-learning", "ppo", "dpo"]


def test_six_modules_and_four_learning_stages():
    assert [m["id"] for m in TRACK["modules"]] == ["math-foundations", "statistical-learning",
                                                       "representations", "data-systems",
                                                       "neural-transformers", "training-post-training"]
    assert [s["id"] for s in TRACK["learning_stages"]] == ["math", "scratch", "package", "parity"]
    assert {i["module"] for i in TRACK["ideas"]} == {m["id"] for m in TRACK["modules"]}


def test_recommendation_project_gives_every_idea_a_purpose():
    anchor = TRACK["anchor_project"]
    assert "recommendation system" in anchor["title"].lower()
    assert set(anchor["milestones"]) == {i["id"] for i in TRACK["ideas"]}
    assert all(anchor["milestones"][i["id"]] for i in TRACK["ideas"])


def test_civic_depth_and_philosophy_sources_are_explicit():
    assert set(TRACK["depth_modes"]) == {"civic-overview", "foundational", "practitioner", "advanced"}
    assert TRACK["depth_modes"]["civic-overview"]["stages"] == ["math"]
    civic = TRACK["civic_lens"]
    assert "democratic" in civic["rationale"] and "complete learning destination" in civic["rule"]
    assert all(s["url"].startswith("https://readysetgo.substack.com/")
               for s in civic["consciousness_personhood"]["sources"])


def test_prerequisites_point_backward():
    seen = set()
    for idea in TRACK["ideas"]:
        assert set(idea["requires"]) <= seen, idea["id"]
        seen.add(idea["id"])


def test_concept_ids_unique_and_written_by_program_known():
    ids = [c["id"] for i in TRACK["ideas"] for c in i["concepts"]]
    assert len(ids) == len(set(ids))
    for idea in TRACK["ideas"]:
        own = {c["id"] for c in idea["concepts"]}
        assert set(idea.get("written_by_program", [])) <= own
        assert set(idea.get("concept_requires", {})) <= own
        assert {r for rs in idea.get("concept_requires", {}).values() for r in rs} <= own


def test_standards_look_like_common_core_codes():
    for idea in TRACK["ideas"]:
        for s in idea["standards"]:
            assert CODE.match(s), s


def test_every_idea_is_foundational_and_converges_on_transformers():
    for idea in TRACK["ideas"]:
        assert idea["foundation"]
        assert "transformer" in idea["converges_on_transformers"].lower()
        assert idea["standards"]
        assert set(idea["practice"]) == {"scratch", "package", "parity"}


def test_math_the_user_asked_for_is_on_the_path():
    names = " ".join(c["name"] for i in TRACK["ideas"] for c in i["concepts"])
    for needed in ["dot product", "matrix multiplication", "ReLU", "Euler's number", "softmax",
                   "feed-forward neural", "derivatives", "partial derivatives", "chain rule",
                   "gradient descent", "unit circle", "positional encodings", "linear functions",
                   "logistic function", "decision trees", "TF-IDF", "cosine similarity",
                   "principal components", "SQL queries", "MapReduce", "hyperparameters",
                   "supervised fine-tuning", "policy gradients", "Proximal Policy Optimization",
                   "Direct Preference Optimization"]:
        assert needed in names, needed


def test_calculus_foundations_precede_backpropagation():
    by_id = {idea["id"]: idea for idea in TRACK["ideas"]}
    assert by_id["calculus-foundations"]["order"] == 1
    assert "calculus-foundations" in by_id["backpropagation"]["requires"]
