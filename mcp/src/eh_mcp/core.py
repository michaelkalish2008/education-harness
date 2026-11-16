"""Core logic for the education harness MCP server.

Every function here reads and writes plain files under the learner's workspace
(``learning/``). The files are the source of truth; the search index is derived
from them. The MCP layer in ``server.py`` is a thin wrapper over this module, so
everything can be tested without a model in the loop.
"""

from __future__ import annotations

import datetime as _dt
import re
import shutil
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import yaml

from .index import Index
from .board import Board
from .journal import Journal
from .report import Reports
from .share import Share
from .orient import Orientation
from .journey import Journey
from .catalog import Catalog
from .knowledge_map import KnowledgeMap
from .review import Review
from .knowledge import Knowledge
from .library import GREP_RRF_K, GREP_SELECTIVITY_MAX, Library
from .semantic import SemanticSetup, extra_installed

PROGRAMS = Path(__file__).parent / "programs"

SCHEMA = 1
STATUSES = ("not started", "seen", "drafted", "defended")
REVEALS = ("hint", "answer", "method")
ROLES = ("tutor", "mentor", "validator", "organizer", "lesson planner", "facilitator", "archivist")

WORKSPACE_GITIGNORE = "# Private records never leave this computer\n.private/\nMAP.md\n"
# Generated pages carry the learner's notes, so they stay private too (older versions wrote them at the root).
GENERATED_IGNORES = ("MAP.md", "views/", "goals/", "JOURNEY.html", "CATALOG.html", "KNOWLEDGE-MAP.html")
PYPROJECT_TEMPLATE = """[project]
name = "{name}"
version = "0.1.0"
description = "Learning project: its own environment, managed by the education harness."
requires-python = ">=3.10"
dependencies = ["numpy", "ipykernel"]

[tool.uv]
package = false
"""
PRIVATE_DIRS = ("diary", "log", "attempts", "handoff", "learnings", "library", "index", "checkpoints", "concepts", "reflection", "journal", "reports", "share", "arcs")


class HarnessError(Exception):
    """A refusal the tool returns to the agent in plain words."""


def _now() -> _dt.datetime:
    return _dt.datetime.now().astimezone()


def _stamp(t: _dt.datetime | None = None) -> str:
    return (t or _now()).strftime("%Y-%m-%dT%H%M%S%f")


def _slug(text: str, fallback: str = "entry") -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:48] or fallback


def _check_name(value: str, what: str) -> str:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", value or ""):
        raise HarnessError(f"{what} must be lowercase letters, digits and hyphens: {value!r}")
    return value


def _read_yaml(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return default if data is None else data


def _write_yaml(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)
    tmp.replace(path)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class Workspace:
    """The learner's workspace: ``learning/`` with ``projects/``, ``inbox/`` and ``.private/``."""

    def __init__(self, root: str | Path):
        self.root = Path(root).expanduser().resolve()
        self.private = self.root / ".private"
        self.index = Index(self.private / "index" / "memory.sqlite")
        self.semantic = SemanticSetup(self.index, self.private)
        self.library = Library(self)
        self.knowledge = Knowledge(self)
        self.orient = Orientation(self)
        self.board = Board(self)
        self.journal = Journal(self)
        self.reports = Reports(self)
        self.share = Share(self)
        self.journey = Journey(self)
        self.catalog = Catalog(self)
        from .alignment import Alignment
        self.alignment = Alignment(self)
        from .expectations import Expectations
        self.expectations = Expectations(self)
        self.knowledge_map = KnowledgeMap(self)
        self.review = Review(self)

    # ------------------------------------------------------------------ paths
    @property
    def views_dir(self) -> Path:
        """Generated pages for everything: views/CATALOG.html, JOURNEY.html, KNOWLEDGE-MAP.html."""
        return self.root / "views"

    @property
    def goals_dir(self) -> Path:
        """One folder per goal (arc), holding that goal's JOURNEY.html."""
        return self.root / "goals"

    def retire_root_page(self, name: str) -> None:
        """Remove a generated page left at the workspace root by an older version (now in views/)."""
        old = self.root / name
        try:
            if old.is_file():
                old.unlink()
        except OSError:
            pass

    def project_dir(self, project: str) -> Path:
        return self.root / "projects" / _check_name(project, "project")

    def _require_project(self, project: str) -> Path:
        d = self.project_dir(project)
        if not (d / "program.yaml").exists():
            raise HarnessError(f"No project named {project!r}. Create it with init_project first.")
        return d

    def _handoff(self, project: str, step: str) -> Path:
        return self.private / "handoff" / project / _check_name(step, "step")

    # ------------------------------------------------------------- workspace
    def ensure_workspace(self) -> None:
        for d in ("inbox", "projects"):
            (self.root / d).mkdir(parents=True, exist_ok=True)
        for d in PRIVATE_DIRS:
            (self.private / d).mkdir(parents=True, exist_ok=True)
        gi = self.root / ".gitignore"
        if not gi.exists():
            _write_text(gi, WORKSPACE_GITIGNORE)
        have = set(gi.read_text(encoding="utf-8").split())
        missing = [x for x in GENERATED_IGNORES if x not in have]
        if missing:
            text = gi.read_text(encoding="utf-8")
            with gi.open("a", encoding="utf-8") as f:
                f.write(("" if text.endswith("\n") else "\n") + "\n".join(missing) + "\n")
        projects = self.root / "projects"
        for d in sorted(projects.iterdir()) if projects.exists() else []:
            if (d / "program.yaml").exists():
                self.ensure_python_env(d)
        if not (self.private / "learner.yaml").exists():
            _write_yaml(self.private / "learner.yaml", {"schema": SCHEMA})
        if not (self.private / "proposals.yaml").exists():
            _write_yaml(self.private / "proposals.yaml", {"schema": SCHEMA, "proposals": []})
        self.load_program_graph()

    def ensure_python_env(self, dest: Path) -> None:
        """Every project is its own uv project, so its packages never mix with another's:
        pyproject.toml (numpy and ipykernel to start; tutors `uv add` more) and a .gitignore for .venv/.
        Never overwrites; the environment itself is built by `uv run`/`uv sync` on first use."""
        py = dest / "pyproject.toml"
        if not py.exists():
            name = re.sub(r"[^a-z0-9-]+", "-", dest.name.lower()).strip("-") or "project"
            _write_text(py, PYPROJECT_TEMPLATE.format(name=name))
        gi = dest / ".gitignore"
        if not gi.exists():
            _write_text(gi, ".venv/\n__pycache__/\n.ipynb_checkpoints/\n")

    def init_project(self, project: str, question: str = "", from_program: str | None = None) -> dict:
        """Create the workspace if needed, then a project folder (copied or empty)."""
        self.ensure_workspace()
        dest = self.project_dir(project)
        if dest.exists():
            raise HarnessError(f"Project {project!r} already exists.")
        if from_program:
            src = Path(from_program).expanduser().resolve()
            if not (src / "program.yaml").exists():
                raise HarnessError(f"No program.yaml in {src}.")
            shutil.copytree(src, dest, ignore=shutil.ignore_patterns(".gitkeep", "rebuild*", "__pycache__"))
        else:
            dest.mkdir(parents=True)
            _write_yaml(dest / "program.yaml", {
                "schema": SCHEMA,
                "project": {"question": question or ""},
                "steps": [],
                "constellation": {},
            })
        for d in ("data", "solutions", "work", "portfolio"):
            (dest / d).mkdir(exist_ok=True)
        self.ensure_python_env(dest)
        if not (dest / "commitment.md").exists():
            _write_text(dest / "commitment.md", "# Commitment\n\nCadence: not set yet (the learner chooses, including none).\n")
        plan = _read_yaml(dest / "program.yaml", {})
        progress = {"schema": SCHEMA, "steps": {s["id"]: {"status": "not started", "seen": []}
                                                for s in plan.get("steps", []) if "id" in s}}
        _write_yaml(dest / "progress.yaml", progress)
        return {"project": project, "path": str(dest), "steps": list(progress["steps"])}

    # ------------------------------------------------------------- plan/state
    def get_plan(self, project: str) -> dict:
        return _read_yaml(self._require_project(project) / "program.yaml", {})

    def _progress(self, project: str) -> dict:
        d = self._require_project(project)
        prog = _read_yaml(d / "progress.yaml", {"schema": SCHEMA, "steps": {}})
        prog.setdefault("steps", {})
        return prog

    def _save_progress(self, project: str, prog: dict) -> None:
        _write_yaml(self.project_dir(project) / "progress.yaml", prog)

    def _step_state(self, prog: dict, step: str) -> dict:
        st = prog["steps"].setdefault(step, {"status": "not started", "seen": []})
        st.setdefault("seen", [])
        return st

    def _plan_step(self, project: str, step: str) -> dict:
        for s in self.get_plan(project).get("steps", []):
            if s.get("id") == step:
                return s
        raise HarnessError(f"Step {step!r} is not in {project}'s plan.")

    def get_progress(self, project: str, role: str | None = None) -> dict:
        prog = self._progress(project)
        out: dict[str, Any] = {"project": project, "steps": prog["steps"]}
        if role:
            out["notes"] = self._open_notes(project, role)
        return out

    # -------------------------------------------------------------- solutions
    def write_solution(self, project: str, step: str, hints: list[str], answer: str, method: str,
                       follow_ons: list[dict]) -> dict:
        """Lesson planner only. Every step needs at least two follow-on problems."""
        self._plan_step(project, step)
        if len(follow_ons or []) < 2:
            raise HarnessError("Each step needs at least two follow-on problems.")
        clean = []
        for i, f in enumerate(follow_ons, 1):
            if not str(f.get("problem", "")).strip():
                raise HarnessError("Every follow-on needs a problem.")
            clean.append({"id": f.get("id") or f"{step}-f{i}", "problem": f["problem"],
                          "solution": f.get("solution", "")})
        data = {"schema": SCHEMA, "step": step, "hints": list(hints or []), "answer": answer,
                "method": method, "follow_ons": clean}
        _write_yaml(self.project_dir(project) / "solutions" / f"{step}.yaml", data)
        return {"saved": f"solutions/{step}.yaml", "hints": len(data["hints"]), "follow_ons": len(clean)}

    def _solution(self, project: str, step: str) -> dict:
        sol = _read_yaml(self.project_dir(project) / "solutions" / f"{step}.yaml")
        if not sol:
            raise HarnessError(f"No solution written yet for {step}. Ask the lesson planner.")
        return sol

    # --------------------------------------------------------------- attempts
    def record_attempt(self, project: str, step: str, text: str, follow_on: str | None = None) -> dict:
        """Any real contribution counts: an explanation so far, a question, a hunch. Only a blank is refused."""
        self._plan_step(project, step)
        if not (text or "").strip():
            raise HarnessError("Nothing to save. Whatever the learner has so far counts, even a question.")
        t = _now()
        name = f"{_stamp(t)}{'-' + _check_name(follow_on, 'follow-on') if follow_on else ''}.md"
        path = self.private / "attempts" / project / step / name
        _write_text(path, text.strip() + "\n")
        prog = self._progress(project)
        st = self._step_state(prog, step)
        st["attempts"] = st.get("attempts", 0) + 1
        if follow_on and (follow_on == st.get("follow_on") or st.get("follow_on_owed")):
            st["follow_on_attempted"] = True
            st["follow_on_owed"] = False
        self._save_progress(project, prog)
        return {"saved": str(path.relative_to(self.root)), "follow_on_attempted": st.get("follow_on_attempted", False)}

    def reveal_solution(self, project: str, step: str, what: str) -> dict:
        """Never refuses. Logs what was seen. A pre-written solution is served when one exists;
        otherwise the tutor works it out and checks it in the open. Seeing an answer or method
        leaves a follow-on owed, which is offered, never required."""
        if what not in REVEALS:
            raise HarnessError(f"what must be one of {REVEALS}.")
        self._plan_step(project, step)
        sol = _read_yaml(self.project_dir(project) / "solutions" / f"{step}.yaml")
        prog = self._progress(project)
        st = self._step_state(prog, step)
        result: dict[str, Any] = {"step": step, "what": what}
        if not sol:
            if what not in st["seen"]:
                st["seen"].append(what)
            st.setdefault("seen_log", []).append({"what": what, "at": _now().isoformat(timespec="minutes")})
            if what in ("answer", "method"):
                st["follow_on_owed"] = True
                if st.get("status") == "not started":
                    st["status"] = "seen"
            self._save_progress(project, prog)
            result["content"] = None
            result["next"] = ("No pre-written solution: work it out now and check it (run the numbers, or cite "
                              "the passage) before showing it. Then offer a sibling problem, once.")
            return result
        if what == "hint":
            given = st.get("hints_given", 0)
            hints = sol.get("hints", [])
            if given < len(hints):
                result["content"] = hints[given]
                st["hints_given"] = given + 1
            else:
                result["content"] = "No more hints for this step; the answer or the method can be shown."
        elif what == "answer":
            result["content"] = sol.get("answer", "")
            result["next"] = ("The method stays to be found: work backward from this answer together. "
                              "Work on the method counts as the follow-on.")
            st["follow_on"] = st.get("follow_on") or f"{step}-backward"
        else:
            result["content"] = sol.get("method", "")
            used = set(st.get("follow_ons_used", []))
            fo = next((f for f in sol.get("follow_ons", []) if f["id"] not in used), None)
            if fo:
                st["follow_on"] = fo["id"]
                st.setdefault("follow_ons_used", []).append(fo["id"])
                st["follow_on_attempted"] = False
                result["follow_on"] = {"id": fo["id"], "problem": fo["problem"]}
                result["next"] = "Carry the method into this sibling problem, using the solution as a worked example."
            else:
                result["next"] = "All follow-ons for this step are used; the learner can move on whenever they like."
        if what not in st["seen"]:
            st["seen"].append(what)
        st.setdefault("seen_log", []).append({"what": what, "at": _now().isoformat(timespec="minutes"),
                                              **({"follow_on": st["follow_on"]} if what != "hint" and st.get("follow_on") else {})})
        if what in ("answer", "method") and st.get("status") == "not started":
            st["status"] = "seen"
        self._save_progress(project, prog)
        return result

    # ----------------------------------------------------------------- status
    def set_status(self, project: str, step: str, status: str, role: str,
                   checklist: dict | None = None) -> dict:
        """seen never blocks moving on; drafted needs work (and the follow-on after a reveal);
        defended only from the validator, with the three-part checklist."""
        if status not in STATUSES[1:]:
            raise HarnessError(f"status must be one of {STATUSES[1:]}.")
        self._plan_step(project, step)
        prog = self._progress(project)
        st = self._step_state(prog, step)
        revealed = bool({"answer", "method"} & set(st["seen"]))
        if status == "drafted":
            if not st.get("attempts"):
                raise HarnessError("Drafted needs the learner's own work on the step first (a note of kind attempt).")
        if status == "defended":
            if role != "validator":
                raise HarnessError("Only the validator marks a step defended.")
            c = checklist or {}
            missing = [k for k in ("explained", "path_not_taken", "limit_named") if not c.get(k)]
            if int(c.get("questions_worked", 0)) < 3:
                missing.append("questions_worked >= 3")
            if missing:
                raise HarnessError("Defended needs the full checklist; missing: " + ", ".join(missing))
            if revealed and not st.get("follow_on_attempted"):
                raise HarnessError("A defense counts work on a problem the learner hadn't seen solved; "
                                   "work a sibling problem first.")
            st["checklist"] = {**c, "at": _now().isoformat(timespec="seconds")}
        st["status"] = status
        self._save_progress(project, prog)
        marked = self.alignment.step_status(project, step, status)
        return {"step": step, "status": status, **({"standards_exercised": marked} if marked else {})}

    # --------------------------------------------------------------- handoffs
    def record_defense(self, project: str, step: str, record: str, parked: list[str] | None = None,
                       reviewed: bool = False) -> dict:
        """The learner's own words. Saved as a draft until the learner has reviewed it."""
        self._plan_step(project, step)
        if not (record or "").strip():
            raise HarnessError("The defense record is empty.")
        d = self._handoff(project, step)
        draft = d / "defense-draft.md"
        body = record.strip() + "\n"
        if parked:
            body += "\n## Parked questions\n" + "".join(f"- {q}\n" for q in parked)
        if reviewed:
            path = d / f"defense-{_stamp()}.md"
            _write_text(path, body)
            if draft.exists():
                draft.unlink()
            self.index.upsert(f"defense:{project}:{step}:{path.name}", "defense", body,
                              {"project": project, "step": step}, str(path.relative_to(self.root)))
        else:
            path = draft
            _write_text(path, body)
        return {"saved": str(path.relative_to(self.root)), "reviewed": reviewed}

    def post_note(self, project: str, step: str, to: str, from_role: str, text: str) -> dict:
        if to not in ROLES or from_role not in ROLES:
            raise HarnessError(f"Roles must be among {ROLES}.")
        if not (text or "").strip():
            raise HarnessError("The note is empty.")
        self._plan_step(project, step)
        path = self._handoff(project, step) / "notes" / f"{_stamp()}-{_slug(from_role)}-to-{_slug(to)}.yaml"
        _write_yaml(path, {"schema": SCHEMA, "from": from_role, "to": to, "text": text.strip(), "read": False})
        self.index.upsert(f"note:{path.relative_to(self.private)}", "note", text,
                          {"project": project, "step": step}, str(path.relative_to(self.root)))
        return {"saved": str(path.relative_to(self.root))}

    def _open_notes(self, project: str, role: str) -> list[dict]:
        base = self.private / "handoff" / project
        out = []
        for p in sorted(base.glob("*/notes/*.yaml")) if base.exists() else []:
            n = _read_yaml(p, {})
            if n.get("to") == role and not n.get("read"):
                out.append({"step": p.parent.parent.name, "from": n.get("from"), "text": n.get("text"),
                            "file": str(p.relative_to(self.root))})
                n["read"] = True
                _write_yaml(p, n)
        return out

    # ---------------------------------------------------------------- profile
    def propose_profile_change(self, action: str, change: dict | None = None, proposal_id: str | None = None,
                               reason: str = "") -> dict:
        """propose / list / accept / reject. Accepted changes are applied to learner.yaml and logged."""
        self.ensure_workspace()
        pf = self.private / "proposals.yaml"
        data = _read_yaml(pf, {"schema": SCHEMA, "proposals": []})
        props = data.setdefault("proposals", [])
        if action == "propose":
            if not change:
                raise HarnessError("A proposal needs a change, e.g. {'formats_that_fit': ['diagrams']}.")
            choices = {
                "lesson_mode": {"structured", "semi-structured", "free-form"},
                "sociability": {"group", "guided", "solo"},
                "mastery_mode": {"written-practical", "spoken", "both"},
                "depth_mode": {"civic-overview", "foundational", "practitioner", "advanced"},
                "learning_context": {"job-interview", "school", "curiosity-personal-growth",
                                     "professional-growth"},
            }
            for field, allowed in choices.items():
                if field in change and change[field] not in allowed:
                    raise HarnessError(f"{field} must be one of {sorted(allowed)}.")
            if "voice_mode" in change and not isinstance(change["voice_mode"], str):
                raise HarnessError("voice_mode is the learner's own words for how to teach by voice.")
            for field in ("school_level", "target_role", "professional_context"):
                if field in change and not str(change[field]).strip():
                    raise HarnessError(f"{field} cannot be blank when provided.")
            pid = f"p{len(props) + 1}"
            props.append({"id": pid, "change": change, "reason": reason, "status": "pending",
                          "at": _now().isoformat(timespec="seconds")})
            _write_yaml(pf, data)
            return {"proposed": pid}
        if action == "list":
            return {"pending": [p for p in props if p["status"] == "pending"]}
        if action in ("accept", "reject"):
            p = next((p for p in props if p["id"] == proposal_id), None)
            if not p or p["status"] != "pending":
                raise HarnessError(f"No pending proposal {proposal_id!r}.")
            p["status"] = "accepted" if action == "accept" else "rejected"
            if action == "accept":
                lf = self.private / "learner.yaml"
                learner = _read_yaml(lf, {"schema": SCHEMA})
                learner.update(p["change"])
                _write_yaml(lf, learner)
                self.log_session(f"Learner accepted profile proposal {p['id']}: {p['change']}")
            _write_yaml(pf, data)
            return {proposal_id: p["status"]}
        raise HarnessError("action must be propose, list, accept or reject.")

    # ----------------------------------------------------------- log & diary
    def log_session(self, text: str, project: str | None = None) -> dict:
        if not (text or "").strip():
            raise HarnessError("The session note is empty.")
        t = _now()
        path = self.private / "log" / t.strftime("%Y") / t.strftime("%m") / f"{t.strftime('%Y-%m-%d')}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        line = f"- {t.strftime('%H:%M')}{' [' + project + ']' if project else ''} {text.strip()}\n"
        with path.open("a", encoding="utf-8") as f:
            f.write(line)
        self.index.upsert(f"log:{path.name}:{_stamp(t)}", "log", text, {"project": project or ""},
                          str(path.relative_to(self.root)))
        return {"saved": str(path.relative_to(self.root))}

    def add_diary_entry(self, text: str, title: str = "", project: str | None = None) -> dict:
        """Optional. Never required for anything."""
        if not (text or "").strip():
            raise HarnessError("The diary entry is empty.")
        self.ensure_workspace()
        t = _now()
        name = f"{t.strftime('%Y-%m-%d')}-{_slug(title or text[:40])}.md"
        path = self.private / "diary" / t.strftime("%Y") / t.strftime("%m") / name
        n = 2
        while path.exists():
            path = path.with_name(f"{name[:-3]}-{n}.md")
            n += 1
        header = f"---\ndate: {t.isoformat(timespec='minutes')}\nproject: {project or ''}\n---\n\n"
        _write_text(path, header + text.strip() + "\n")
        rel = str(path.relative_to(self.root))
        self.index.upsert(f"diary:{rel}", "diary", text, {"project": project or ""}, rel)
        return {"saved": rel}

    # -------------------------------------------------------------- learnings
    def extract_learnings(self, project: str, record: dict) -> dict:
        """Validates and stores a learning record the archivist wrote. The server extracts nothing itself."""
        plan = self.get_plan(project)
        source = record.get("source", "")
        if not source or not (self.root / source).exists():
            raise HarnessError("A learning needs a source file that exists (a diary entry, note or defense).")
        concepts = {c for s in plan.get("steps", []) for c in s.get("concepts", [])}
        tags = record.get("tags", {}) or {}
        bad = [c for c in tags.get("concept", []) if c not in concepts]
        if bad:
            raise HarnessError(f"Concept tags not in the plan: {bad}. Known: {sorted(concepts)}")
        if not str(record.get("what_happened", "")).strip():
            raise HarnessError("A learning needs what_happened.")
        rid = record.get("id") or f"l-{_stamp()}"
        data = {"schema": SCHEMA, "id": rid, "project": project, "step": record.get("step", ""),
                "concept": record.get("concept", ""), "what_happened": record["what_happened"],
                "format": record.get("format", ""), "tags": tags, "source": source,
                "at": _now().isoformat(timespec="seconds")}
        path = self.private / "learnings" / project / f"{_check_name(rid, 'learning id')}.yaml"
        if path.exists():
            raise HarnessError(f"Learning {rid} already exists; records are written once.")
        _write_yaml(path, data)
        self._index_learning(data, path)
        return {"saved": str(path.relative_to(self.root))}

    # ----------------------------------------------------------------- search
    def _index_learning(self, d: dict, path: Path) -> None:
        concepts = sorted({*(d.get("tags", {}) or {}).get("concept", []), *([d["concept"]] if d.get("concept") else [])})
        meta = {"project": d.get("project", ""), "step": d.get("step", ""), "author": "archivist",
                "concepts": [_slug(c) for c in concepts],
                "tags": sorted({t for k, v in (d.get("tags") or {}).items() if isinstance(v, list) for t in v}),
                "date": str(d.get("at", ""))[:10]}
        self.index.upsert(f"learning:{d.get('project')}:{d.get('id')}", "learning",
                          f"{d.get('concept', '')} {d.get('what_happened', '')}", meta,
                          str(path.relative_to(self.root)), [("about", f"concept:{_slug(c)}") for c in concepts])

    def load_program_graph(self) -> int:
        """Concept prerequisites from the bundled programs: each concept of an idea requires
        the concepts of the ideas it builds on."""
        edges = []
        for track_file in PROGRAMS.glob("*/track.yaml"):
            track = _read_yaml(track_file, {})
            by_idea = {i["id"]: [c["id"] for c in i.get("concepts", [])] for i in track.get("ideas", [])}
            for idea in track.get("ideas", []):
                for c in by_idea[idea["id"]]:
                    edges.append((f"concept:{c}", "part_of", f"idea:{idea['id']}"))
                    for req in idea.get("requires", []):
                        edges += [(f"concept:{c}", "requires", f"concept:{r}") for r in by_idea.get(req, [])]
                for concept, requirements in (idea.get("concept_requires") or {}).items():
                    edges += [(f"concept:{concept}", "requires", f"concept:{required}")
                              for required in requirements]
        self.index.set_concept_edges(edges)
        return len(edges)

    def search_memory(self, query: str, kinds: list[str] | None = None, project: str | None = None,
                      limit: int = 8, filters: dict | None = None, grep: str | None = None,
                      hops: int = 0, scope: str = "domain") -> dict:
        """Hop 1 of two-hop search. filters: area, tags, concepts, type, since (ISO date), step.
        grep: a literal pattern for the original library files, written by the agent from the
        learner's question; decisive only when it matches few files. hops=1 widens through the
        concept graph. Library hits carry the original's path (and section anchors) for hop 2."""
        f = dict(filters or {})
        if scope != "all":
            if scope not in ("meta", "domain", "reflection", "reference"):
                raise HarnessError("scope must be reflection (the learner's own words and learnings), "
                                   "domain, meta, reference or all.")
            f["scope"] = scope
        if project:
            f["project"] = project
        self.resume_semantic()
        extra, k_by = {}, {}
        if grep:
            hits = self.library.grep(grep)
            extra["literal"] = hits
            if len(hits) <= GREP_SELECTIVITY_MAX:
                k_by["literal"] = GREP_RRF_K
        return {"mode": self.index.mode(),
                "results": self.index.search(query, kinds=kinds, filters=f, limit=limit, extra=extra,
                                             k_by_list=k_by, hops=hops)}

    def enable_semantic_search(self, action: str = "on", embedder_factory=None) -> dict:
        """on: set up in the background (install, model download, indexing); off; or status."""
        if action == "status":
            return self.semantic.status()
        if action == "off":
            self.index.disable_semantic()
            self.semantic.state, self.semantic.detail = "off", "Smart search is off; keyword search is on."
            return self.semantic.status()
        if action != "on":
            raise HarnessError("action must be on, off or status.")
        self.ensure_workspace()
        if not self.index.semantic_wanted():
            self.rebuild_index()  # make sure every row carries its text before vectors are built
        return self.semantic.start(embedder_factory)

    def resume_semantic(self) -> None:
        """Lazy: if the learner turned smart search on earlier, start loading it in the background the
        first time a search needs it. Until it's ready, search answers in keyword mode."""
        if getattr(self, "_semantic_resumed", False):
            return
        self._semantic_resumed = True
        if self.index.path.exists() and self.index.semantic_wanted() and extra_installed():
            self.semantic.start()

    def rebuild_index(self) -> dict:
        """Re-derive the whole index from the files."""
        self.index.clear()
        n = 0
        for p in sorted((self.private / "diary").rglob("*.md")):
            body = p.read_text(encoding="utf-8").split("---\n", 2)[-1]
            rel = str(p.relative_to(self.root))
            self.index.upsert(f"diary:{rel}", "diary", body, {}, rel); n += 1
        for p in sorted((self.private / "learnings").rglob("*.yaml")):
            self._index_learning(_read_yaml(p, {}), p); n += 1
        for rec in self.library._records():
            self.library.index_record(rec); n += 1
        self.load_program_graph()
        self.knowledge.reload_standards()
        self.expectations.reindex()
        for doc_id, it in self.knowledge._state()["items"].items():
            if it.get("tier") == "cold":
                self.index.set_tier(doc_id, "cold")
        for p in sorted((self.private / "handoff").rglob("notes/*.yaml")):
            d = _read_yaml(p, {})
            proj = p.relative_to(self.private / "handoff").parts[0]
            self.index.upsert(f"note:{p.relative_to(self.private)}", "note", d.get("text", ""),
                              {"project": proj}, str(p.relative_to(self.root))); n += 1
        for p in sorted((self.private / "handoff").rglob("defense-2*.md")):
            proj, step = p.relative_to(self.private / "handoff").parts[:2]
            self.index.upsert(f"defense:{proj}:{step}:{p.name}", "defense", p.read_text(encoding="utf-8"),
                              {"project": proj, "step": step}, str(p.relative_to(self.root))); n += 1
        for p in sorted((self.private / "log").rglob("*.md")):
            for i, line in enumerate(p.read_text(encoding="utf-8").splitlines()):
                if line.strip():
                    self.index.upsert(f"log:{p.name}:{i}", "log", line, {}, str(p.relative_to(self.root))); n += 1
        for f in sorted((self.private / "reflection" / "annotations").glob("*.yaml")):
            for it in (_read_yaml(f, {}) or {}).get("items", []):
                self.journal._index(it, f); n += 1
        for f in sorted((self.private / "reflection" / "errors").glob("*.yaml")):
            for it in (_read_yaml(f, {}) or {}).get("items", []):
                self.index.upsert(f"error:{it['id']}", "error", f"{it['what']} {it.get('helped', '')}",
                                  {"scope": "reflection", "author": "tutor", "type": it["kind"],
                                   "project": it["project"], "step": it["step"], "date": it["at"][:10]},
                                  str(f.relative_to(self.root))); n += 1
        for p in sorted((self.private / "reflection" / "retros").glob("*.yaml")):
            self.share._index_retro(_read_yaml(p, {}) or {}, p); n += 1
        for p in sorted((self.private / "reports").glob("*.md")):
            body = p.read_text(encoding="utf-8").split("---\n", 2)[-1]
            self.index.upsert(f"report:{p.stem}", "report", body,
                              {"scope": "reflection", "author": "mentor", "date": p.stem[:10]},
                              str(p.relative_to(self.root))); n += 1
        for p in sorted((self.private / "concepts").glob("*.yaml")):
            d = _read_yaml(p, {}) or {}
            if d.get("concept"):
                self.board._index_concept(d, p); n += 1
        for p in sorted((self.private / "checkpoints").glob("*.yaml")):
            c = _read_yaml(p, {}) or {}
            body = " ".join(str(c.get(k, "")) for k in ("label", "thinking", "tried", "open_question", "next_move"))
            self.index.upsert(f"checkpoint:{c.get('id', p.stem)}", "checkpoint", body,
                              {"project": c.get("project", ""), "step": c.get("step", ""),
                               "date": str(c.get("at", ""))[:10]}, str(p.relative_to(self.root))); n += 1
        return {"indexed": n}

    # ------------------------------------------------------------------ links
    @staticmethod
    def check_links(urls: list[str], timeout: float = 10.0) -> dict:
        results = []
        for u in urls:
            if not re.match(r"^https?://", u or ""):
                results.append({"url": u, "ok": False, "detail": "not an http(s) link"})
                continue
            req = urllib.request.Request(u, method="GET", headers={"User-Agent": "education-harness/0.1"})
            try:
                with urllib.request.urlopen(req, timeout=timeout) as r:
                    results.append({"url": u, "ok": 200 <= r.status < 400, "detail": r.status})
            except urllib.error.HTTPError as e:
                results.append({"url": u, "ok": False, "detail": e.code})
            except Exception as e:  # network errors, timeouts
                results.append({"url": u, "ok": False, "detail": type(e).__name__})
        return {"results": results, "dead": [r["url"] for r in results if not r["ok"]]}
