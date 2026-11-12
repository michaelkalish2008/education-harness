"""Share-out and retrospectives: where the work meets other people, and looking back on it.

- Every project names an audience at the start ("who would you show this to?"): one
  person, a group, or the public. Preparing to teach helps learning; actually teaching
  helps it last. The audience lives in ``.private/share/<project>/audience.yaml``.
- The share-out is the project's last step (format ``share-out``): a five-minute
  walkthrough, a post, a one-page explainer or a show-and-tell. Drafts are built from the
  learner's own words and kept as versions; the harness never posts anything.
- ``mark_shared`` records that it happened, closes the share-out step and adds the moment to
  the learner's shared moments. ``heard_back`` keeps how it landed: reactions and questions.
- A retrospective is the learner's own look back on a project or a period, in their words.
  It feeds the retrospective report.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from .core import Workspace

AUDIENCE_KINDS = ("person", "group", "public")
FORMATS = ("walkthrough", "post", "explainer", "show-and-tell")
RETRO_QUESTIONS = ("went_well", "was_hard", "surprised", "differently", "how_i_learn", "sharing", "next")


def _read(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return yaml.safe_load(path.read_text(encoding="utf-8")) or default


def _write(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    tmp.replace(path)


class Share:
    def __init__(self, ws: "Workspace"):
        self.ws = ws

    def _dir(self, project: str) -> Path:
        from .core import _check_name
        return self.ws.private / "share" / _check_name(project, "project")

    # ------------------------------------------------------------------ audience
    def set_audience(self, project: str, audience: str, kind: str = "person", format: str = "walkthrough",
                     where: str = "") -> dict:
        """Who the learner would show this project to, as they put it ('my team', 'my sister',
        'LinkedIn'), never a name; the kind of audience; the share-out format; where, for a post."""
        from .core import HarnessError, _now
        self.ws._require_project(project)
        if not (audience or "").strip():
            raise HarnessError("Ask who they'd show it to: one person, a group, or a public post.")
        if kind not in AUDIENCE_KINDS:
            raise HarnessError(f"kind must be one of {AUDIENCE_KINDS}.")
        if format not in FORMATS:
            raise HarnessError(f"format must be one of {FORMATS}.")
        f = self._dir(project) / "audience.yaml"
        old = _read(f, {}) or {}
        data = {"schema": 1, "audience": audience.strip(), "kind": kind, "format": format,
                "where": (where or "").strip(), "set": old.get("set") or _now().isoformat(timespec="minutes")}
        _write(f, data)
        return {"saved": str(f.relative_to(self.ws.root)), **data}

    def get_share(self, project: str) -> dict:
        """The project's audience, drafts, whether it has been shared, and how it landed."""
        d = self._dir(project)
        drafts = sorted(d.glob("draft-*.md")) if d.exists() else []
        return {"audience": _read(d / "audience.yaml"),
                "drafts": [str(p.relative_to(self.ws.root)) for p in drafts],
                "latest_draft": drafts[-1].read_text(encoding="utf-8") if drafts else "",
                "shared": _read(d / "shared.yaml", {}).get("events", []) if d.exists() else [],
                "heard_back": _read(d / "heard_back.yaml", {}).get("items", []) if d.exists() else []}

    # -------------------------------------------------------------------- drafts
    def save_share_draft(self, project: str, text: str, format: str = "") -> dict:
        """Save a version of the share-out. Built from the learner's own words; each save is
        a new version, so nothing they wrote is overwritten."""
        from .core import HarnessError
        self.ws._require_project(project)
        if not (text or "").strip():
            raise HarnessError("The draft is empty.")
        d = self._dir(project)
        n = len(list(d.glob("draft-*.md"))) + 1 if d.exists() else 1
        f = d / f"draft-{n:02d}.md"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text.strip() + "\n", encoding="utf-8")
        step = self._share_step(project)
        if step:
            self.ws.record_attempt(project, step, f"[share-out draft {n}]\n{text.strip()}")
        return {"saved": str(f.relative_to(self.ws.root)), "version": n,
                "format": format or (_read(d / "audience.yaml", {}) or {}).get("format", "")}

    def _share_step(self, project: str) -> str:
        for s in self.ws.get_plan(project).get("steps", []):
            if s.get("format") == "share-out":
                return s["id"]
        return ""

    # -------------------------------------------------------------------- shared
    def mark_shared(self, project: str, how: str, where: str = "", who: str = "", link: str = "",
                    note: str = "") -> dict:
        """The learner shared it (they did, not the harness). Records the moment, closes the
        share-out step as drafted, and adds it to their shared moments."""
        from .core import HarnessError, _now
        self.ws._require_project(project)
        if how not in ("explained", "showed", "posted", "presented", "sent"):
            raise HarnessError("how must be explained, showed, posted, presented or sent.")
        d = self._dir(project)
        f = d / "shared.yaml"
        data = _read(f, {}) or {"schema": 1, "events": []}
        ev = {"at": _now().isoformat(timespec="minutes"), "how": how}
        for k, v in (("where", where), ("who", who), ("link", link), ("note", note)):
            if v.strip():
                ev[k] = v.strip()
        data["events"].append(ev)
        _write(f, data)
        step = self._share_step(project)
        text = note.strip() or f"{how.capitalize()} the project" + (f" to {who}" if who else "") + \
            (f" on {where}" if where else "")
        self.ws.reports.record_shared({"posted": "showed", "presented": "showed", "sent": "showed"}.get(how, how),
                                      text, who=who, project=project, step=step)
        out: dict[str, Any] = {"shared": ev}
        if step:
            prog = self.ws.get_progress(project)["steps"].get(step, {})
            if not prog.get("attempts"):
                self.ws.record_attempt(project, step, f"[shared] {text}")
            if prog.get("status") not in ("drafted", "defended"):
                self.ws.set_status(project, step, "drafted", "tutor")
                out["step"] = {step: "drafted"}
        return out

    def heard_back(self, project: str, text: str, from_whom: str = "") -> dict:
        """How it landed: a reaction, a question, a comment, in the learner's words (or pasted,
        with names removed). Questions people asked often suggest the next project."""
        from .core import HarnessError, _now
        if not (text or "").strip():
            raise HarnessError("What did they say?")
        d = self._dir(project)
        f = d / "heard_back.yaml"
        data = _read(f, {}) or {"schema": 1, "items": []}
        item = {"at": _now().isoformat(timespec="minutes"), "text": text.strip()}
        if from_whom.strip():
            item["from"] = from_whom.strip()
        data["items"].append(item)
        _write(f, data)
        self.ws.reports.record_shared("heard-back", text, who=from_whom, project=project)
        return {"saved": str(f.relative_to(self.ws.root)), "items": len(data["items"])}

    # ------------------------------------------------------------ retrospective
    def save_retrospective(self, answers: dict, project: str = "", period: str = "") -> dict:
        """The learner's look back, in their words. answers: any of went_well, was_hard,
        surprised, differently, how_i_learn, sharing, next. Every question can be skipped."""
        from .core import HarnessError, _now, _slug
        clean = {k: str(v).strip() for k, v in (answers or {}).items() if k in RETRO_QUESTIONS and str(v).strip()}
        if not clean:
            raise HarnessError("A retrospective needs at least one answer in the learner's words.")
        if project:
            self.ws._require_project(project)
        t = _now()
        f = self.ws.private / "reflection" / "retros" / f"{t.date().isoformat()}-{_slug(project or period or 'period')}.yaml"
        n = 2
        while f.exists():
            f = f.with_name(f"{f.stem}-{n}.yaml")
            n += 1
        data = {"schema": 1, "at": t.isoformat(timespec="minutes"), "project": project, "period": period,
                "answers": clean}
        _write(f, data)
        self._index_retro(data, f)
        return {"saved": str(f.relative_to(self.ws.root)), "answered": list(clean)}

    def _index_retro(self, data: dict, f: Path) -> None:
        self.ws.index.upsert(f"retro:{f.stem}", "retro", " ".join(data["answers"].values()),
                             {"scope": "reflection", "author": "learner", "project": data.get("project", ""),
                              "date": data["at"][:10]}, str(f.relative_to(self.ws.root)))

    def retrospectives(self, since: str = "", until: str = "", project: str = "") -> list[dict]:
        d = self.ws.private / "reflection" / "retros"
        out = []
        for f in sorted(d.glob("*.yaml"), reverse=True) if d.exists() else []:
            r = _read(f, {}) or {}
            day = str(r.get("at", ""))[:10]
            if (since and day < since) or (until and day > until) or (project and r.get("project") != project):
                continue
            out.append(r)
        return out

    def retro_due(self) -> list[str]:
        """Projects whose steps are all done but that have no retrospective yet."""
        done = []
        for p in self.ws.orient._projects():
            if p["steps"] and not p["now"] and not self.retrospectives(project=p["project"]):
                done.append(p["project"])
        return done
