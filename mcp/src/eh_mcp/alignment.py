"""Standards alignment, decided while the learning happens and kept beside it.

Each project has a sidecar, projects/<slug>/standards.yaml. It is the one record reports
and the catalog read, so the same work always reports the same standards:

- At planning, write_plan resolves what each step cites (directly, or through its concepts'
  authored links in the program) and retrieves candidates once per new step. Candidates are
  frozen in the file; the planner accepts or declines each with the learner.
- During a session, the tutor can add a standard the learner's work showed, with their words.
- When a step is drafted or defended, every standard on it is marked exercised, dated.

Statements are snapshotted, so reloading the standards set never rewrites history.
Nothing here searches at report time.
"""
from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .core import Workspace

SCHEMA = 1
DECISIONS = ("accept", "decline")


def _today() -> str:
    return _dt.date.today().isoformat()


class Alignment:
    def __init__(self, ws: "Workspace"):
        self.ws = ws

    # ------------------------------------------------------------- storage
    def path(self, project: str) -> Path:
        return self.ws.project_dir(project) / "standards.yaml"

    def _load(self, project: str) -> dict | None:
        from .core import _read_yaml
        return _read_yaml(self.path(project), None)

    def _save(self, project: str, data: dict) -> None:
        from .core import _write_yaml
        _write_yaml(self.path(project), data)

    def _empty(self, project: str) -> dict:
        src = self.ws.knowledge._state().get("standards_source") or (
            {"subject": "expectation sets", "loaded": _today()} if self.ws.expectations.list()["sets"] else {})
        return {"schema": SCHEMA, "project": project,
                "source": {k: src[k] for k in ("subject", "jurisdictions", "loaded") if k in src} or None,
                "standards": [], "candidates": [], "searched_steps": []}

    def _any_standards(self) -> bool:
        return bool(self.ws.knowledge._state().get("standards_source") or self.ws.expectations.list()["sets"])

    # ------------------------------------------------------------- lookups
    def _pinned(self) -> dict[str, dict]:
        from .knowledge import _code_key
        out = {}
        for _, meta in self.ws.index.docs_in_scope("reference"):
            if meta.get("_kind") == "standard" and meta.get("code"):
                out[_code_key(meta["code"])] = meta
        return out

    def _concept_links(self) -> dict[str, set[str]]:
        from .knowledge import _slug
        cites: dict[str, set[str]] = {}
        with self.ws.index._conn() as c:
            for src, meta in c.execute("SELECT e.src, d.meta FROM edges e JOIN docs d ON d.id = e.dst "
                                       "WHERE e.rel = 'cites'").fetchall():
                code = json.loads(meta).get("code")
                if code:
                    cites.setdefault(_slug(src.removeprefix("concept:")), set()).add(code)
        return cites

    @staticmethod
    def _snapshot(code: str, meta: dict | None) -> dict:
        meta = meta or {}
        return {"code": meta.get("code") or code, "statement": meta.get("statement", ""),
                "grade_band": meta.get("grade", ""), "domain": list(meta.get("domain", [])),
                "jurisdiction": meta.get("jurisdiction", ""), "attribution": meta.get("attribution", ""),
                "origin": meta.get("origin", "common"), **({"set": meta["set"]} if meta.get("set") else {})}

    def _entry(self, data: dict, code: str) -> dict | None:
        from .knowledge import _code_key
        return next((s for s in data["standards"] if _code_key(s["code"]) == _code_key(code)), None)

    def _put(self, data: dict, code: str, step: str, via: str, by: str, when: str,
             pinned: dict[str, dict], evidence: str = "") -> dict:
        from .knowledge import _code_key
        rec = self._entry(data, code)
        if rec is None:
            meta = pinned.get(_code_key(code))
            rec = {**self._snapshot(code, meta), "in_standards_set": bool(meta), "steps": [], "via": {},
                   "decided": {"at": _today(), "by": by, "when": when}, "exercised": []}
            data["standards"].append(rec)
        if step and step not in rec["steps"]:
            rec["steps"].append(step)
        if step:
            rec["via"].setdefault(step, via)
        if evidence.strip():
            rec.setdefault("evidence", []).append({"step": step, "at": _today(), "text": evidence.strip()[:400]})
        return rec

    # ------------------------------------------------------------- planning
    def align_plan(self, project: str, steps: list[dict], search: bool = True) -> dict:
        """Called by write_plan. Resolves what each step cites; retrieves candidates once per new step."""
        from .knowledge import _slug
        loaded = self._any_standards()
        data = self._load(project) or self._empty(project)
        pinned = self._pinned() if loaded else {}
        links = self._concept_links() if loaded else {}
        ids = {s["id"] for s in steps}
        for s in steps:
            for code in s.get("standards_cited", []):
                self._put(data, code, s["id"], "cited", "planner", "planning", pinned)
            for cpt in s.get("concepts", []):
                for code in sorted(links.get(_slug(str(cpt)), set())):
                    self._put(data, code, s["id"], "concept-link", "planner", "planning", pinned)
        for rec in data["standards"]:     # steps dropped from the plan keep their exercised history
            rec["retired_steps"] = sorted(set(rec["steps"]) - ids) or []
            if not rec["retired_steps"]:
                rec.pop("retired_steps")
        added = []
        if loaded and search:
            have = {x["code"] for x in data["standards"]}
            known = {c["code"]: c for c in data["candidates"]}
            found: dict[str, dict] = {}      # code -> best (rank, step, match) across the new steps
            for s in steps:
                if s["id"] in data["searched_steps"]:
                    continue
                query = " ".join([str(s.get("does", "")), *map(str, s.get("concepts", []))])
                for rank, m in enumerate(self.ws.knowledge.relevant_standards(query, limit=4, expand=False)["matches"]):
                    if not m["code"] or m["code"] in have:
                        continue
                    f = found.setdefault(m["code"], {"m": m, "steps": []})
                    f["steps"].append((rank, s["id"]))
                data["searched_steps"].append(s["id"])
            for code, f in found.items():
                ranked = [sid for _, sid in sorted(f["steps"])]   # the step that ranks it highest comes first
                if code in known:
                    known[code]["steps"] = list(dict.fromkeys(known[code].get("steps", [known[code]["step"]]) + ranked))
                    continue
                cand = {**self._snapshot(code, f["m"]), "step": ranked[0], "steps": ranked,
                        "retrieved_at": _today(), "review": "pending"}
                data["candidates"].append(cand)
                added.append(cand)
        self._save(project, data)
        return {"file": str(self.path(project).relative_to(self.ws.root)), "loaded": loaded,
                "aligned": [{"code": r["code"], "statement": r["statement"], "steps": r["steps"]}
                            for r in data["standards"]],
                "candidates_to_review": [{"code": c["code"], "statement": c["statement"], "step": c["step"],
                                          **({"also": c["steps"][1:]} if len(c.get("steps", [])) > 1 else {})}
                                         for c in data["candidates"] if c["review"] == "pending"],
                "note": ("Read each candidate's statement with the learner's project in mind; accept only those "
                         "the step will exercise, decline the rest: standards(action='review', ...).")
                if added else ("" if loaded else "No standards are loaded; nothing was aligned.")}

    # -------------------------------------------------------------- actions
    def manage(self, action: str, project: str, step: str = "", code: str = "", decision: str = "",
               evidence: str = "", by: str = "tutor") -> dict:
        from .core import HarnessError
        from .knowledge import _code_key
        if action == "show":
            return self.read(project)
        data = self._load(project) or self._empty(project)
        if action == "review":
            if decision not in DECISIONS:
                raise HarnessError("decision must be accept or decline.")
            cand = next((c for c in data["candidates"] if _code_key(c["code"]) == _code_key(code)), None)
            if not cand:
                raise HarnessError(f"{code} is not a candidate for {project}.")
            cand["review"] = "accepted" if decision == "accept" else "declined"
            cand["reviewed_at"] = _today()
            if decision == "accept":
                rec = self._put(data, cand["code"], step or cand["step"], "chosen", by, "planning", self._pinned())
                for k in ("statement", "grade_band", "domain", "jurisdiction", "attribution", "origin", "set"):
                    if cand.get(k):
                        rec[k] = cand[k]
        elif action == "add":
            if not (code and step):
                raise HarnessError("add needs a code and the step whose work showed it.")
            self.ws._plan_step(project, step)
            pinned = self._pinned()
            if _code_key(code) not in pinned:
                raise HarnessError(f"{code} is not in the loaded standards; check the code.")
            self._put(data, code, step, "chosen", by, "session", pinned, evidence)
            st = self.ws._progress(project).get("steps", {}).get(step, {})
            if st.get("status") in ("drafted", "defended"):
                self._mark(data, step, st["status"], [code])
        elif action == "drop":
            rec = self._entry(data, code)
            if not rec:
                raise HarnessError(f"{code} is not aligned to {project}.")
            done = {e["step"] for e in rec.get("exercised", [])}
            if (step and step in done) or (not step and done):
                raise HarnessError(f"{code} was exercised on {', '.join(sorted(done))}; that history stays.")
            if step:
                rec["steps"] = [x for x in rec["steps"] if x != step]
                rec["via"].pop(step, None)
            if not step or not rec["steps"]:
                data["standards"] = [x for x in data["standards"] if x is not rec]
        else:
            raise HarnessError("action must be show, review, add or drop.")
        self._save(project, data)
        return self.read(project)

    def _mark(self, data: dict, step: str, status: str, codes: list[str] | None = None) -> list[str]:
        from .knowledge import _code_key
        want = {_code_key(c) for c in codes} if codes else None
        marked = []
        for rec in data["standards"]:
            if step not in rec["steps"] or (want is not None and _code_key(rec["code"]) not in want):
                continue
            ex = rec.setdefault("exercised", [])
            if not any(e["step"] == step and e["status"] == status for e in ex):
                ex.append({"step": step, "status": status, "at": _today()})
                marked.append(rec["code"])
        return marked

    def step_status(self, project: str, step: str, status: str) -> list[str]:
        """Called when a step is drafted or defended."""
        if status not in ("drafted", "defended") or not self.path(project).exists():
            return []
        data = self._load(project)
        marked = self._mark(data, step, status)
        if marked:
            self._save(project, data)
        return marked

    # --------------------------------------------------------------- reading
    def read(self, project: str) -> dict:
        """The sidecar. A project planned before sidecars existed is aligned once, now, from its plan
        and progress, and marked backfilled; after that it is read like any other."""
        from .core import _read_yaml
        data = self._load(project)
        if data is not None and not data.get("source") and self._any_standards():
            data = None   # aligned before any standards were loaded: align now, once
        if data is None:
            plan = _read_yaml(self.ws.project_dir(project) / "program.yaml", {}) or {}
            self.align_plan(project, plan.get("steps", []))
            data = self._load(project)
            data["backfilled"] = _today()
            prog = (_read_yaml(self.ws.project_dir(project) / "progress.yaml", {}) or {}).get("steps", {})
            for sid, st in prog.items():
                if st.get("status") in ("drafted", "defended"):
                    self._mark(data, sid, st["status"])
            self._save(project, data)
        return data

    def summary(self, project: str, since: str = "", until: str = "") -> dict:
        """What reports and the catalog show: exercised (in the period, and before), aligned but ahead,
        and candidates still waiting for review."""
        data = self.read(project)
        def in_window(at: str) -> bool:
            return (not since or at >= since) and (not until or at <= until)
        exercised, before, ahead = [], [], []
        for rec in data["standards"]:
            short = {k: rec.get(k) for k in ("code", "statement", "grade_band", "domain")}
            short["origin"] = rec.get("origin", "common")
            if rec.get("set"):
                short["set"] = rec["set"]
            short["steps"] = rec["steps"]
            if rec.get("evidence"):
                short["evidence"] = rec["evidence"][-2:]      # latest two; the file keeps all
            ex = rec.get("exercised", [])
            if any(in_window(e["at"]) for e in ex):
                exercised.append({**short, "exercised": [e for e in ex if in_window(e["at"])]})
            elif ex:
                before.append({**short, "exercised": ex})
            else:
                ahead.append(short)
        return {"file": str(self.path(project).relative_to(self.ws.root)),
                "source": data.get("source"), "backfilled": data.get("backfilled", ""),
                "exercised": sorted(exercised, key=lambda r: r["code"]),
                "exercised_before": sorted(before, key=lambda r: r["code"]),
                "ahead": sorted(ahead, key=lambda r: r["code"]),
                "pending_review": [{"code": c["code"], "statement": c["statement"], "step": c["step"]}
                                   for c in data["candidates"] if c["review"] == "pending"],
                "attribution": " ".join(sorted({r["attribution"] for r in data["standards"] if r.get("attribution")}))}
