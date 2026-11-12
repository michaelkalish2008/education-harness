import re
from pathlib import Path

import yaml

TRACK = yaml.safe_load((Path(__file__).with_name("track.yaml")).read_text())
CODE = re.compile(r"^(HS[NAFGS]-[A-Z]{2,3}\.[A-C]\.\d+[a-e]?|\d\.[A-Z]{1,3}\.[A-C]\.\d+[a-e]?)$")


def test_six_ideas_in_order():
    assert [i["order"] for i in TRACK["ideas"]] == [1, 2, 3, 4, 5, 6]


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


def test_standards_look_like_common_core_codes():
    for idea in TRACK["ideas"]:
        for s in idea["standards"]:
            assert CODE.match(s), s


def test_math_the_user_asked_for_is_on_the_path():
    names = " ".join(c["name"] for i in TRACK["ideas"] for c in i["concepts"])
    for needed in ["exponential", "logarithm", "matri", "partial derivative", "sine and cosine"]:
        assert needed in names, needed
