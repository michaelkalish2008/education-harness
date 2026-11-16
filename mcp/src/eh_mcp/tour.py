"""The tour: the default first lesson, which teaches the harness by using it.

- A new learner (no projects, no goals, the tour never taken or skipped) gets the move
  ``tour`` from ``where_am_i``. Nothing is written until they start it: setup stays lazy.
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

    def offer(self) -> bool:
        """True when a brand-new learner should be offered the tour first."""
        return self.state() == "none"

    def summary(self) -> dict[str, Any]:
        return {"state": self.state(), "project": TOUR_PROJECT}
