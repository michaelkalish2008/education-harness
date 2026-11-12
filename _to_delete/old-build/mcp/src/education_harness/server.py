from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from .core import Harness


mcp = FastMCP("education-harness")


def service() -> Harness:
    return Harness(Path(os.environ.get("EDUCATION_HARNESS_WORKSPACE", Path.cwd())))


@mcp.tool()
def init_project(slug: str, question: str | None = None, source: str | None = None) -> dict[str, Any]:
    """Create learning/ and one new learner or default-program project."""
    return service().init_project(slug, question, source)


@mcp.tool()
def get_plan(project: str) -> dict[str, Any]:
    """Read a project's program.yaml."""
    return service().get_plan(project)


@mcp.tool()
def get_progress(project: str, role: str, step_id: str | None = None) -> dict[str, Any]:
    """Read progress and open handoff notes addressed to one role."""
    return service().get_progress(project, role, step_id)


@mcp.tool()
def write_solution(project: str, step_id: str, hints: list[str], method: str, follow_on_problems: list[dict[str, str]], caller_role: str) -> dict[str, Any]:
    """Write a gated solution; only the lesson-planner role is accepted."""
    return service().write_solution(project, step_id, hints, method, follow_on_problems, caller_role)


@mcp.tool()
def record_attempt(project: str, step_id: str, text: str, kind: str = "attempt") -> dict[str, Any]:
    """Save any nonblank learner contribution as an attempt."""
    return service().record_attempt(project, step_id, text, kind)


@mcp.tool()
def reveal_solution(project: str, step_id: str, level: str, hint_number: int = 1) -> dict[str, Any]:
    """Reveal a hint, shown answer, or method and always pair it with a follow-on."""
    return service().reveal_solution(project, step_id, level, hint_number)


@mcp.tool()
def record_defense(project: str, step_id: str, learner_words: str, parked_questions: list[str] | None = None) -> dict[str, Any]:
    """Save a learner-reviewed defense in the learner's own words."""
    return service().record_defense(project, step_id, learner_words, parked_questions)


@mcp.tool()
def post_note(project: str, step_id: str, to_role: str, from_role: str, text: str) -> dict[str, Any]:
    """Post a role-scoped handoff note."""
    return service().post_note(project, step_id, to_role, from_role, text)


@mcp.tool()
def set_status(project: str, step_id: str, status: str, caller_role: str, evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    """Set step status while enforcing drafted and defended evidence gates."""
    return service().set_status(project, step_id, status, caller_role, evidence)


@mcp.tool()
def propose_profile_change(proposal: dict[str, Any], accepted: bool = False) -> dict[str, Any]:
    """Queue a profile proposal, applying it only when explicitly accepted."""
    return service().propose_profile_change(proposal, accepted)


@mcp.tool()
def log_session(text: str) -> dict[str, Any]:
    """Append a private session record."""
    return service().log_session(text)


@mcp.tool()
def add_diary_entry(text: str, tags: dict[str, str] | None = None) -> dict[str, Any]:
    """Save and keyword-index an optional diary entry."""
    return service().add_diary_entry(text, tags)


@mcp.tool()
def check_links(urls: list[str], timeout: float = 8) -> list[dict[str, Any]]:
    """Check cited URLs without judging whether they support a claim."""
    return service().check_links(urls, timeout)


@mcp.tool()
def search_memory(query: str, tags: dict[str, str] | None = None, limit: int = 8) -> list[dict[str, Any]]:
    """Search private memory with SQLite FTS5 and optional exact tag filters."""
    return service().search_memory(query, tags, limit)


@mcp.tool()
def extract_learnings(project: str, learning: dict[str, Any]) -> dict[str, Any]:
    """Validate and store one source-linked learning record."""
    return service().extract_learnings(project, learning)


@mcp.tool()
def enable_semantic_search(enabled: bool) -> dict[str, Any]:
    """Record semantic-search intent; installation remains an explicit later action."""
    return service().enable_semantic_search(enabled)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

