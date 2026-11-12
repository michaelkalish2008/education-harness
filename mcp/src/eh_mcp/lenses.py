"""Lenses: how an arc's work is checked and how its strengths are named.

A math arc and a philosophy arc grow different habits of mind and need different checks.
Each arc carries one lens; the tutor applies its checks, and reports name strengths with
its strands. Strands are reference points for describing growth, never a rubric to score.
"""

from __future__ import annotations

LENSES: dict[str, dict] = {
    "math": {
        "title": "Mathematics and data science",
        "strands": ["conceptual understanding", "procedural fluency", "strategic competence",
                    "adaptive reasoning", "productive disposition"],
        "strands_source": "the five strands of mathematical proficiency (National Research Council, "
                          "Adding It Up, 2001)",
        "practices": "Mathematical Practices MP1-MP8 (Common Core, via Learning Commons)",
        "checks": ["run every number and every piece of code before calling it correct",
                   "say which steps are by hand and which are computed",
                   "label anything that can't be checked as unchecked"],
        "examples": "5 to 20 numbers, or a handful of words or vectors, workable by hand",
    },
    "philosophy": {
        "title": "Philosophy and close reading",
        "strands": ["close reading", "reconstructing an argument", "charitable interpretation",
                    "raising and answering the strongest objection", "connecting concepts across thinkers",
                    "writing a position you can defend"],
        "strands_source": "the harness's own lens for philosophical work",
        "practices": "",
        "checks": ["quote briefly and cite the passage (work, section or page) for every claim about a text",
                   "keep what the text says apart from the interpretation of it",
                   "say when a reading is contested, and state the main readings fairly",
                   "never invent a quotation; if the passage isn't at hand, say so"],
        "examples": "one short passage, two sentences to compare, or a toy model of the concept",
    },
    "general": {
        "title": "General",
        "strands": ["framing a problem", "judging evidence", "explaining clearly", "connecting ideas",
                    "learning something new", "working with others"],
        "strands_source": "the lasting capacities the harness aims at (Dewey's reflective thinking)",
        "practices": "",
        "checks": ["check facts and sources before giving them", "label anything unchecked"],
        "examples": "something small enough to hold in mind at once, from the learner's interests",
    },
}


def lens_for(arc: dict) -> str:
    """The arc's lens: as set, else math when its path uses the data-science program, else general."""
    if arc.get("lens") in LENSES:
        return arc["lens"]
    if any(str(i.get("idea", "")).startswith("data-scientist:") for i in arc.get("path", [])):
        return "math"
    return "general"
