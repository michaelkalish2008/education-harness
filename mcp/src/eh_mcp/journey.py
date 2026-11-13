"""The journey: everything the learner has on one page, for the journey map.

``data()`` gathers the goals (arcs) and their stops, every project and its steps, the learner's
own notes (annotations, concept notes, attempts, diary, slips), bookmarks, open questions and
links, as plain JSON. ``write()`` puts that JSON into the bundled page template
(``skills/start/journey.html``) and saves ``JOURNEY.html`` beside ``MAP.md`` in the learner's
workspace, so it opens in a browser even when the app is closed. The tutor publishes the same
template with the same data as an artifact in the Claude app.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover
    from .core import Workspace

PLACEHOLDER = "__JOURNEY_DATA__"
URL = re.compile(r"https?://[^\s)\]>\"']+")
OPEN_KINDS = ("confusion", "question")
DONE = ("drafted", "defended")


def template_path() -> Path:
    """skills/start/journey.html at the plugin (or repo) root."""
    return Path(__file__).resolve().parents[3] / "skills" / "start" / "journey.html"


def _read(path: Path, default: Any = None) -> Any:
    from .core import _read_yaml
    return _read_yaml(path, default)


class Journey:
    def __init__(self, ws: "Workspace"):
        self.ws = ws

    @property
    def _state_file(self) -> Path:
        return self.ws.private / "journey.yaml"

    def set_link(self, url: str) -> dict:
        """Remember the published journey page, so the next update republishes the same one."""
        from .core import _write_yaml
        data = _read(self._state_file, {}) or {}
        data["artifact"] = url.strip()
        _write_yaml(self._state_file, data)
        return {"artifact": data["artifact"]}

    # ------------------------------------------------------------------ data
    def data(self, move: dict | None = None) -> dict:
        from .core import _now
        orient = self.ws.orient
        arcs_raw = orient._arcs()
        projects = orient._projects()
        by_name = {p["project"]: p for p in projects}

        proj_out = []
        for p in projects:
            d = self.ws.root / "projects" / p["project"]
            plan = _read(d / "program.yaml", {}) or {}
            prog = (_read(d / "progress.yaml", {}) or {}).get("steps", {})
            steps = [{"id": s["id"], "does": s.get("does", ""), "concepts": s.get("concepts", []),
                      "status": prog.get(s["id"], {}).get("status", "not started"),
                      "attempts": prog.get(s["id"], {}).get("attempts", 0),
                      "seen": prog.get(s["id"], {}).get("seen", [])}
                     for s in plan.get("steps", []) if not prog.get(s["id"], {}).get("retired")]
            proj_out.append({"project": p["project"], "question": p["question"], "idea": p["idea"],
                             "steps": steps, "now": (p["now"] or {}).get("step"),
                             "touched": p["_touched"]})

        proj_map = {p["project"]: p for p in proj_out}

        def stop_state(project: str) -> str:
            pp = proj_map.get(project)
            if not pp or not pp["steps"]:
                return "not started"
            if all(s["status"] in DONE for s in pp["steps"]):
                return "done"
            if any(s["status"] in DONE or s["attempts"] or s["seen"] for s in pp["steps"]):
                return "in progress"
            return "planned"

        arcs = []
        for name, arc in arcs_raw.items():
            path = []
            for i, item in enumerate(arc.get("path", [])):
                state = stop_state(item.get("project", ""))
                path.append({"index": i, "title": item.get("title", ""), "idea": item.get("idea", ""),
                             "project": item.get("project", ""), "state": state})
            touched = max((by_name[i["project"]]["_touched"] for i in arc.get("path", [])
                           if i.get("project") in by_name), default=0)
            arcs.append({"name": name, "goal": arc.get("goal", ""), "why": arc.get("why", ""),
                         "space": arc.get("space", ""), "path": path, "touched": touched})
        arcs.sort(key=lambda a: -a["touched"])
        placed = {i["project"] for a in arcs for i in a["path"] if i["project"]}
        for p in proj_out:
            p["placed"] = p["project"] in placed
            p["state"] = stop_state(p["project"])

        notes = self._notes()
        current = max((p for p in proj_out if p["now"]), key=lambda p: p["touched"], default=None)
        links = []
        for n in notes:
            for u in URL.findall(n["text"]):
                links.append({"url": u.rstrip(".,;"), "note": n["id"], "at": n["at"],
                              "project": n.get("project", ""), "step": n.get("step", ""),
                              "concept": n.get("concept", "")})
        state = _read(self._state_file, {}) or {}
        return {
            "schema": 1,
            "generated": _now().isoformat(timespec="minutes"),
            "arcs": arcs,
            "projects": sorted(proj_out, key=lambda p: -p["touched"]),
            "current": {"project": current["project"], "step": current["now"]} if current else None,
            "notes": notes,
            "bookmarks": orient.list_checkpoints(limit=50)["checkpoints"],
            "links": links,
            "next": move,
            "artifact": state.get("artifact", ""),
        }

    def _notes(self) -> list[dict]:
        """Every note in the learner's words, newest first. kind: question, confusion, insight,
        gist, opinion, connection (annotations), keep (concept notes), attempt, diary, slip."""
        priv = self.ws.private
        out: list[dict] = []
        refl = priv / "reflection"
        for f in sorted((refl / "annotations").glob("*.yaml")) if (refl / "annotations").exists() else []:
            for it in (_read(f, {}) or {}).get("items", []):
                out.append({"id": it.get("id", ""), "at": str(it.get("at", "")), "kind": it.get("kind", "gist"),
                            "text": it.get("text", ""), "project": it.get("project", ""),
                            "step": it.get("step", ""),
                            "concept": it.get("ref", "") if it.get("anchor") == "concept" else "",
                            "open": it.get("kind") in OPEN_KINDS and not it.get("resolved_by"),
                            "resolved_by": it.get("resolved_by", "")})
        for f in sorted((refl / "errors").glob("*.yaml")) if (refl / "errors").exists() else []:
            for i, it in enumerate((_read(f, {}) or {}).get("items", [])):
                text = it.get("what", "") + (f" What helped: {it['helped']}" if it.get("helped") else "")
                out.append({"id": it.get("id", f"slip-{f.stem}-{i}"), "at": str(it.get("at", f.stem)),
                            "kind": "slip", "text": text, "project": it.get("project", ""),
                            "step": it.get("step", ""), "concept": "", "open": False})
        cdir = priv / "concepts"
        for f in sorted(cdir.glob("*.yaml")) if cdir.exists() else []:
            c = _read(f, {}) or {}
            for i, n in enumerate(c.get("notes", [])):
                out.append({"id": f"keep-{c.get('concept', f.stem)}-{i}", "at": str(n.get("at", "")),
                            "kind": "keep", "text": n.get("text", ""), "project": n.get("project", ""),
                            "step": n.get("step", ""), "concept": c.get("name") or c.get("concept", f.stem),
                            "open": False})
        adir = priv / "attempts"
        for f in sorted(adir.glob("*/*/*.md")) if adir.exists() else []:
            stamp = f.stem[:19]
            at = f"{stamp[:10]}T{stamp[11:13]}:{stamp[13:15]}" if len(stamp) >= 15 and stamp[10] == "T" else stamp[:10]
            out.append({"id": f"attempt-{f.parent.parent.name}-{f.parent.name}-{f.stem}", "at": at,
                        "kind": "attempt", "text": f.read_text(encoding="utf-8").strip(),
                        "project": f.parent.parent.name, "step": f.parent.name, "concept": "", "open": False})
        ddir = priv / "diary"
        for f in sorted(ddir.rglob("*.md")) if ddir.exists() else []:
            raw = f.read_text(encoding="utf-8")
            head, body = "", raw
            if raw.startswith("---\n"):
                head, _, body = raw[4:].partition("\n---\n")
            meta = dict(line.split(":", 1) for line in head.splitlines() if ":" in line)
            out.append({"id": f"diary-{f.stem}", "at": (meta.get("at") or meta.get("date") or f.name[:10]).strip(),
                        "kind": "diary", "text": body.strip(), "project": (meta.get("project") or "").strip(),
                        "step": "", "concept": "", "open": False})
        out.sort(key=lambda n: n["at"], reverse=True)
        return out

    # ------------------------------------------------------------------ page
    def render(self, data: dict) -> str | None:
        t = template_path()
        if not t.exists():
            return None
        payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
        return t.read_text(encoding="utf-8").replace(PLACEHOLDER, payload, 1)

    def write(self, move: dict | None = None) -> dict:
        """Save JOURNEY.html in the workspace. Returns the data and where the page went.
        move: the suggested next move from where_am_i, shown at the foot of the page."""
        data = self.data(move)
        page = self.render(data)
        out: dict[str, Any] = {"data": data, "template": str(template_path())}
        if page is not None:
            path = self.ws.root / "JOURNEY.html"
            path.write_text(page, encoding="utf-8")
            out["file"] = str(path)
        return out
