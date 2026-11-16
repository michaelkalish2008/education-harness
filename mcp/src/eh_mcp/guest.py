"""Guest mode: a throwaway learning space for someone trying the harness on the owner's computer.

- ``start`` creates ``.private/guests/<id>/`` (a complete, empty workspace) and makes it the active one,
  so every tool reads and writes there: the guest is a brand-new learner and the owner's profile,
  goals, notes and bookmarks are never read or written.
- Time to live: ``session`` (default) lasts as long as the guest keeps using it and expires after
  ``SESSION_IDLE`` without a tool call; ``day`` and ``week`` keep it that long from when it was asked.
- ``end`` deletes the space unless ``keep`` is day or week, then returns to the owner's space.
- Expired spaces are swept on server start and on every guest action. Which space is active is kept in
  ``.private/guest_active.json`` so a server restart mid-session stays in the guest's space.
"""

from __future__ import annotations

import json
import shutil
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

SESSION_IDLE = timedelta(hours=2)
KEEP = {"session": None, "day": timedelta(days=1), "week": timedelta(days=7)}


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Guests:
    def __init__(self, owner_root: Path, make_workspace):
        self.owner_root = Path(owner_root).expanduser().resolve()
        self.dir = self.owner_root / ".private" / "guests"
        self._make = make_workspace
        self._active_file = self.owner_root / ".private" / "guest_active.json"

    # ----------------------------------------------------------------- state
    def _meta_path(self, gid: str) -> Path:
        return self.dir / gid / "guest.json"

    def _meta(self, gid: str) -> dict | None:
        try:
            return json.loads(self._meta_path(gid).read_text())
        except (OSError, ValueError):
            return None

    def _write_meta(self, gid: str, meta: dict) -> None:
        p = self._meta_path(gid)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(meta, indent=2))

    def _expires(self, meta: dict) -> datetime:
        if meta.get("keep", "session") == "session":
            return datetime.fromisoformat(meta["last_active"]) + SESSION_IDLE
        return datetime.fromisoformat(meta["expires_at"])

    def active_id(self) -> str:
        try:
            gid = json.loads(self._active_file.read_text()).get("id", "")
        except (OSError, ValueError):
            return ""
        meta = self._meta(gid) if gid else None
        if not meta or self._expires(meta) <= _now():
            self._set_active("")
            return ""
        return gid

    def _set_active(self, gid: str) -> None:
        if gid:
            self._active_file.parent.mkdir(parents=True, exist_ok=True)
            self._active_file.write_text(json.dumps({"id": gid}))
        else:
            self._active_file.unlink(missing_ok=True)

    def _remove(self, gid: str) -> None:
        d = (self.dir / gid).resolve()
        if d.parent == self.dir.resolve() and d.is_dir():
            shutil.rmtree(d)

    def sweep(self) -> list[str]:
        """Delete every guest space past its time to live (never the active, unexpired one)."""
        gone = []
        if not self.dir.exists():
            return gone
        active = self.active_id()
        for d in self.dir.iterdir():
            if not d.is_dir() or d.name == active:
                continue
            meta = self._meta(d.name)
            if meta is None or self._expires(meta) <= _now():
                self._remove(d.name)
                gone.append(d.name)
        return gone

    def touch(self) -> None:
        gid = self.active_id()
        if gid:
            meta = self._meta(gid) or {}
            meta["last_active"] = _now().isoformat()
            self._write_meta(gid, meta)

    def _summary(self, gid: str) -> dict:
        meta = self._meta(gid) or {}
        return {"id": gid, "name": meta.get("name", ""), "keep": meta.get("keep", "session"),
                "expires": self._expires(meta).isoformat(timespec="minutes") if meta else ""}

    # ---------------------------------------------------------------- actions
    def start(self, name: str = "") -> dict:
        self.sweep()
        if self.active_id():
            return {"guest": True, "already": True, **self._summary(self.active_id())}
        gid = _now().strftime("%Y%m%d-%H%M") + "-" + uuid.uuid4().hex[:6]
        now = _now().isoformat()
        self._write_meta(gid, {"name": name, "created": now, "last_active": now, "keep": "session"})
        (self.dir / gid / "projects").mkdir(parents=True, exist_ok=True)
        self._set_active(gid)
        return {"guest": True, **self._summary(gid),
                "note": "A blank space for this session only. It is deleted when the guest ends it, or after "
                        "two idle hours, unless they ask to keep it for a day or a week."}

    def keep(self, duration: str) -> dict:
        gid = self.active_id()
        if not gid:
            return {"refused": "No guest session is active."}
        if duration not in KEEP:
            return {"refused": "keep must be session, day or week."}
        meta = self._meta(gid) or {}
        meta["keep"] = duration
        if KEEP[duration]:
            meta["expires_at"] = (_now() + KEEP[duration]).isoformat()
        meta["last_active"] = _now().isoformat()
        self._write_meta(gid, meta)
        return {"guest": True, **self._summary(gid)}

    def end(self, keep: str = "") -> dict:
        gid = self.active_id()
        if not gid:
            return {"guest": False, "note": "No guest session was active."}
        if keep in ("day", "week"):
            out = self.keep(keep)
            self._set_active("")
            return {"guest": False, "kept": out, "resume": f"setup(action='guest_resume', feature='{gid}')"}
        self._set_active("")
        self._remove(gid)
        self.sweep()
        return {"guest": False, "deleted": gid}

    def resume(self, gid: str) -> dict:
        self.sweep()
        if not gid or self._meta(gid) is None:
            return {"refused": "No kept guest space by that id; it may have expired."}
        self._set_active(gid)
        self.touch()
        return {"guest": True, **self._summary(gid)}

    def status(self) -> dict:
        gid = self.active_id()
        kept = [self._summary(d.name) for d in self.dir.iterdir()
                if d.is_dir() and d.name != gid] if self.dir.exists() else []
        return {"guest": bool(gid), "active": self._summary(gid) if gid else None, "kept": kept}


class ActiveWorkspace:
    """Forwards to whichever workspace is active, so tools follow a switch into or out of guest mode."""

    def __init__(self, guests: Guests):
        self._guests = guests
        self._cache: dict[Path, Any] = {}

    def _current(self):
        gid = self._guests.active_id()
        root = (self._guests.dir / gid) if gid else self._guests.owner_root
        root = root.resolve()
        if root not in self._cache:
            self._cache = {root: self._guests._make(root)}
        return self._cache[root]

    @property
    def is_guest(self) -> bool:
        return bool(self._guests.active_id())

    def __getattr__(self, name: str):
        return getattr(self._current(), name)
