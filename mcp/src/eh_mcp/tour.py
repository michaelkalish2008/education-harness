"""The tour: the default first lesson, which teaches the harness by using it.

- A new learner (no projects, no goals, the tour never taken or skipped) gets the move
  ``welcome`` from ``where_am_i``: topic first, one question, then a first small lesson.
  The tour is opt-in ("show me how this works"). Nothing is written until they start: setup stays lazy.
- ``introduce`` records which phrases ("hint", "note this", "bookmark this", ...) the learner has
  been shown, so each is taught once, at the moment it is first useful, across chats.
- ``start`` seeds ``projects/how-this-works/`` from ``programs/harness-tour/program.yaml``.
  It is an ordinary project: notes, reveals, bookmarks and statuses all work on it, so every
  step practises a real feature on a tiny topic the learner chooses.
- ``skip`` records that they'd rather go straight to learning. Either way, the tour can be
  started again later ("show me how this works").
- State lives in ``.private/tour.yaml``; "finished" is read from the project's progress.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .core import Workspace

TOUR_PROJECT = "how-this-works"
# Phrases taught just in time, in roughly the order a new learner first needs them.
FEATURES = ("hint", "note this", "place saved", "lets go", "look back", "where am i",
            "another way", "explain it back", "catalog", "knowledge map", "portfolio")


class Tour:
    def __init__(self, ws: "Workspace"):
        self.ws = ws

    @property
    def _file(self):
        return self.ws.private / "tour.yaml"

    def state(self) -> str:
        """none (never offered an answer), started, skipped or finished."""
        from .core import _read_yaml
        rec = _read_yaml(self._file, {}) or {}
        status = rec.get("status", "none")
        if status == "started" and self._done():
            return "finished"
        return status

    def _done(self) -> bool:
        from .core import _read_yaml
        d = self.ws.project_dir(TOUR_PROJECT)
        plan = _read_yaml(d / "program.yaml", {}) or {}
        prog = (_read_yaml(d / "progress.yaml", {}) or {}).get("steps", {})
        ids = [s["id"] for s in plan.get("steps", [])]
        return bool(ids) and all(prog.get(i, {}).get("status") in ("drafted", "defended") for i in ids)

    def _save(self, status: str) -> None:
        from .core import SCHEMA, _now, _read_yaml, _write_yaml
        rec = _read_yaml(self._file, {}) or {"schema": SCHEMA}
        rec["status"] = status
        rec.setdefault("history", []).append({"status": status, "at": _now().isoformat(timespec="minutes")})
        _write_yaml(self._file, rec)

    def start(self) -> dict:
        """Seed the tour project (once) and return its plan, ready for step s1."""
        from .core import PROGRAMS
        self.ws.ensure_workspace()
        if not (self.ws.project_dir(TOUR_PROJECT) / "program.yaml").exists():
            self.ws.init_project(TOUR_PROJECT, from_program=str(PROGRAMS / "harness-tour"))
        self._save("started")
        self.ws.log_session("Started the tour: how this works.", project=TOUR_PROJECT)
        return {"project": TOUR_PROJECT, "state": self.state(),
                "plan": self.ws.orient._plan_brief(TOUR_PROJECT),
                "next": "Read the start skill's references/tour.md, then begin step s1 with the learner's topic."}

    def skip(self) -> dict:
        self.ws.ensure_workspace()
        self._save("skipped")
        return {"state": "skipped", "next": "Go straight to what they want to learn; the tour stays available "
                                            "if they say 'show me how this works'."}

    def introduced(self) -> list[str]:
        from .core import _read_yaml
        return list((_read_yaml(self._file, {}) or {}).get("introduced", []))

    def introduce(self, feature: str) -> dict:
        """Record that the learner has been shown one phrase or feature (once)."""
        from .core import SCHEMA, HarnessError, _read_yaml, _write_yaml
        feature = (feature or "").strip().lower()
        if feature not in FEATURES:
            raise HarnessError(f"feature must be one of: {', '.join(FEATURES)}.")
        self.ws.ensure_workspace()
        rec = _read_yaml(self._file, {}) or {"schema": SCHEMA, "status": "none"}
        have = rec.setdefault("introduced", [])
        if feature not in have:
            have.append(feature)
            _write_yaml(self._file, rec)
        return {"introduced": list(have), "not_yet": [f for f in FEATURES if f not in have]}

    def offer(self) -> bool:
        """True when a brand-new learner should be offered the tour first."""
        return self.state() == "none"

    def summary(self) -> dict[str, Any]:
        have = self.introduced()
        return {"state": self.state(), "project": TOUR_PROJECT, "introduced": have,
                "not_yet": [f for f in FEATURES if f not in have]}
