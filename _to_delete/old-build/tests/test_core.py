from pathlib import Path

import pytest
import yaml

from education_harness.core import Harness, HarnessError


def make_project(tmp_path: Path) -> Harness:
    harness = Harness(tmp_path)
    harness.init_project("shade-study", "Do trees reduce summer heat?")
    project = harness.root / "projects" / "shade-study"
    program = yaml.safe_load((project / "program.yaml").read_text())
    program["steps"] = [{"id": "fit-line", "does": "Fit a line", "concepts": ["linear fit"], "format": "work-backward", "answer": "slope = -2"}]
    (project / "program.yaml").write_text(yaml.safe_dump(program, sort_keys=False))
    progress = yaml.safe_load((project / "progress.yaml").read_text())
    progress["steps"]["fit-line"] = {"status": "not-started", "revealed": []}
    (project / "progress.yaml").write_text(yaml.safe_dump(progress, sort_keys=False))
    harness.write_solution("shade-study", "fit-line", ["Plot both variables."], "Fit least squares.", [{"problem": "Use a second city", "solution": "Repeat the fit"}, {"problem": "Swap axes", "solution": "Interpret the new slope"}], "lesson-planner")
    return harness


def test_init_project_creates_private_workspace(tmp_path: Path) -> None:
    harness = Harness(tmp_path)
    result = harness.init_project("my-project", "What should I build?")
    assert result["created"] is True
    assert (harness.root / ".gitignore").read_text() == ".private/\n"
    assert (harness.root / ".private" / "learner.yaml").is_file()
    assert harness.get_plan("my-project")["schema"] == 1


def test_reveal_is_logged_and_paired(tmp_path: Path) -> None:
    harness = make_project(tmp_path)
    reveal = harness.reveal_solution("shade-study", "fit-line", "method")
    assert reveal["content"] == "Fit least squares."
    assert reveal["follow_on"] == {"problem": "Use a second city"}
    assert "method" in harness.get_progress("shade-study", "tutor")["progress"]["steps"]["fit-line"]["revealed"]


def test_only_lesson_planner_writes_solutions(tmp_path: Path) -> None:
    harness = make_project(tmp_path)
    with pytest.raises(HarnessError, match="lesson-planner"):
        harness.write_solution("shade-study", "fit-line", [], "Secret", [{"problem": "a"}, {"problem": "b"}], "tutor")


def test_defended_gate_requires_validator_and_all_evidence(tmp_path: Path) -> None:
    harness = make_project(tmp_path)
    evidence = {"explained_work": True, "three_questions": True, "path_not_taken": True, "named_limit": True, "unseen_problem": True}
    with pytest.raises(HarnessError, match="validator"):
        harness.set_status("shade-study", "fit-line", "defended", "tutor", evidence)
    assert harness.set_status("shade-study", "fit-line", "defended", "validator", evidence)["status"] == "defended"


def test_notes_are_scoped_to_role(tmp_path: Path) -> None:
    harness = make_project(tmp_path)
    harness.post_note("shade-study", "fit-line", "validator", "tutor", "Please check the slope.")
    assert len(harness.get_progress("shade-study", "validator", "fit-line")["notes"]) == 1
    assert harness.get_progress("shade-study", "mentor", "fit-line")["notes"] == []


def test_keyword_memory_and_learning_validation(tmp_path: Path) -> None:
    harness = make_project(tmp_path)
    diary = harness.add_diary_entry("The slope clicked when I described shade per degree.", {"project": "shade-study", "concept": "linear fit"})
    hits = harness.search_memory("slope", {"project": "shade-study"})
    assert hits and "[slope]" in hits[0]["snippet"]
    learning = {"source": diary["saved"], "what_happened": "Explaining the slope in context worked.", "tags": {"concept": ["linear fit"], "project": "shade-study"}}
    assert harness.extract_learnings("shade-study", learning)["saved"].endswith(".yaml")

