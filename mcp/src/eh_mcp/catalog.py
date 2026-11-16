"""Local learning catalog: classification, ordering, archiving and a generated HTML view."""
from __future__ import annotations

import json
import datetime as _dt
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .core import Workspace

PLACEHOLDER = "__CATALOG_DATA__"
KINDS = ("ad-hoc", "developing", "structured", "continuous")
PRIORITIES = ("now", "next", "later", "someday")


def template_path() -> Path:
    return Path(__file__).resolve().parents[3] / "skills" / "start" / "catalog.html"


class Catalog:
    def __init__(self, ws: "Workspace"):
        self.ws = ws

    @property
    def state_file(self) -> Path:
        return self.ws.private / "catalog.yaml"

    def _state(self) -> dict:
        from .core import _read_yaml
        return _read_yaml(self.state_file, {"schema": 1, "items": {}}) or {"schema": 1, "items": {}}

    def _save(self, state: dict) -> None:
        from .core import _write_yaml
        _write_yaml(self.state_file, state)

    def _inferred_kind(self, project: dict, arc_names: list[str], learner: dict) -> str:
        if len(project.get("steps", [])) >= 3:
            return "structured"
        if project.get("steps") or arc_names:
            return "developing"
        return "ad-hoc"

    def data(self) -> dict:
        from .core import _read_yaml, _now
        state = self._state().get("items", {})
        arcs = self.ws.orient._arcs()
        projects = self.ws.orient._projects()
        learner = _read_yaml(self.ws.private / "learner.yaml", {}) or {}
        project_arcs: dict[str, list[str]] = {}
        for name, arc in arcs.items():
            for stop in arc.get("path", []):
                if stop.get("project"):
                    project_arcs.setdefault(stop["project"], []).append(name)

        def lesson_standards(slug: str) -> dict:
            """From the project's sidecar only: the catalog never searches standards."""
            sm = self.ws.alignment.summary(slug)

            def short(r: dict) -> dict:
                return {"code": r["code"], "statement": r["statement"], "steps": r["steps"]}
            return {"loaded": bool(sm["source"]), "file": sm["file"],
                    "covered": [short(r) for r in sm["exercised"]],
                    "ahead": [short(r) for r in sm["ahead"]],
                    "pending_review": len(sm["pending_review"]), "attribution": sm["attribution"]}

        items = []
        for name, arc in arcs.items():
            key = f"arc:{name}"
            custom = state.get(key, {})
            path = arc.get("path", [])
            items.append({"id": key, "entity": "trajectory", "slug": name,
                          "title": arc.get("goal") or name.replace("-", " ").title(),
                          "description": arc.get("why", ""), "kind": custom.get("kind", "continuous"),
                          "priority": custom.get("priority", "next"), "rank": custom.get("rank", 999),
                          "archived": bool(custom.get("archived", False)), "cadence": arc.get("cadence", ""),
                          "progress": f"{sum(bool(x.get('project')) for x in path)} linked lessons",
                          "lessons": [x.get("project") for x in path if x.get("project")],
                          "next": next((x.get("title", "") for x in path if x.get("project")), "")})
        for project in projects:
            key = f"project:{project['project']}"
            custom = state.get(key, {})
            plan = _read_yaml(self.ws.project_dir(project["project"]) / "program.yaml", {}) or {}
            steps = plan.get("steps", [])
            done = len(project.get("done", []))
            kind = custom.get("kind") or self._inferred_kind(plan, project_arcs.get(project["project"], []), learner)
            items.append({"id": key, "entity": "lesson", "slug": project["project"],
                          "title": project.get("question") or project["project"].replace("-", " ").title(),
                          "description": (project.get("now") or {}).get("does", ""), "kind": kind,
                          "priority": custom.get("priority", "now" if project.get("now") else "later"),
                          "rank": custom.get("rank", 999), "archived": bool(custom.get("archived", False)),
                          "progress": f"{done} of {len(steps)} steps complete" if steps else "No fixed plan",
                          "trajectories": project_arcs.get(project["project"], []),
                          "next": (project.get("now") or {}).get("does", ""),
                          "last_active": _dt.datetime.fromtimestamp(project.get("_touched", 0)).date().isoformat()
                          if project.get("_touched") else "",
                          "path": str(self.ws.project_dir(project["project"])),
                          "standards": lesson_standards(project["project"])})
        for key, custom in state.items():
            if not key.startswith("external:"):
                continue
            items.append({"id": key, "entity": "external", "slug": key.split(":", 1)[1],
                          "title": custom.get("title", key.split(":", 1)[1].replace("-", " ").title()),
                          "description": custom.get("notes", ""), "provider": custom.get("provider", ""),
                          "url": custom.get("url", ""), "kind": custom.get("kind", "developing"),
                          "priority": custom.get("priority", "later"), "rank": custom.get("rank", 999),
                          "archived": bool(custom.get("archived", False)),
                          "progress": custom.get("progress", "Learner-reported external learning"),
                          "trajectories": [], "next": custom.get("next", ""),
                          "last_active": custom.get("last_active") or custom.get("added_on", "")})
        p_order = {p: i for i, p in enumerate(PRIORITIES)}
        items.sort(key=lambda x: (x["archived"], p_order.get(x["priority"], 99), x["rank"], x["title"].lower()))
        active_lessons = [x for x in items if x["entity"] in ("lesson", "external") and not x["archived"]]
        trajectory_counts = {name: sum(name in x.get("trajectories", []) for x in active_lessons) for name in arcs}
        linked = sum(trajectory_counts.values())
        dominant = max(trajectory_counts.values(), default=0)
        enough = len(active_lessons) >= 3
        if not enough:
            shape = "not enough evidence yet"
        elif len([n for n in trajectory_counts.values() if n]) >= 3 and (not linked or dominant / linked < .6):
            shape = "renaissance pattern"
        elif linked and dominant / linked >= .7:
            shape = "specialist pattern"
        else:
            shape = "mixed breadth-and-depth pattern"
        analytics = {
            "portfolio_shape": shape, "enough_evidence": enough,
            "note": "A description of the current portfolio, not a fixed identity or ability judgment.",
            "active_lessons": len(active_lessons), "trajectories": len(arcs),
            "linked_lessons": linked, "unlinked_lessons": sum(not x.get("trajectories") for x in active_lessons),
            "kinds": {kind: sum(x["kind"] == kind and not x["archived"] for x in items) for kind in KINDS},
            "priorities": {p: sum(x["priority"] == p and not x["archived"] for x in items) for p in PRIORITIES},
            "suggestions": "available only when the learner asks the academic advisor",
        }
        by_slug = {x["slug"]: x for x in items if x["entity"] == "lesson"}
        for x in items:
            if x["entity"] == "trajectory":
                parts = [by_slug[s]["standards"] for s in x["lessons"] if s in by_slug]
                x["standards"] = {"covered": sorted({c["code"] for p in parts for c in p.get("covered", [])}),
                                  "ahead": sorted({c["code"] for p in parts for c in p.get("ahead", [])})}
        lessons_std = [x["standards"] for x in active_lessons if x.get("standards", {}).get("loaded")]
        covered_all: dict[str, dict] = {}
        for st in lessons_std:
            for c in st["covered"]:
                covered_all.setdefault(c["code"], c)
        analytics["standards"] = {
            "loaded": bool(lessons_std) or self.ws.alignment._any_standards(),
            "covered": sorted(covered_all.values(), key=lambda c: c["code"]),
            "pending_review": sum(st["pending_review"] for st in lessons_std),
            "ahead_count": len({r["code"] for st in lessons_std for r in st["ahead"]}),
            "note": "Recorded in each lesson's standards.yaml as the work happened; reference points, not requirements or gaps.",
            "attribution": " ".join(sorted({st["attribution"] for st in lessons_std if st.get("attribution")})),
        }
        dates = sorted(x["last_active"] for x in active_lessons if x.get("last_active"))
        analytics["activity_span"] = {"from": dates[0], "through": dates[-1]} if dates else None
        return {"schema": 1, "generated": _now().isoformat(timespec="minutes"), "items": items,
                "counts": {"active": sum(not x["archived"] for x in items),
                           "archived": sum(x["archived"] for x in items)},
                "kinds": list(KINDS), "priorities": list(PRIORITIES), "analytics": analytics}

    def manage(self, action: str = "show", item: str = "", priority: str = "", rank: int = 0,
               kind: str = "", title: str = "", provider: str = "", progress: str = "",
               notes: str = "", url: str = "") -> dict:
        from .core import HarnessError
        if action == "show":
            return self.write()
        if action == "add_external":
            from .core import _slug
            if not title.strip():
                raise HarnessError("An external learning item needs a title in the learner's words.")
            target = f"external:{_slug(title + '-' + provider)}"
            state = self._state()
            state.setdefault("items", {})[target] = {
                "title": title.strip(), "provider": provider.strip(), "progress": progress.strip(),
                "notes": notes.strip(), "url": url.strip(), "kind": kind if kind in KINDS else "developing",
                "priority": priority if priority in PRIORITIES else "later", "rank": rank or 999,
                "archived": False, "learner_reported": True,
                "added_on": _dt.date.today().isoformat(), "last_active": _dt.date.today().isoformat(),
            }
            self._save(state)
            out = self.write()
            out["changed"] = {"item": target, "action": action}
            return out
        target = item if item.startswith(("project:", "arc:", "external:")) else f"project:{item}"
        valid = {x["id"] for x in self.data()["items"]}
        if target not in valid:
            matches = [x for x in valid if x.split(":", 1)[1] == item]
            if len(matches) == 1:
                target = matches[0]
            else:
                raise HarnessError(f"No catalog item matches {item!r}.")
        state = self._state()
        rec = state.setdefault("items", {}).setdefault(target, {})
        if action == "archive":
            rec["archived"] = True
        elif action == "restore":
            rec["archived"] = False
        elif action == "prioritize":
            if priority not in PRIORITIES:
                raise HarnessError(f"priority must be one of {', '.join(PRIORITIES)}.")
            rec["priority"] = priority
        elif action == "rank":
            if rank < 1:
                raise HarnessError("rank must be a positive whole number.")
            rec["rank"] = int(rank)
        elif action == "classify":
            if kind not in KINDS:
                raise HarnessError(f"kind must be one of {', '.join(KINDS)}.")
            rec["kind"] = kind
        else:
            raise HarnessError("action must be show, add_external, archive, restore, prioritize, rank or classify.")
        self._save(state)
        out = self.write()
        out["changed"] = {"item": target, "action": action, "value": priority or rank or kind or True}
        return out

    def render(self, data: dict) -> str | None:
        path = template_path()
        if not path.exists():
            return None
        payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
        return path.read_text(encoding="utf-8").replace(PLACEHOLDER, payload, 1)

    def write(self) -> dict:
        data = self.data()
        page = self.render(data)
        # The page gets every statement; the chat gets codes only, to keep the context small.
        slim = json.loads(json.dumps(data))
        for x in slim["items"]:
            st = x.get("standards") or {}
            for k in ("covered", "ahead"):
                if isinstance(st.get(k), list):
                    st[k] = [c["code"] if isinstance(c, dict) else c for c in st[k]]
        out: dict[str, Any] = {"data": slim, "template": str(template_path())}
        if page is not None:
            path = self.ws.views_dir / "CATALOG.html"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(page, encoding="utf-8")
            self.ws.retire_root_page("CATALOG.html")
            out["file"] = str(path)
        return out
