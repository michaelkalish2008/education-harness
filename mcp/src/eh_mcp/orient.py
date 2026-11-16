"""Orientation: where the learner is, where they are heading, and what to say next.

- The arc (``.private/arc.yaml``) is the learner's own trajectory: a goal in their words,
  where the work leads, and an ordered path of projects. It changes whenever they want,
  and every change is kept in its history.
- ``where_am_i`` reads the arc, every project's plan and progress, and the profile, and
  returns what is done, what is current and what comes next, with one suggested move.
- ``MAP.md`` at the workspace root is the same picture as a file, rewritten after every
  change, so a learner coming back from a break can open it without the app.
- ``write_plan`` is how a plan reaches ``program.yaml``: checked, and never losing progress.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from .core import Workspace

DONE = ("drafted", "defended")
NAMED_SOFT_CAP = 12  # past this many of the learner's own bookmarks, saving one suggests tidying

# What the learner can say. Shown on the help card and in MAP.md; the start skill
# answers all of them. Plain phrases, no commands to memorize.
# Profile fields the tutor needs every turn to fit the teaching to the learner.
LEARNER_FIELDS = ("lesson_mode", "sociability", "mastery_mode", "depth_mode", "learning_context",
                  "school_level", "target_role", "professional_context", "interests",
                  "formats_that_fit", "voice_mode", "keep_slips")

PHRASES = [
    ("Let's learn", "start a new learning path"),
    ("Show me how this works", "a short first lesson that teaches the harness by using it"),
    ("Let's go", "pick up where you left off, or start"),
    ("Where am I?", "what's done, what's now, what's next"),
    ("Show my catalog", "browse, prioritize or archive learning paths"),
    ("Show my knowledge map", "explore local semantic connections in 3D"),
    ("Note this", "keep a thought in your words, half-formed is fine"),
    ("Bookmark this", "save where your thinking is right now"),
    ("Look back", "your notes and what you've done, brought back together"),
]
# Everything else is plain language: "show me the answer", "how am I doing?",
# "I want to learn …", "what do I know about the chain rule?", "I'm stopping here".


def _read(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return yaml.safe_load(path.read_text(encoding="utf-8")) or default


def _write(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    tmp.replace(path)



def _as_list(v: Any) -> list:
    """A single string is one item, never a list of its characters."""
    if v is None:
        return []
    if isinstance(v, str):
        return [v] if v.strip() else []
    return list(v)

class Orientation:
    def __init__(self, ws: "Workspace"):
        self.ws = ws

    # ------------------------------------------------------------------ program
    def get_program(self, track: str = "data-scientist") -> dict:
        """The default program's ideas, concepts and order. Carries no solutions or examples."""
        from .core import PROGRAMS, HarnessError
        f = PROGRAMS / track / "track.yaml"
        if not f.exists():
            names = sorted(p.parent.name for p in PROGRAMS.glob("*/track.yaml"))
            raise HarnessError(f"No program {track!r}. Available: {', '.join(names)}.")
        t = _read(f, {})
        return {"track": t.get("track"), "title": t.get("title"),
                "guiding_question": t.get("guiding_question"),
                "sequence_rule": t.get("sequence_rule"),
                "learning_stages": t.get("learning_stages", []),
                "depth_modes": t.get("depth_modes", {}),
                "modules": t.get("modules", []), "anchor_project": t.get("anchor_project", {}),
                "civic_lens": t.get("civic_lens", {}),
                "example_rules": t.get("example_rules"),
                "ideas": [{"id": i["id"], "order": i.get("order"), "idea": i.get("idea"),
                           "module": i.get("module"),
                           "foundation": i.get("foundation"),
                           "concepts": [c["name"] for c in i.get("concepts", [])],
                           "requires": i.get("requires", []), "example_hint": i.get("example_hint"),
                           "standards": i.get("standards", []), "build": i.get("build"),
                           "practice": i.get("practice", {}),
                           "converges_on_transformers": i.get("converges_on_transformers")}
                          for i in t.get("ideas", [])]}

    # --------------------------------------------------------------------- arcs
    # A learner can have several arcs, one per direction (fine-tuning, the math of
    # backpropagation, causal inference). Each lives in .private/arcs/<name>.yaml. A chat
    # thread focuses on one arc; the knowledge base underneath is shared by all of them.
    @property
    def _arcs_dir(self) -> Path:
        d = self.ws.private / "arcs"
        old = self.ws.private / "arc.yaml"
        if old.exists() and not (d.exists() and any(d.glob("*.yaml"))):  # one-arc workspaces
            from .core import _slug
            data = _read(old, {}) or {}
            d.mkdir(parents=True, exist_ok=True)
            name = _slug(data.get("goal", "main"))[:40] or "main"
            data["name"] = name
            _write(d / f"{name}.yaml", data)
            old.replace(d / ".arc.yaml.migrated")
        return d

    def _arcs(self) -> dict[str, dict]:
        d = self._arcs_dir
        return {f.stem: (_read(f, {}) or {}) for f in sorted(d.glob("*.yaml"))} if d.exists() else {}

    def _arcs_in(self, space: str = "") -> dict[str, dict]:
        """Arcs visible in a space (a Claude project). Arcs not yet given a space show everywhere."""
        arcs = self._arcs()
        if not space:
            return arcs
        from .core import _slug
        return {k: v for k, v in arcs.items() if not v.get("space") or _slug(v["space"]) == _slug(space)}

    def _resolve_arc(self, name: str, space: str = "") -> str | None:
        """An arc by name or by words from its name or goal; None when there are none."""
        from .core import HarnessError, _slug
        arcs = self._arcs_in(space)
        if not arcs:
            return None
        if not name:
            if len(arcs) == 1:
                return next(iter(arcs))
            raise HarnessError("Which arc? " + "; ".join(f"{k}: {v.get('goal', '')}" for k, v in arcs.items()))
        if _slug(name) in arcs:
            return _slug(name)
        words = name.lower().split()
        hits = [k for k, v in arcs.items() if all(w in f"{k} {v.get('goal', '')}".lower().replace("-", " ")
                                                  for w in words)]
        if len(hits) == 1:
            return hits[0]
        raise HarnessError(f"No single arc matches {name!r}. Arcs: " + ", ".join(arcs))

    def list_arcs(self, space: str = "") -> dict:
        from .lenses import lens_for
        return {"arcs": [{"name": k, "goal": v.get("goal"), "why": v.get("why"), "space": v.get("space", ""),
                          "lens": lens_for(v), "path": [i["title"] for i in v.get("path", [])]}
                         for k, v in self._arcs_in(space).items()]}

    def get_arc(self, name: str = "", space: str = "") -> dict:
        from .lenses import LENSES, lens_for
        arcs = self._arcs_in(space)
        if not arcs:
            return {"arc": None, "note": "No arc yet. Ask what the learner wants to be able to do."}
        if not name and len(arcs) > 1:
            return {"arc": None, **self.list_arcs(space), "note": "Several arcs; name one."}
        key = self._resolve_arc(name, space)
        arc = dict(arcs[key])
        arc["name"] = key
        arc["lens"] = lens_for(arc)
        arc["lens_detail"] = LENSES[arc["lens"]]
        arc["history"] = arc.get("history", [])[-5:]
        return {"arc": arc}

    def set_arc_space(self, name: str, space: str = "", lens: str = "", cadence: str = "") -> dict:
        """Put an existing arc in a space (the Claude project its chats live in) and/or set its lens."""
        from .core import HarnessError
        from .lenses import LENSES
        key = self._resolve_arc(name)
        if key is None:
            raise HarnessError("No arcs yet.")
        if lens and lens not in LENSES:
            raise HarnessError(f"lens must be one of {sorted(LENSES)}.")
        f = self._arcs_dir / f"{key}.yaml"
        arc = _read(f, {}) or {}
        if space:
            arc["space"] = space.strip()
        if lens:
            arc["lens"] = lens
        if cadence:
            arc["cadence"] = cadence.strip()
        _write(f, arc)
        return {"arc": key, "space": arc.get("space", ""), "lens": arc.get("lens", ""),
                "cadence": arc.get("cadence", "")}

    def set_arc(self, goal: str, path: list[dict] | None = None, why: str = "", change: str = "", name: str = "",
                space: str = "", lens: str = "", cadence: str = "") -> dict:
        """Save an arc the learner agreed to. name: a short handle for the direction
        ('causal-inference'); a new name starts a new arc beside the others. path: ordered items
        {title, idea?, project?, note?}; idea is 'track:idea-id', project a project folder.
        space: the Claude project this arc's chats live in. lens: math, philosophy or general."""
        from .core import HarnessError, _now, _slug
        from .lenses import LENSES
        if lens and lens not in LENSES:
            raise HarnessError(f"lens must be one of {sorted(LENSES)}.")
        if not (goal or "").strip() and name:
            existing = self._resolve_arc(name)
            if existing:
                goal = self._arcs()[existing].get("goal", "")
                name = existing
        if not (goal or "").strip():
            raise HarnessError("An arc needs a goal in the learner's own words.")
        path = path or [{"title": goal.strip()}]
        clean = []
        for i, item in enumerate(path, 1):
            title = str(item.get("title", "")).strip()
            if not title:
                raise HarnessError(f"Path item {i} needs a title.")
            entry: dict[str, Any] = {"title": title}
            if item.get("idea"):
                track, _, idea = str(item["idea"]).partition(":")
                ids = {x["id"] for x in self.get_program(track or "data-scientist")["ideas"]}
                if idea not in ids:
                    raise HarnessError(f"{item['idea']!r} is not an idea in the {track} program.")
                entry["idea"] = f"{track}:{idea}"
            if item.get("project"):
                entry["project"] = str(item["project"])
            if item.get("note"):
                entry["note"] = str(item["note"])
            clean.append(entry)
        arcs = self._arcs_in(space)
        if name:
            key = _slug(name)[:40]
        elif len(arcs) == 1:
            key = next(iter(arcs))
        elif not arcs:
            key = _slug(goal)[:40]
        else:
            raise HarnessError("Several arcs exist: pass name, an existing one to change it or a new one to add.")
        old = self._arcs().get(key, {})
        history = old.get("history", [])
        history.append({"at": _now().isoformat(timespec="seconds"),
                        "change": change.strip() or ("Arc set." if not old else "Arc changed.")})
        arc = {"schema": 1, "name": key, "goal": goal.strip(), "why": (why or "").strip(), "path": clean,
               "space": (space or old.get("space", "")).strip(), "lens": lens or old.get("lens", ""),
               "cadence": (cadence or old.get("cadence", "")).strip(),
               "history": history}
        if not arc["lens"]:
            arc.pop("lens")
        if not arc["space"]:
            arc.pop("space")
        if not arc["cadence"]:
            arc.pop("cadence")
        _write(self._arcs_dir / f"{key}.yaml", arc)
        self.ws.log_session(f"Arc {key} {'set' if not old else 'changed'}: {goal.strip()}")
        return {"saved": f".private/arcs/{key}.yaml", "name": key, "path": [c["title"] for c in clean],
                "arcs": len(self._arcs())}

    # --------------------------------------------------------------------- plan
    def write_plan(self, project: str, question: str, steps: list[dict], example: str = "",
                   interests_used: list[str] | None = None, idea: str = "",
                   constellation: dict | None = None, sources: list[dict] | None = None) -> dict:
        """Lesson planner. Writes program.yaml after checking every step, and keeps progress:
        a step with work on it is never dropped (it is kept, marked retired)."""
        from .core import HarnessError, SCHEMA, _check_name, _read_yaml, _write_yaml
        d = self.ws.project_dir(project)
        if not d.exists():
            self.ws.init_project(project, question)
        seen: set[str] = set()
        clean = []
        for i, s in enumerate(steps or [], 1):
            sid = _check_name(str(s.get("id") or f"s{i}"), "step")
            if sid in seen:
                raise HarnessError(f"Two steps are named {sid}.")
            for key in ("does", "concepts", "strong_version_shows"):
                if not s.get(key):
                    raise HarnessError(f"Step {sid} needs '{key}'.")
            bad = [r for r in _as_list(s.get("requires", [])) if r not in seen]
            if bad:
                raise HarnessError(f"Step {sid} requires {bad}, which must come earlier in the plan.")
            seen.add(sid)
            clean.append({"id": sid, "does": s["does"], "concepts": _as_list(s["concepts"]),
                          **({"standards_cited": list(s["standards_cited"])} if s.get("standards_cited") else {}),
                          "format": s.get("format", "solve-it"),
                          "strong_version_shows": _as_list(s["strong_version_shows"]),
                          "requires": _as_list(s.get("requires", [])),
                          **({"terms": {str(k): str(v) for k, v in dict(s["terms"]).items()}}
                             if s.get("terms") else {})})
        if not clean:
            raise HarnessError("A plan needs at least one step.")
        from .neutrality import check_all
        issues = check_all("question", [question]) + [
            i for s in clean for i in check_all(f"step {s['id']}", [s["does"], *s["strong_version_shows"]])]
        if issues:
            raise HarnessError("Neutral point of view (principle 19): " + " | ".join(issues))
        old = _read_yaml(d / "program.yaml", {}) or {}
        plan: dict[str, Any] = {"schema": SCHEMA}
        if idea:
            track, _, idea_id = idea.partition(":")
            plan["track"], plan["idea"] = track, idea_id
        plan["project"] = {"question": question or old.get("project", {}).get("question", ""),
                           **({"example": example} if example else {}),
                           **({"interests_used": list(interests_used)} if interests_used else {}),
                           **({"sources": [{k: str(s[k]).strip()
                                            for k in ("kind", "url", "title", "library_id", "accessed_on")
                                            if s.get(k)}
                                           for s in sources if s.get("url") or s.get("library_id") or s.get("title")]}
                              if sources else {})}
        plan["steps"] = clean
        plan["constellation"] = constellation or old.get("constellation", {})
        _write_yaml(d / "program.yaml", plan)
        prog = _read_yaml(d / "progress.yaml", {"schema": SCHEMA, "steps": {}}) or {}
        prog.setdefault("steps", {})
        retired = []
        for sid, st in prog["steps"].items():
            if sid not in seen:
                worked = st.get("attempts") or st.get("seen") or st.get("status") not in (None, "not started")
                if worked:
                    st["retired"] = True
                    retired.append(sid)
        prog["steps"] = {k: v for k, v in prog["steps"].items() if k in seen or v.get("retired")}
        for s in clean:
            prog["steps"].setdefault(s["id"], {"status": "not started", "seen": []}).pop("retired", None)
        _write_yaml(d / "progress.yaml", prog)
        self.ws.load_program_graph()
        return {"saved": f"projects/{project}/program.yaml", "steps": [s["id"] for s in clean],
                "kept_as_retired": retired, "standards": self.ws.alignment.align_plan(project, clean)}

    def _plan_brief(self, project: str) -> dict:
        from .core import _read_yaml
        d = self.ws.project_dir(project)
        plan = _read_yaml(d / "program.yaml", {}) or {}
        prog = (_read_yaml(d / "progress.yaml", {}) or {}).get("steps", {})
        return {"question": plan.get("project", {}).get("question", ""),
                "example": plan.get("project", {}).get("example", ""),
                "steps": [{"id": x["id"], "does": x["does"], "concepts": x.get("concepts", []),
                           "format": x.get("format", ""), "strong_version_shows": x.get("strong_version_shows", []),
                           "terms": x.get("terms", {}),
                           "status": prog.get(x["id"], {}).get("status", "not started"),
                           "seen": prog.get(x["id"], {}).get("seen", []),
                           "follow_on_owed": prog.get(x["id"], {}).get("follow_on_owed", False)}
                          for x in plan.get("steps", [])],
                "audience": (_read(self.ws.share._dir(project) / "audience.yaml", {}) or {}).get("audience", "")}

    # --------------------------------------------------------------- commitment
    def set_commitment(self, project: str, cadence: str, deadline: str = "", showcase: str = "",
                       fallback: str = "") -> dict:
        """The learner's own commitment for a project. cadence is theirs: weekly, irregular,
        'only when I ask' or anything they say. Deadline, showcase date and fallback are optional."""
        from .core import HarnessError, _write_text
        d = self.ws._require_project(project)
        if not (cadence or "").strip():
            raise HarnessError("Ask the learner how often they want to check in; 'only when I ask' is fine.")
        lines = ["# Commitment", "", f"Cadence: {cadence.strip()}"]
        lines += [f"Deadline: {deadline}"] if deadline else []
        lines += [f"Showcase: {showcase}"] if showcase else []
        lines += [f"If plans slip: {fallback}"] if fallback else []
        _write_text(d / "commitment.md", "\n".join(lines) + "\n")
        return {"saved": f"projects/{project}/commitment.md"}

    # -------------------------------------------------------------- checkpoints
    @property
    def _cp_dir(self) -> Path:
        return self.ws.private / "checkpoints"

    def save_checkpoint(self, label: str, thinking: str, next_move: str, project: str = "",
                        step: str = "", open_question: str = "", tried: str = "", auto: bool = False) -> dict:
        """A bookmark of the learner's place: where their thinking was (in their words where
        possible), what they tried, the open question and the next move. Saved when the learner
        asks ("bookmark this") and automatically when a session ends."""
        from .core import HarnessError, _now, _slug, _stamp
        if not (thinking or "").strip() or not (next_move or "").strip():
            raise HarnessError("A checkpoint needs where the thinking is and the next move.")
        if project:
            self.ws._require_project(project)
            if step:
                self.ws._plan_step(project, step)
        t = _now()
        label = (label or "").strip() or (f"{project} {step}".strip() or "checkpoint")
        cid = f"{_stamp(t)}-{_slug(label)}"
        data = {"schema": 1, "id": cid, "label": label, "at": t.isoformat(timespec="minutes"),
                "auto": bool(auto), "project": project, "step": step, "thinking": thinking.strip(),
                "tried": (tried or "").strip(), "open_question": (open_question or "").strip(),
                "next_move": next_move.strip()}
        replaced = []
        if auto:  # one "where you stopped" per project: the newest replaces the last
            for f in self._cp_dir.glob("*.yaml") if self._cp_dir.exists() else []:
                old = _read(f, {}) or {}
                if old.get("auto") and old.get("project", "") == project:
                    self._delete(f)
                    replaced.append(old.get("label"))
        path = self._cp_dir / f"{cid}.yaml"
        _write(path, data)
        body = " ".join(x for x in (label, thinking, tried, open_question, next_move) if x)
        self.ws.index.upsert(f"checkpoint:{cid}", "checkpoint", body,
                             {"project": project, "step": step, "date": t.date().isoformat(), "scope": "meta"},
                             str(path.relative_to(self.ws.root)))
        out: dict[str, Any] = {"saved": str(path.relative_to(self.ws.root)), "id": cid, "label": label}
        if replaced:
            out["replaced"] = replaced
        named = [c for c in self.list_checkpoints(limit=1000)["checkpoints"] if not c["auto"]]
        if not auto and len(named) > NAMED_SOFT_CAP:
            out["consider_tidying"] = {
                "named_bookmarks": len(named),
                "resolved": [c["label"] for c in named if c["resolved"]],
                "oldest": [c["label"] for c in named[-3:]],
                "say": "Offer once, lightly, to remove resolved or old bookmarks. Never refuse to save."}
        return out

    def list_checkpoints(self, project: str = "", limit: int = 10, resolved: bool | None = None) -> dict:
        """Bookmarks, newest first. 'auto' marks the one-per-project "where you stopped";
        'resolved' marks a bookmark whose step is now drafted or defended."""
        from .core import _read_yaml
        files = sorted(self._cp_dir.glob("*.yaml"), reverse=True) if self._cp_dir.exists() else []
        status: dict[str, dict] = {}
        out = []
        for f in files:
            c = _read(f, {}) or {}
            if project and c.get("project") != project:
                continue
            done = False
            if c.get("project") and c.get("step"):
                if c["project"] not in status:
                    pf = self.ws.root / "projects" / c["project"] / "progress.yaml"
                    status[c["project"]] = (_read_yaml(pf, {}) or {}).get("steps", {})
                done = status[c["project"]].get(c["step"], {}).get("status") in DONE
            if resolved is not None and done != resolved:
                continue
            where = " / ".join(x for x in (c.get("project"), c.get("step")) if x) or "general"
            out.append({"id": c.get("id"), "label": c.get("label"),
                        "when": str(c.get("at", ""))[:16].replace("T", " "),
                        "where": f"{where}: {c.get('next_move', '')}",
                        "auto": c.get("auto", False), "resolved": done})
            if len(out) >= limit:
                break
        return {"checkpoints": out}

    def _find(self, checkpoint: str) -> Path:
        from .core import HarnessError
        files = sorted(self._cp_dir.glob("*.yaml"), reverse=True) if self._cp_dir.exists() else []
        want = (checkpoint or "").lower().strip()
        hit = next((f for f in files if f.stem == want), None)
        if not hit and want:
            words = want.split()
            for f in files:
                c = _read(f, {}) or {}
                hay = " ".join(str(c.get(k, "")) for k in ("label", "project", "step", "thinking")).lower()
                if all(w in hay for w in words):
                    hit = f
                    break
        if not hit:
            if not files:
                raise HarnessError("No bookmarks yet. Say 'bookmark this' to save one.")
            raise HarnessError("No bookmark matches that. Recent ones: " +
                               "; ".join(c["label"] for c in self.list_checkpoints(limit=5)["checkpoints"]))
        return hit

    def _delete(self, f: Path) -> None:
        c = _read(f, {}) or {}
        self.ws.index.remove(f"checkpoint:{c.get('id', f.stem)}")
        f.unlink()

    def update_checkpoint(self, checkpoint: str, label: str = "", thinking: str = "", next_move: str = "",
                          open_question: str = "", tried: str = "", step: str = "") -> dict:
        """Refresh a bookmark to where the learner is now; only the fields given change.
        An automatic bookmark the learner refreshes becomes one of theirs."""
        from .core import _now
        f = self._find(checkpoint)
        c = _read(f, {}) or {}
        if step:
            if c.get("project"):
                self.ws._plan_step(c["project"], step)
            c["step"] = step
        for k, v in (("label", label), ("thinking", thinking), ("next_move", next_move),
                     ("open_question", open_question), ("tried", tried)):
            if v.strip():
                c[k] = v.strip()
        c["auto"] = False
        c["updated"] = _now().isoformat(timespec="minutes")
        _write(f, c)
        body = " ".join(str(c.get(k, "")) for k in ("label", "thinking", "tried", "open_question", "next_move"))
        self.ws.index.upsert(f"checkpoint:{c['id']}", "checkpoint", body,
                             {"project": c.get("project", ""), "step": c.get("step", ""),
                              "date": str(c.get("at", ""))[:10], "scope": "meta"},
                             str(f.relative_to(self.ws.root)))
        return {"updated": c["label"], "id": c["id"]}

    def remove_checkpoints(self, checkpoints: list[str] | None = None, resolved: bool = False,
                           learner_confirmed: bool = False) -> dict:
        """Remove bookmarks by id or words, or every resolved one. Without learner_confirmed it
        only lists what would go, so the learner can say yes."""
        from .core import HarnessError
        targets: list[Path] = [self._find(x) for x in (checkpoints or [])]
        if resolved:
            ids = {c["id"] for c in self.list_checkpoints(limit=10000, resolved=True)["checkpoints"]}
            targets += [f for f in self._cp_dir.glob("*.yaml") if (_read(f, {}) or {}).get("id") in ids]
        targets = list(dict.fromkeys(targets))
        if not targets:
            raise HarnessError("Nothing to remove: name a bookmark, or ask for the resolved ones.")
        labels = [(_read(f, {}) or {}).get("label") for f in targets]
        if not learner_confirmed:
            return {"would_remove": labels, "note": "Ask the learner; call again with learner_confirmed=true."}
        for f in targets:
            self._delete(f)
        self.ws.log_session(f"Learner removed bookmarks: {', '.join(map(str, labels))}")
        return {"removed": labels}

    def open_checkpoint(self, checkpoint: str) -> dict:
        """Reopen a bookmark by id, or by words from its label (the latest match). Returns the
        checkpoint and the step as it stands now, so the tutor can resume from it."""
        from .core import _read_yaml
        hit = self._find(checkpoint)
        c = _read(hit, {}) or {}
        out: dict[str, Any] = {"checkpoint": c}
        if c.get("project") and c.get("step"):
            prog = (_read_yaml(self.ws.project_dir(c["project"]) / "progress.yaml", {}) or {}).get("steps", {})
            out["step_now"] = prog.get(c["step"], {"status": "not started"})
            att = self.ws.private / "attempts" / c["project"] / c["step"]
            out["recent_attempts"] = [str(p.relative_to(self.ws.root)) for p in
                                      sorted(att.glob("*.md"), reverse=True)[:3]] if att.exists() else []
        return out

    # ------------------------------------------------------------------- status
    def _projects(self) -> list[dict]:
        from .core import _read_yaml
        out = []
        base = self.ws.root / "projects"
        for d in sorted(base.iterdir()) if base.exists() else []:
            if not (d / "program.yaml").exists():
                continue
            plan = _read_yaml(d / "program.yaml", {}) or {}
            prog = (_read_yaml(d / "progress.yaml", {}) or {}).get("steps", {})
            steps = plan.get("steps", [])
            done = [s for s in steps if prog.get(s["id"], {}).get("status") in DONE]
            todo = [s for s in steps if prog.get(s["id"], {}).get("status") not in DONE]
            touched = max((p.stat().st_mtime for p in (d / "progress.yaml", d / "program.yaml") if p.exists()),
                          default=0)
            out.append({
                "project": d.name,
                "question": plan.get("project", {}).get("question", ""),
                "idea": f"{plan['track']}:{plan['idea']}" if plan.get("track") else "",
                "steps": len(steps),
                "done": [{"step": s["id"], "does": s["does"],
                          "status": prog[s["id"]]["status"]} for s in done],
                "now": _brief(todo[0], prog) if todo else None,
                "next": _brief(todo[1], prog) if len(todo) > 1 else None,
                "_touched": touched,
            })
        return out

    def where_am_i(self, focus: str = "", space: str = "") -> dict:
        """The learner's picture: setup, their arcs, the focused arc's done / now / next, and one
        move. focus: an arc or project this chat is about; space: the Claude project the chat is in.
        Pass both on every call in that chat."""
        from .core import HarnessError, _read_yaml
        from .lenses import LENSES, lens_for
        learner = _read_yaml(self.ws.private / "learner.yaml", {}) or {}
        all_arcs = self._arcs()
        arcs = self._arcs_in(space)
        projects = self._projects()
        by_name = {p["project"]: p for p in projects}

        def arc_view(key: str, arc: dict) -> dict:
            path = []
            for item in arc.get("path", []):
                p = by_name.get(item.get("project", ""))
                state = ("done" if p and p["steps"] and not p["now"] else
                         "in progress" if p and p["done"] else
                         "planned" if p and p["steps"] else "not started")
                path.append({**item, "state": state})
            mine = [by_name[i["project"]] for i in arc.get("path", []) if i.get("project") in by_name]
            open_ = [p for p in mine if p["now"]]
            cur = max(open_, key=lambda p: p["_touched"]) if open_ else None
            lens = lens_for(arc)
            return {"name": key, "goal": arc.get("goal"), "why": arc.get("why"), "path": path,
                    "space": arc.get("space", ""), "lens": lens, "lens_detail": LENSES[lens],
                    "_current": cur, "_touched": max((p["_touched"] for p in mine), default=0)}

        all_views = {k: arc_view(k, v) for k, v in all_arcs.items()}
        views = {k: all_views[k] for k in arcs}
        in_an_arc = {i.get("project") for v in all_arcs.values() for i in v.get("path", [])}
        focus_arc, current = None, None
        if focus:
            if focus in by_name:
                current = by_name[focus]
                focus_arc = next((k for k, v in arcs.items()
                                  if any(i.get("project") == focus for i in v.get("path", []))), None)
            else:
                # On a first visit, hosts often pass the learning project's title as focus.
                # It is useful context for calibration and standards lookup, not an arc name.
                focus_arc = self._resolve_arc(focus, space) if arcs else None
                current = views[focus_arc]["_current"] if focus_arc else None
        elif len(views) == 1:
            focus_arc = next(iter(views))
            current = views[focus_arc]["_current"]
        elif not views:
            open_ = [p for p in projects if p["now"]]
            current = max(open_, key=lambda p: p["_touched"]) if open_ else None
        notes = sum(_unread_notes(self.ws, p["project"], "tutor") for p in projects)
        pending = len([x for x in (_read_yaml(self.ws.private / "proposals.yaml", {}) or {}).get("proposals", [])
                       if x.get("status") == "pending"])
        setup = {"interests": bool(learner.get("interests")),
                 "lesson_mode": bool(learner.get("lesson_mode")),
                 "sociability": bool(learner.get("sociability")),
                 "mastery_mode": bool(learner.get("mastery_mode")),
                 "depth_mode": bool(learner.get("depth_mode")),
                 "learning_context": bool(learner.get("learning_context")), "arc": bool(arcs),
                 "cadence": bool((focus_arc and arcs.get(focus_arc, {}).get("cadence")) or
                                 (current and _cadence(self.ws.project_dir(current["project"]))))}
        ask_later = [k for k, v in (("lesson_mode", setup["lesson_mode"]),
                                     ("sociability", setup["sociability"]),
                                     ("mastery_mode", setup["mastery_mode"]),
                                     ("depth_mode", setup["depth_mode"]),
                                     ("learning_context", setup["learning_context"]),
                                     ("interests", setup["interests"])) if not v]
        context = learner.get("learning_context")
        if context == "school" and not learner.get("school_level"):
            ask_later.append("school_level")
        elif context == "job-interview" and not learner.get("target_role"):
            ask_later.append("target_role")
        elif context == "professional-growth" and not learner.get("professional_context"):
            ask_later.append("professional_context")
        if current and not (self.ws.share._dir(current["project"]) / "audience.yaml").exists():
            ask_later.append("audience")
        if (current or projects) and not arcs:
            ask_later.append("goal")
        fv = views.get(focus_arc) if focus_arc else None
        if len(views) > 1 and not focus:
            recent = max(views.values(), key=lambda v: v["_touched"])
            move = {"move": "choose", "say": f"Let's go on {recent['name']}",
                    "why": "you have several arcs; say which one this chat is for (each gets its own chat)"}
        elif not all_arcs and not projects and self.ws.tour.offer():
            move = {"move": "welcome", "say": "Let's learn",
                    "why": "new here: pick a topic, answer one quick question, and start a first small "
                           "lesson; 'show me how this works' gives the guided tour instead"}
        else:
            move = _suggest(setup, fv["path"] if fv else [], current)
        retro = self.ws.share.retro_due()
        if move["move"] in ("plan", "zoom-out") and retro:
            move = {"move": "retro", "say": "Let's look back on this project",
                    "why": f"{retro[0]} is finished; a short retrospective, then your report"}

        def strip(p: dict | None) -> dict | None:
            return {k: v for k, v in p.items() if not k.startswith("_")} if p else None
        def now_of(v: dict) -> str | None:
            c = v["_current"]
            return c["now"]["does"] if c and c["now"] else None
        standards_query = " ".join(dict.fromkeys(x.strip() for x in (focus, space) if x.strip()))
        out = {"setup": setup, "focus": focus_arc or ((current or {}).get("project") if current else
                                                        (focus or None)),
               "welcome": {"name": "Education Harness",
                           "summary": "Learn something with a path that remembers your place and your own words.",
                           "starters": ["Let's learn", "Teach me <topic>", "Show me the data-science path",
                                        "Let's go", "Where am I?", "Show me how this works"]},
               "arc": {k: v for k, v in fv.items() if not k.startswith("_")} if fv else None,
               "arcs": [{"name": v["name"], "goal": v["goal"], "now": now_of(v),
                         "project": (v["_current"] or {}).get("project")} for v in views.values()],
               "current": strip(current),
               "plan": self._plan_brief(current["project"]) if current else None,
               "program": None if arcs or projects else
               [{"id": i["id"], "idea": i["idea"]} for i in self.get_program()["ideas"]],
               "ask_later": ask_later,
               "onboarding_choices": {
                   "lesson_mode": {
                       "structured": "an end-to-end lesson plan",
                       "semi-structured": "short segments adjusted from the learner's direction",
                       "free-form": "follow the learner's current question",
                   },
                   "sociability": {
                       "group": "work with a group of learners",
                       "guided": "work with a tutor, teacher or parent",
                       "solo": "work individually",
                   },
                   "mastery_mode": {
                       "written-practical": "show understanding through writing and doing",
                       "spoken": "show understanding through speaking and oral explanation",
                       "both": "use written/practical work and spoken explanation",
                   },
                   "depth_mode": {
                       "civic-overview": "plain-language technological literacy with no calculus or code required",
                       "foundational": "core mathematics with small examples and optional code",
                       "practitioner": "math, from-scratch code, package code and parity checks",
                       "advanced": "full implementation plus derivations, failure modes and extensions",
                   },
                   "learning_context": {
                       "job-interview": "prepare for a particular role's interview",
                       "school": "support school study at a named level",
                       "curiosity-personal-growth": "learn from curiosity or for personal growth",
                       "professional-growth": "build capability for current work responsibilities",
                   },
               },
               "standards": self.ws.knowledge.relevant_standards(standards_query),
               "latest_report": (self.ws.reports.list_reports()["reports"] or [None])[0],
               "other_projects": [{"project": p["project"], "question": p["question"],
                                   "done": len(p["done"]), "steps": p["steps"]}
                                  for p in projects if p is not current and p["project"] not in in_an_arc],
               "checkpoints": self.list_checkpoints(project=(current or {}).get("project", ""), limit=3,
                                                    resolved=False)["checkpoints"],
               "open_questions": self.ws.journal.open_questions(project=(current or {}).get("project", ""), limit=3),
               "waiting": {"notes_for_tutor": notes, "proposals": pending,
                           "retrospective_due": retro},
               "learner": {k: learner[k] for k in LEARNER_FIELDS if learner.get(k) not in (None, "", [])},
               "suggested": move,
               "tour": self.ws.tour.summary(),
               "phrases": [{"say": s_, "does": d} for s_, d in PHRASES],
               "map": "MAP.md"}
        out["space"] = space
        out["unplaced_arcs"] = [k for k, v in all_arcs.items() if not v.get("space")] if space else []
        self.write_map(all_views, by_name, move)
        try:  # journey pages (views/, goals/<goal>/) and catalog; never breaks orientation
            self.ws.journey.write(move)
            self.ws.catalog.write()
        except Exception:
            pass
        return out

    # ---------------------------------------------------------------------- map
    def write_map(self, views: dict, by_name: dict, move: dict) -> str:
        """MAP.md at the workspace root: every arc, its path and where it stands, for coming back."""
        from .core import _now
        lines = ["# Where you are", "",
                 f"_Updated {_now().strftime('%a %b %-d, %Y, %-I:%M %p')}. "
                 "This file rewrites itself; open it any time._", ""]
        if len(views) > 1:
            lines += ["Each arc has its own chat. To pick one up, start a chat in your learning project "
                      "and say **\"Let's go on <arc>\"**.", ""]
        spaces: dict[str, list] = {}
        for v in views.values():
            spaces.setdefault(v.get("space") or "", []).append(v)
        ordered = []
        for sp in sorted(spaces, key=lambda x: (x == "", x.lower())):
            for v in sorted(spaces[sp], key=lambda x: -x["_touched"]):
                ordered.append((sp, v))
        last_space = None
        for sp, v in ordered:
            if len(spaces) > 1 and sp != last_space:
                lines += [f"# {sp or 'Not yet in a Claude project'}", ""]
                last_space = sp
            lines += [f"## {v['name']}: {v['goal']}", ""]
            if v.get("why"):
                lines += [f"_Why: {v['why']}_", ""]
            for i, item in enumerate(v["path"], 1):
                mark = {"done": "[x]", "in progress": "[~]"}.get(item["state"], "[ ]")
                lines.append(f"{i}. {mark} {item['title']} ({item['state']})")
            c = v["_current"]
            if c:
                lines += ["", f"**Now:** {c['now']['does']}" if c["now"] else ""]
                if c["next"]:
                    lines += [f"**After that:** {c['next']['does']}"]
            lines.append("")
        loose = [p for n, p in by_name.items() if not any(n == i.get("project") for v in views.values()
                                                         for i in v["path"])]
        if loose:
            lines += ["## Other projects", ""] + [f"- {p['question'] or p['project']}" for p in loose] + [""]
        cps = self.list_checkpoints(limit=5, resolved=False)["checkpoints"]
        if cps:
            lines += ["## Bookmarks", ""] + [f"- **{k['label']}** ({k['when']}): {k['where']}" for k in cps] + [""]
        lines += ["## Next move", "", f"Say **\"{move['say']}\"**: {move['why']}", "", "## What you can say", ""]
        lines += [f"- **{s_}**: {d}" for s_, d in PHRASES]
        lines += ["", "Nothing here is a grade. You can change the plan, the pace or the direction "
                      "whenever you like."]
        text = "\n".join(lines) + "\n"
        path = self.ws.root / "MAP.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return text

    def refresh_map(self) -> None:
        """Best effort after any change; never breaks the tool that called it."""
        try:
            self.where_am_i()
        except Exception:
            pass


def _brief(step: dict, prog: dict) -> dict:
    st = prog.get(step["id"], {})
    return {"step": step["id"], "does": step["does"], "status": st.get("status", "not started"),
            "seen": st.get("seen", []), "attempts": st.get("attempts", 0)}


def _cadence(d: Path) -> str:
    f = d / "commitment.md"
    if not f.exists():
        return ""
    text = f.read_text(encoding="utf-8")
    return "" if "not set yet" in text else text


def _suggest(setup: dict, path: list[dict], current: dict | None) -> dict:
    """One next move. Setup never gates learning: missing pieces are asked along the way."""
    if current and current["now"]:
        return {"move": "continue", "say": "Let's go",
                "why": f"pick up where you left off: {current['now']['does']}"}
    unplanned = next((p for p in path if p["state"] == "not started"), None)
    if unplanned:
        return {"move": "plan", "say": "Let's go",
                "why": f"start the next part of your goal: {unplanned['title']}"}
    if not setup["arc"] and not current:
        return {"move": "begin", "say": "Let's learn",
                "why": "say what you want to be able to do (or start with the first idea of the data-science "
                       "path); we start right away"}
    if current and not current["now"]:
        return {"move": "zoom-out", "say": "Let's zoom out",
                "why": "this project is done; look back on it and choose what's next"}
    return {"move": "begin", "say": "Let's learn", "why": "say what you want to learn next"}


def _unread_notes(ws: "Workspace", project: str, role: str) -> int:
    base = ws.private / "handoff" / project
    n = 0
    for p in base.glob("*/notes/*.yaml") if base.exists() else []:
        d = _read(p, {}) or {}
        n += d.get("to") == role and not d.get("read")
    return n
