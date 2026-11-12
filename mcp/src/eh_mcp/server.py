"""MCP server (stdio) exposing the harness tools over the learner's files."""

from __future__ import annotations

import functools
import json
import os
from pathlib import Path
from typing import Any

from mcp.server.mcpserver import MCPServer

from .core import HarnessError, Workspace

INSTRUCTIONS = (
    "Education harness: keeps the learner's place, their own words and their goals in local files. "
    "Be fast: call where_am_i once at the start of a chat, then use about one tool call per learner turn, "
    "made alongside your reply. For a new learner, calibrate their goal and notation/background before "
    "presenting content; inspect relevant loaded standards as prerequisite evidence. "
    "One voice; end each reply with the next step. A refusal comes back as {'refused': reason}: "
    "say it plainly and offer the closest thing you can do."
)


def workspace_root() -> Path:
    return Path(os.environ.get("EH_WORKSPACE", Path.home() / "learning")).expanduser()


CHANGES_THE_MAP = {"set_arc", "write_plan", "note", "reveal", "set_status", "bookmark", "save_doc", "profile"}

NOTE_KINDS = ("attempt", "question", "confusion", "insight", "thought", "keep", "slip", "shared", "heard_back",
              "diary", "session")

CHATGPT_TOOLS = {
    "where_am_i", "set_arc", "write_plan", "note", "look_back", "reveal", "bookmark", "profile",
}


def build_server(root: Path | None = None, *, chatgpt: bool = False) -> MCPServer:
    ws = Workspace(root or workspace_root())
    server = MCPServer(name="education-harness", version="0.6.0", instructions=INSTRUCTIONS)

    def tool(fn):
        if chatgpt and fn.__name__ not in CHATGPT_TOOLS:
            return fn
        @functools.wraps(fn)
        def wrapped(*args: Any, **kwargs: Any) -> dict:
            try:
                out = fn(*args, **kwargs)
            except HarnessError as e:
                return {"refused": str(e)}
            if fn.__name__ in CHANGES_THE_MAP:
                ws.orient.refresh_map()
            return out
        return server.tool()(wrapped)

    # ---------------------------------------------------------------- where
    @tool
    def where_am_i(focus: str = "", space: str = "") -> dict:
        """Call once at the start of a chat and when the learner asks where they are or what's next.
        Returns the current step and its plan, open questions, bookmarks, the learner's goals (arcs),
        what is still unknown about them (ask_later), relevant loaded math standards for prerequisite
        calibration, and one suggested move. For a new learner, focus may be the topic/project title even
        when no saved goal exists. space: the Claude project's name. Rewrites MAP.md."""
        return ws.orient.where_am_i(focus, space)

    @tool
    def set_arc(goal: str = "", path: list[dict] | None = None, name: str = "", why: str = "", lens: str = "",
                space: str = "", cadence: str = "", change: str = "") -> dict:
        """Save a goal (an arc) only after the learner says yes. goal in their words; path: ordered items
        {title, idea? ('data-scientist:fit'), project?} (defaults to the goal itself); name: a short handle
        ('causal-inference'), a new one adds a goal beside the others; lens: math, philosophy or general;
        space: the Claude project; cadence: how often they want to check in, in their words. With only
        name plus space, lens or cadence, updates those on an existing goal."""
        if not goal and name:
            return ws.orient.set_arc_space(name, space, lens, cadence)
        return ws.orient.set_arc(goal, path, why, change, name, space, lens, cadence)

    @tool
    def write_plan(project: str, question: str, steps: list[dict], example: str = "", audience: str = "",
                   audience_format: str = "walkthrough", idea: str = "", solutions: dict | None = None) -> dict:
        """Write a project plan (creating the project). Each step: {id, does, concepts, strong_version_shows,
        requires?, format? ('share-out' for the last step)}. audience: who the learner would show it to, as a
        relationship or place, never a name; audience_format: walkthrough, post, explainer or show-and-tell.
        solutions: optional {step_id: {hints, answer, method, follow_ons}}, only where an answer needs computed
        numbers worth checking ahead of time. Steps with work on them are never dropped."""
        out = ws.orient.write_plan(project, question, steps, example, idea=idea)
        if audience:
            kind = "public" if audience_format == "post" else "person"
            out["audience"] = ws.share.set_audience(project, audience, kind, audience_format)["audience"]
        for sid, sol in (solutions or {}).items():
            ws.write_solution(project, sid, sol.get("hints", []), sol.get("answer", ""), sol.get("method", ""),
                              sol.get("follow_ons", []))
        if solutions:
            out["solutions"] = sorted(solutions)
        return out

    # ---------------------------------------------------------------- notes
    @tool
    def note(text: str, kind: str, project: str = "", step: str = "", concept: str = "", responds_to: str = "",
             who: str = "", how: str = "", where: str = "", helped: str = "", follow_on: str = "") -> dict:
        """Keep something in the learner's own words. kind:
        attempt (their work on a step; follow_on if on a sibling problem), question or confusion (stays open
        until a later note answers it via responds_to), insight or thought, keep (what they understand about a
        concept, for later recall; needs concept), slip (where work went sideways and what helped, only if the
        learner agreed to keep slips), shared (they explained, showed or posted it: who as a relationship, how,
        where), heard_back (how it landed), diary, session (one line at the end of a session)."""
        if kind not in NOTE_KINDS:
            raise HarnessError(f"kind must be one of {NOTE_KINDS}.")
        if kind == "attempt":
            if not (project and step):
                raise HarnessError("An attempt needs the project and step.")
            return ws.record_attempt(project, step, text, follow_on or None)
        if kind == "keep":
            if not concept:
                raise HarnessError("Keep it under which concept? (e.g. 'chain rule')")
            return ws.board.remember(concept, text, project, step)
        if kind == "slip":
            if not (project and step):
                raise HarnessError("A slip needs the project and step.")
            return ws.journal.record_error(project, step, text, "slip", helped)
        if kind == "shared":
            if project and ws.share._share_step(project):
                return ws.share.mark_shared(project, how or "explained", where, who, note=text)
            return ws.reports.record_shared(how if how in ("explained", "worked-with", "helped", "asked", "showed")
                                            else "explained", text, who, project, step)
        if kind == "heard_back":
            if not project:
                raise HarnessError("Which project did they react to?")
            return ws.share.heard_back(project, text, who)
        if kind == "diary":
            return ws.add_diary_entry(text, project=project or None)
        if kind == "session":
            return ws.log_session(text, project or None)
        k = {"thought": "gist"}.get(kind, kind)
        anchor = "concept" if concept else ("step" if (project and step) else "day")
        return ws.journal.annotate(text, k, anchor, concept, project, step, responds_to)

    @tool
    def look_back(query: str = "", concept: str = "", project: str = "", since: str = "", until: str = "",
                  kind: str = "", grep: str = "", limit: int = 8, write: bool = False) -> dict:
        """Bring the learner's own record back. concept: everything on one concept (their notes, where it came
        up, what it builds on). query: search notes, journal, library and more (grep: an exact phrase to find
        inside library originals). kind='open': unanswered questions; kind='report': the evidence for a progress
        or retrospective report. Otherwise: the journal, day by day, for since/until/project (default 14 days);
        write=true saves it as a file."""
        if kind == "open":
            return ws.journal.open_questions(project, limit)
        if kind == "report":
            return ws.reports.report_evidence(since, until, project)
        if concept:
            return ws.board.recall(concept)
        if query or grep:
            return ws.search_memory(query, None, project or None, limit, None, grep or None, 1 if concept else 0,
                                    "all")
        return ws.journal.journal(since, until, project, write)

    # ----------------------------------------------------------------- steps
    @tool
    def reveal(project: str, step: str, what: str) -> dict:
        """Show what the learner asks to see, whenever they ask: 'hint', 'answer' or 'method'. Logged as seen,
        never as failure. Serves a pre-written solution if there is one; otherwise work it out and check it."""
        return ws.reveal_solution(project, step, what)

    @tool
    def set_status(project: str, step: str, status: str, role: str = "tutor", checklist: dict | None = None) -> dict:
        """Mark a step 'seen' or 'drafted' (the learner's own work exists). 'defended' only from the validator,
        with checklist {explained, questions_worked (>=3), path_not_taken, limit_named}."""
        return ws.set_status(project, step, status, role, checklist)

    # -------------------------------------------------------------- bookmark
    @tool
    def bookmark(action: str, label: str = "", thinking: str = "", next_move: str = "", project: str = "",
                 step: str = "", open_question: str = "", tried: str = "", which: str = "", auto: bool = False,
                 resolved: bool = False, confirmed: bool = False) -> dict:
        """action: save (thinking in their words + next_move; auto=true when the learner stops: replaces that
        project's last automatic one and logs the session, so ending is one call), list, open (which: id or words), update (which + changed fields), remove (which, or
        resolved=true for done ones; first without confirmed to read back, then confirmed=true on their yes)."""
        o = ws.orient
        if action == "save":
            out = o.save_checkpoint(label, thinking, next_move, project, step, open_question, tried, auto)
            if auto:  # a stop: the session line comes with it, so ending a session is one call
                ws.log_session(f"Stopped: {next_move}", project or None)
            return out
        if action == "list":
            return o.list_checkpoints(project)
        if action == "open":
            return o.open_checkpoint(which)
        if action == "update":
            return o.update_checkpoint(which, label, thinking, next_move, open_question, tried, step)
        if action == "remove":
            return o.remove_checkpoints([which] if which else None, resolved, confirmed)
        raise HarnessError("action must be save, list, open, update or remove.")

    # ------------------------------------------------------------------ docs
    @tool
    def save_doc(kind: str, text: str = "", project: str = "", step: str = "", answers: dict | None = None,
                 reviewed: bool = False, parked: list[str] | None = None, since: str = "", until: str = "",
                 title: str = "") -> dict:
        """Save something the learner has read or written. kind: report (since/until), retro (answers: any of
        went_well, was_hard, surprised, differently, how_i_learn, sharing, next), share_draft (a new version,
        from their own words), defense (their words, never paraphrased: first as a draft, then reviewed=true
        after they've read it)."""
        if kind == "report":
            import datetime as _dt
            return ws.reports.save_report(text, since or _dt.date.today().isoformat(),
                                          until or _dt.date.today().isoformat(), project, title)
        if kind == "retro":
            return ws.share.save_retrospective(answers or {}, project)
        if kind == "share_draft":
            return ws.share.save_share_draft(project, text)
        if kind == "defense":
            return ws.record_defense(project, step, text, parked, reviewed)
        raise HarnessError("kind must be report, retro, share_draft or defense.")

    @tool
    def profile(action: str = "show", change: dict | None = None, proposal_id: str = "", reason: str = "") -> dict:
        """The learner's profile (interests, access needs, formats that fit, whether to keep slips). show;
        propose a change; list proposals; accept or reject one. Nothing changes without the learner's yes."""
        if action == "show":
            ws.ensure_workspace()
            from .core import _read_yaml
            return {"profile": _read_yaml(ws.private / "learner.yaml", {}) or {}}
        return ws.propose_profile_change(action, change, proposal_id or None, reason)

    # -------------------------------------------------------------- opt-in
    @tool
    def library(action: str, path: str = "", area: str = "", doc_id: str = "", doc_ids: list[str] | None = None,
                title: str = "", summary: str = "", sections: list[dict] | None = None, tags: list[str] | None = None,
                concepts: list[str] | None = None, how: str = "opened", tier: str = "", confirmed: bool = False) -> dict:
        """The learner's own library (opt-in). action: add (path, area), summarize (doc_id, title, a 10-200 word
        summary in your words, sections [{heading, anchor, summary}]), list (area), check (changed originals),
        use (doc_ids, how), tidy (cool what's unused), tier (doc_ids, tier: cold or active), forget (doc_id, only
        with confirmed=true after the learner's yes). Search it with look_back."""
        if action == "add":
            return ws.library.add(path, area, tags, concepts)
        if action == "summarize":
            return ws.library.write_summary(doc_id, title, summary, sections, "", tags, concepts)
        if action == "list":
            return ws.library.list(area or None)
        if action == "check":
            return ws.library.check()
        if action == "use":
            return ws.knowledge.record_use(doc_ids or [doc_id], how)
        if action == "tidy":
            return ws.knowledge.sweep()
        if action == "tier":
            return ws.knowledge.set_tier(doc_ids or [doc_id], tier)
        if action == "forget":
            return ws.knowledge.forget(doc_id, confirmed)
        raise HarnessError("action must be add, summarize, list, check, use, tidy, tier or forget.")

    @tool
    def setup(action: str = "status") -> dict:
        """Opt-in features. action: status; smart_search_on / smart_search_off (a small local model, about
        70 MB once); load_standards (pin openly licensed Common Core math standards from a download on this
        computer, with attribution); rebuild_index."""
        if action == "status":
            return {"smart_search": ws.semantic.status(), "standards": ws.knowledge._state().get("standards_source")}
        if action in ("smart_search_on", "smart_search_off"):
            return ws.enable_semantic_search("on" if action.endswith("on") else "off")
        if action == "load_standards":
            from .standards import default_folder
            return ws.knowledge.load_standards(str(default_folder()))
        if action == "rebuild_index":
            return ws.rebuild_index()
        raise HarnessError("action must be status, smart_search_on, smart_search_off, load_standards or rebuild_index.")

    @tool
    def check_links(urls: list[str]) -> dict:
        """Fetch each link and report the dead ones."""
        return ws.check_links(urls)

    return server  # smart search, if on, loads on the first search, not at start


def main() -> None:
    import sys
    if "--self-check" in sys.argv:
        from .selfcheck import run
        raise SystemExit(run())
    if "--semantic-check" in sys.argv:
        from .selfcheck import run_semantic
        raise SystemExit(run_semantic())
    if "--fetch-standards" in sys.argv:
        from .standards import fetch
        raise SystemExit(fetch())
    if "--load-standards" in sys.argv:
        from .standards import default_folder
        ws = Workspace(workspace_root())
        ws.ensure_workspace()
        r = ws.knowledge.load_standards(str(default_folder()))
        print(json.dumps(r, indent=2))
        return
    if "--rebuild-index" in sys.argv:
        print(Workspace(workspace_root()).rebuild_index())
        return
    build_server(chatgpt="--chatgpt" in sys.argv).run("stdio")
