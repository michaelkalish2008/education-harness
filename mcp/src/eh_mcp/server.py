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
    "Education Harness is a visible learning companion: keeps the learner's place, their own words and goals. "
    "Invoke it implicitly for ordinary requests to learn, study, understand, practice, prepare for school or an "
    "interview, or improve professional capability. "
    "Treat 'Let's learn' as the canonical explicit invocation. If selected without a specific request or asked "
    "what it does, name Education Harness and show these starters: 'Let's learn', 'Teach me <topic>', 'Show me the data-science path', "
    "'Let's go', and 'Where am I?'. Never require the learner to know MCP, tool or skill names. "
    "A brand-new learner gets move 'welcome': topic first (parse their first message), at most one plain "
    "question, then a first small lesson they do something in; teach phrases just in time and record each "
    "with setup(action='introduced', feature=...). The guided tour is opt-in: setup(action='tour') when they "
    "say 'show me how this works'. "
    "Guest mode ('let's try this as a guest'): setup(action='guest_start') switches every tool to a blank, "
    "short-lived space; while where_am_i shows 'guest', use nothing stored about the owner. "
    "Be fast: call where_am_i once at the start of a chat, then use about one tool call per learner turn, "
    "made alongside your reply. Never show internal profile labels; ask in everyday words, one question a turn, "
    "and calibrate level from the learner's work, not self-report. Defer lesson mode, sociability and mastery "
    "mode until they matter; save any profile value only on the learner's yes. "
    "Inspect relevant loaded standards as prerequisite evidence. "
    "One voice; end each reply with the next step. A refusal comes back as {'refused': reason}: "
    "say it plainly and offer the closest thing you can do."
)


def workspace_root() -> Path:
    return Path(os.environ.get("EH_WORKSPACE", Path.home() / "learning")).expanduser()


CHANGES_THE_MAP = {"set_arc", "write_plan", "standards", "note", "reveal", "set_status", "bookmark", "save_doc", "profile", "catalog"}

NOTE_KINDS = ("attempt", "question", "confusion", "insight", "thought", "keep", "slip", "shared", "heard_back",
              "diary", "session", "review")

CHATGPT_TOOLS = {
    "where_am_i", "set_arc", "write_plan", "note", "look_back", "reveal", "bookmark", "profile",
    "catalog", "knowledge_map", "setup", "save_doc",
}


def build_server(root: Path | None = None, *, chatgpt: bool = False) -> MCPServer:
    from .guest import ActiveWorkspace, Guests
    guests = Guests(root or workspace_root(), Workspace)
    guests.sweep()
    ws = ActiveWorkspace(guests)
    server = MCPServer(name="education-harness", version="0.21.0", instructions=INSTRUCTIONS)

    def tool(fn=None, *, meta: dict | None = None):
        if fn is None:
            return lambda f: tool(f, meta=meta)
        if chatgpt and fn.__name__ not in CHATGPT_TOOLS:
            return fn
        @functools.wraps(fn)
        def wrapped(*args: Any, **kwargs: Any) -> dict:
            try:
                guests.touch()
                out = fn(*args, **kwargs)
            except HarnessError as e:
                return {"refused": str(e)}
            if fn.__name__ in CHANGES_THE_MAP:
                ws.orient.refresh_map()
            return out
        return server.tool(meta=meta)(wrapped) if meta else server.tool()(wrapped)

    # ---------------------------------------------------------------- where
    @tool
    def where_am_i(focus: str = "", space: str = "", journey: bool = False, journey_url: str = "") -> dict:
        """Call once at the start of a chat and when the learner asks where they are or what's next.
        Returns the current step and its plan, open questions, bookmarks, the learner's goals (arcs),
        what is still unknown about them (ask_later), defined onboarding choices, relevant loaded math
        standards for prerequisite calibration, and one suggested move. For a new learner, focus may be the
        topic/project title even when no saved goal exists. space: the Claude project's name. Rewrites MAP.md
        and the journey pages (views/JOURNEY.html, goals/<goal>/JOURNEY.html). journey=true (the learner asks to see their journey or map) also returns the journey
        map's data and its page template path: fill the template's __JOURNEY_DATA__ with the data and publish
        it. journey_url: after publishing, pass the page's URL once so later updates republish the same page."""
        if journey_url:
            ws.journey.set_link(journey_url)
        out = ws.orient.where_am_i(focus, space)
        if ws.is_guest:
            out["guest"] = guests.status()["active"]
        if journey or journey_url:
            j = ws.journey.write(out.get("suggested"))
            out["journey"] = {"data": j["data"], "template": j["template"], "file": j.get("file", "")}
        return out

    @tool
    def set_arc(goal: str = "", path: list[dict] | None = None, name: str = "", why: str = "", lens: str = "",
                space: str = "", cadence: str = "", change: str = "") -> dict:
        """Save a goal (an arc) only after the learner says yes. goal in their words; path: ordered items
        {title, idea? ('data-scientist:calculus-foundations'), project?} (defaults to the goal itself); name: a short handle
        ('causal-inference'), a new one adds a goal beside the others; lens: math, philosophy or general;
        space: the Claude project; cadence: how often they want to check in, in their words. With only
        name plus space, lens or cadence, updates those on an existing goal."""
        if not goal and name and path is None and not why and not change:
            return ws.orient.set_arc_space(name, space, lens, cadence)
        return ws.orient.set_arc(goal, path, why, change, name, space, lens, cadence)

    @server.resource("ui://education-harness/catalog", name="catalog_view", title="Learning catalog",
                     description="The learner's local catalog of lessons and trajectories.",
                     mime_type="text/html;profile=mcp-app",
                     meta={"ui": {"prefersBorder": False, "csp": {"connectDomains": [], "resourceDomains": []}}})
    def catalog_view() -> str:
        return ws.catalog.render(ws.catalog.data()) or ""

    @tool(meta={"ui": {"resourceUri": "ui://education-harness/catalog", "visibility": ["model", "app"]},
                "openai/ui": {"entrypoints": [{"type": "thread"}]}})
    def catalog(action: str = "show", item: str = "", priority: str = "", rank: int = 0,
                kind: str = "", title: str = "", provider: str = "", progress: str = "",
                notes: str = "", url: str = "") -> dict:
        """Show or organize the local learning catalog. action: show; archive or restore (item); prioritize
        (item, priority: now/next/later/someday); rank (item, positive rank); classify (item, kind:
        ad-hoc/developing/structured/continuous); add_external (title, optional provider/progress/notes/url/kind/
        priority) for learner-reported work in tools without MCP access. item is a project slug, arc:<name> or
        external:<name>. Opens the catalog inline where the app shows embedded views; also returns catalog
        data and the generated views/CATALOG.html file. The learner controls every organization change."""
        return ws.catalog.manage(action, item, priority, rank, kind, title, provider, progress, notes, url)

    @server.resource("ui://education-harness/knowledge-map", name="knowledge_map_view",
                     title="Knowledge Map", description="Interactive 3D PCA view of the local TurboQuant knowledge base.",
                     mime_type="text/html;profile=mcp-app",
                     meta={"ui": {"prefersBorder": False, "csp": {"connectDomains": [],
                                                                    "resourceDomains": []}}})
    def knowledge_map_view() -> str:
        from .knowledge_map import PLACEHOLDER, template_path
        empty = {"points": [], "count": 0, "scope": "domain", "explained_variance": [0, 0, 0],
                 "note": "Waiting for the local knowledge-map data."}
        return template_path().read_text(encoding="utf-8").replace(PLACEHOLDER, json.dumps(empty), 1)

    @server.tool(title="Explore knowledge map", structured_output=True,
                 meta={"ui": {"resourceUri": "ui://education-harness/knowledge-map",
                               "visibility": ["model", "app"]},
                       "openai/ui": {"entrypoints": [{"type": "global"}, {"type": "thread"}]}})
    def knowledge_map(scope: str = "domain", max_points: int = 600) -> dict[str, Any]:
        """Open an embedded interactive 3D PCA explorer for local TurboQuant vectors. scope:
        domain (default), reflection, reference, meta or all; max_points: 3-2000. Requires optional local
        smart search. Also saves views/KNOWLEDGE-MAP.html as a host-independent fallback."""
        try:
            return ws.knowledge_map.write(scope, max_points)
        except HarnessError as e:
            return {"refused": str(e), "data": {"points": [], "count": 0, "scope": scope,
                                                  "explained_variance": [0, 0, 0], "note": str(e)}}

    @tool
    def write_plan(project: str, question: str, steps: list[dict], example: str = "", audience: str = "",
                   audience_format: str = "walkthrough", idea: str = "", solutions: dict | None = None,
                   sources: list[dict] | None = None, audience_where: str = "") -> dict:
        """Write a project plan (creating the project). Each step: {id, does, concepts, strong_version_shows,
        requires?, format? ('share-out' for the last step), terms? ({word: its one meaning here,
        as a concrete phrase} for words with an everyday meaning)}. audience: who the learner would show it to, as a
        relationship or place, never a name; audience_format: walkthrough, post, explainer, show-and-tell or
        portfolio (optional for any lesson; audience_where: github, web, post or other).
        solutions: optional {step_id: {hints, answer, method, follow_ons}}, only where an answer needs computed
        numbers worth checking ahead of time. sources: lesson sources actually consulted, such as
        [{kind: 'url', url, title?, library_id?}], [{kind: 'image', title, library_id?}] or
        [{kind: 'video', title, library_id?}]; never list gated,
        unread or non-visible content. Steps with work on them are never dropped."""
        out = ws.orient.write_plan(project, question, steps, example, idea=idea, sources=sources)
        if audience:
            kind = "public" if audience_format in ("post", "portfolio") else "person"
            out["audience"] = ws.share.set_audience(project, audience, kind, audience_format,
                                                    audience_where)["audience"]
        for sid, sol in (solutions or {}).items():
            ws.write_solution(project, sid, sol.get("hints", []), sol.get("answer", ""), sol.get("method", ""),
                              sol.get("follow_ons", []))
        if solutions:
            out["solutions"] = sorted(solutions)
        return out

    # ---------------------------------------------------------------- notes
    @tool
    def note(text: str, kind: str, project: str = "", step: str = "", concept: str = "", responds_to: str = "",
             who: str = "", how: str = "", where: str = "", helped: str = "", follow_on: str = "",
             link: str = "") -> dict:
        """Keep something in the learner's own words. kind:
        attempt (their work on a step; follow_on if on a sibling problem), question or confusion (stays open
        until a later note answers it via responds_to), insight or thought, keep (what they understand about a
        concept, for later recall; needs concept), slip (where work went sideways and what helped, only if the
        learner agreed to keep slips), shared (they explained, showed or posted it: who as a relationship, how,
        where, link if they posted it), heard_back (how it landed), diary, session (one line at the end of a session), review (a run-through
        of one review card: responds_to is the card id from look_back(kind='review'), text is what they said
        this time, kept on the concept)."""
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
            if project and (ws.share._share_step(project) or link or how == "posted"):
                return ws.share.mark_shared(project, how or "explained", where, who, link=link, note=text)
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
        if kind == "review":
            return ws.review.mark(responds_to, text, project, step)
        k = {"thought": "gist"}.get(kind, kind)
        anchor = "concept" if concept else ("step" if (project and step) else "day")
        return ws.journal.annotate(text, k, anchor, concept, project, step, responds_to)

    @tool
    def look_back(query: str = "", concept: str = "", project: str = "", since: str = "", until: str = "",
                  kind: str = "", grep: str = "", limit: int = 8, write: bool = False, modality: str = "computer",
                  audience: str = "alone", consent: str = "") -> dict:
        """Bring the learner's own record back. concept: everything on one concept (their notes, where it came
        up, what it builds on). query: search notes, journal, library and more (grep: an exact phrase to find
        inside library originals). kind='open': unanswered questions; kind='report': the evidence for a progress
        or retrospective report; kind='review': a run-through of past learnings, one card per concept (their
        kept words, insights, answered questions), least-recently-reviewed first. Otherwise: the journal,
        day by day, for since/until/project (default 14 days);
        write=true saves it as a file. Report: modality computer|phone|voice; audience (who else is present);
        consent all|positive|none once the learner answers the returned question."""
        if kind == "open":
            return ws.journal.open_questions(project, limit)
        if kind == "report":
            return ws.reports.report_evidence(since, until, project, modality=modality, audience=audience,
                                              consent=consent)
        if kind == "review":
            return ws.review.deck(project, concept, limit)
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

    @tool
    def standards(action: str = "show", project: str = "", step: str = "", code: str = "", decision: str = "",
                  evidence: str = "", set: str = "", origin: str = "", issuer: str = "", source: dict | None = None,
                  items: list[dict] | None = None, query: str = "", confirmed: bool = False) -> dict:
        """Lesson sidecar (reports read only this): show, review (code, decision accept|decline), add (code, step,
        evidence), drop. Expectation sets: sets, create (set, origin external|personal, issuer+source if external),
        items (set, items [{statement}], confirmed after the learner's yes), retire (set, code), search (query)."""
        if action in ("show", "review", "add", "drop"):
            return ws.alignment.manage(action, project, step, code, decision, evidence)
        a = {"sets": "list", "items": "add", "retire": "retire", "create": "create", "search": "search",
             "archive": "archive", "restore": "restore", "show_set": "show"}.get(action)
        if not a:
            raise HarnessError("action: show, review, add, drop, sets, create, items, show_set, retire, archive, "
                               "restore or search.")
        return ws.expectations.manage(a, set, origin, "", issuer, None, source, items, code, query, confirmed)

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
                 title: str = "", audience: str = "alone", consent: str = "", target: str = "",
                 files: dict | None = None, include: list[str] | None = None) -> dict:
        """Save something the learner has read or written. kind: report (since/until), retro (answers: any of
        went_well, was_hard, surprised, differently, how_i_learn, sharing, next), share_draft (a new version,
        from their own words), defense (their words, never paraphrased: first as a draft, then reviewed=true
        after they've read it), portfolio (optional for any lesson: target github|web|post|other, files
        {relative path: text from their words}, include [project-relative paths of their own work]; written to
        projects/<project>/portfolio/<target>/, never published by the harness)."""
        if kind == "report":
            import datetime as _dt
            return ws.reports.save_report(text, since or _dt.date.today().isoformat(),
                                          until or _dt.date.today().isoformat(), project, title, audience, consent)
        if kind == "retro":
            return ws.share.save_retrospective(answers or {}, project)
        if kind == "share_draft":
            return ws.share.save_share_draft(project, text)
        if kind == "defense":
            return ws.record_defense(project, step, text, parked, reviewed)
        if kind == "portfolio":
            return ws.share.build_portfolio(project, target, files, include, title)
        raise HarnessError("kind must be report, retro, share_draft, defense or portfolio.")

    @tool
    def profile(action: str = "show", change: dict | None = None, proposal_id: str = "", reason: str = "") -> dict:
        """The learner's profile (interests, access needs, formats that fit, lesson_mode: structured,
        semi-structured or free-form; sociability: group, guided or solo; mastery_mode: written-practical,
        spoken or both; depth_mode: civic-overview, foundational, practitioner or advanced;
        learning_context: job-interview,
        school, curiosity-personal-growth or professional-growth, with school_level, target_role or
        professional_context when relevant; voice_mode: the learner's words for how to teach when they
        are only listening, e.g. on a walk or driving; whether to keep slips). show;
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
                concepts: list[str] | None = None, how: str = "opened", tier: str = "", confirmed: bool = False,
                url: str = "") -> dict:
        """The learner's own library (opt-in). action: add (path, area), add_url (public URL, area; returns the
        publicly exposed text for planning), summarize (doc_id, title, a 10-200 word
        summary in your words, sections [{heading, anchor, summary}]), list (area), check (changed originals),
        use (doc_ids, how), tidy (cool what's unused), tier (doc_ids, tier: cold or active), forget (doc_id, only
        with confirmed=true after the learner's yes). Search it with look_back."""
        if action == "add":
            return ws.library.add(path, area, tags, concepts)
        if action == "add_url":
            return ws.library.add_url(url, area, tags, concepts)
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
        raise HarnessError("action must be add, add_url, summarize, list, check, use, tidy, tier or forget.")

    @tool
    def setup(action: str = "status", scope: str = "domain", max_points: int = 600, feature: str = "") -> dict:
        """Opt-in features. action: status; tour (seed and start the opt-in guided tour of the harness) /
        skip_tour; guest_start (feature: optional guest name; a blank, separate space so a guest, or the owner
        testing, starts as a brand-new learner) / guest_keep (feature: session, day or week) / guest_end
        (feature: '' deletes the space now, or day/week keeps it) / guest_resume (feature: id) / guest_status;
        introduced (feature: a phrase just taught to the learner, e.g. "hint", "note this",
        "place saved", "lets go", "look back", "where am i"; recorded once so it isn't taught again); smart_search_on / smart_search_off (a small local model, about
        70 MB once); load_standards (pin openly licensed Common Core math standards from a download on this
        computer, with attribution); rebuild_index; knowledge_map (scope: domain/reflection/reference/meta/all,
        max_points up to 2000) writes a private interactive 3D PCA view of TurboQuant vectors."""
        if action == "status":
            return {"smart_search": ws.semantic.status(), "standards": ws.knowledge._state().get("standards_source"),
                    "tour": ws.tour.summary()}
        if action == "tour":
            out = ws.tour.start()
            ws.orient.refresh_map()
            return out
        if action == "skip_tour":
            return ws.tour.skip()
        if action == "guest_start":
            return guests.start(feature)
        if action == "guest_keep":
            return guests.keep(feature or "session")
        if action == "guest_end":
            return guests.end(feature)
        if action == "guest_resume":
            return guests.resume(feature)
        if action == "guest_status":
            return guests.status()
        if action == "introduced":
            return ws.tour.introduce(feature)
        if action in ("smart_search_on", "smart_search_off"):
            return ws.enable_semantic_search("on" if action.endswith("on") else "off")
        if action == "load_standards":
            from .standards import default_folder
            return ws.knowledge.load_standards(str(default_folder()))
        if action == "rebuild_index":
            return ws.rebuild_index()
        if action == "knowledge_map":
            return ws.knowledge_map.write(scope, max_points)
        raise HarnessError("action must be status, tour, skip_tour, guest_start, guest_keep, guest_end, guest_resume, guest_status, introduced, smart_search_on, smart_search_off, load_standards, rebuild_index or knowledge_map.")

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
