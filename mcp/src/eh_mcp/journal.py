"""Reflection: annotations, errors and the journal that brings them back.

- Annotations are the learner's own words pinned to something: a step, a concept, a
  library item or section, a standard, a whiteboard item, or the day. Most will be
  half-formed: "I don't get why the error goes backwards", "I think this is like
  compounding". That is the point; nothing here is graded. An annotation can answer an
  earlier one ("now I get it"), which closes the earlier one as resolved.
- Errors are noted by the tutor, neutrally: what went sideways, what kind of slip it was,
  and what helped. They are evidence for learning, shown to the learner only in the
  journal and never as a score.
- The journal assembles, per day: annotations, the learner's responses (attempts and
  defenses), content covered (steps, library items opened, board items kept), standards
  touched, exercises performed (steps, follow-ons, what was revealed) and errors.

The learner's words are stored verbatim and never paraphrased (principle 4).
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from .core import Workspace

ANNOTATION_KINDS = ("confusion", "gist", "question", "insight", "opinion", "connection")
OPEN_KINDS = ("confusion", "question")
ANCHOR_KINDS = ("step", "concept", "library", "standard", "board", "day")
ERROR_KINDS = ("slip", "arithmetic", "procedure", "concept", "reading", "notation", "setup")


def _read(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return yaml.safe_load(path.read_text(encoding="utf-8")) or default


def _write(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    tmp.replace(path)


class Journal:
    def __init__(self, ws: "Workspace"):
        self.ws = ws

    @property
    def _dir(self) -> Path:
        return self.ws.private / "reflection"

    def _day_file(self, what: str, day: str) -> Path:
        return self._dir / what / f"{day}.yaml"

    # -------------------------------------------------------------- annotations
    def annotate(self, text: str, kind: str = "gist", anchor: str = "day", ref: str = "",
                 project: str = "", step: str = "", responds_to: str = "") -> dict:
        """Keep the learner's words, pinned to something. kind: confusion, gist, question,
        insight, opinion, connection. anchor: step, concept, library, standard, board, day;
        ref names it (a concept id, a library doc id and anchor, a standard code, a board item).
        responds_to: an earlier annotation this answers; an open one becomes resolved."""
        from .core import HarnessError, _now
        if not (text or "").strip():
            raise HarnessError("Nothing to keep yet. Half a thought is fine; it just needs words.")
        if kind not in ANNOTATION_KINDS:
            raise HarnessError(f"kind must be one of {ANNOTATION_KINDS}.")
        if anchor not in ANCHOR_KINDS:
            raise HarnessError(f"anchor must be one of {ANCHOR_KINDS}.")
        if project:
            self.ws._require_project(project)
            if step:
                self.ws._plan_step(project, step)
        if anchor == "concept":
            ref = self.ws.board._slug(ref)
        if anchor == "step" and not (project and step):
            raise HarnessError("A step annotation needs the project and step.")
        t = _now()
        day = t.date().isoformat()
        f = self._day_file("annotations", day)
        prev = None
        if responds_to:
            prev, _, _ = self._find(responds_to)  # check it exists before writing anything
        data = _read(f, {}) or {"schema": 1, "day": day, "items": []}
        aid = f"a-{t.strftime('%Y%m%d-%H%M%S')}-{len(data['items']) + 1}"
        item: dict[str, Any] = {"id": aid, "at": t.isoformat(timespec="minutes"), "kind": kind,
                                "anchor": anchor, "text": text.strip()}
        for k, v in (("ref", ref), ("project", project), ("step", step)):
            if v:
                item[k] = v
        data["items"].append(item)
        _write(f, data)
        self._index(item, f)
        if responds_to:
            item["responds_to"] = responds_to
            _write(f, data)
            prev, pf, pdata = self._find(responds_to)
            if prev.get("kind") in OPEN_KINDS:
                prev["resolved_by"] = aid
                _write(pf, pdata)
                self._index(prev, pf)
        return {"saved": aid, "kind": kind, "open": kind in OPEN_KINDS}

    def _find(self, aid: str) -> tuple[dict, Path, dict]:
        from .core import HarnessError
        for f in sorted((self._dir / "annotations").glob("*.yaml"), reverse=True):
            data = _read(f, {}) or {}
            for it in data.get("items", []):
                if it.get("id") == aid:
                    return it, f, data
        raise HarnessError(f"No annotation {aid!r}.")

    def _index(self, it: dict, f: Path) -> None:
        concepts = [it["ref"]] if it.get("anchor") == "concept" and it.get("ref") else []
        meta = {"scope": "reflection", "author": "learner", "type": it["kind"], "project": it.get("project", ""),
                "step": it.get("step", ""), "concepts": concepts, "date": it["at"][:10],
                "status": "resolved" if it.get("resolved_by") else ("open" if it["kind"] in OPEN_KINDS else "")}
        self.ws.index.upsert(f"annotation:{it['id']}", "annotation", it["text"], meta,
                             str(f.relative_to(self.ws.root)),
                             edges=[("about", f"concept:{c}") for c in concepts])

    def open_questions(self, project: str = "", limit: int = 10) -> dict:
        """Confusions and questions not yet answered by a later annotation, newest first."""
        out = []
        for f in sorted((self._dir / "annotations").glob("*.yaml"), reverse=True):
            for it in reversed((_read(f, {}) or {}).get("items", [])):
                if it["kind"] in OPEN_KINDS and not it.get("resolved_by") and \
                        (not project or it.get("project") == project):
                    out.append(it)
        return {"open": out[:limit], "total": len(out)}

    # ------------------------------------------------------------------- errors
    def record_error(self, project: str, step: str, what: str, kind: str = "slip", helped: str = "",
                     follow_on: str = "") -> dict:
        """A slip the learner agreed to keep: what went sideways, in plain words, and what helped.
        Kept in their notes, in the open; evidence for their own looking back, never a score."""
        from .core import HarnessError, _now
        self.ws._plan_step(project, step)
        if kind not in ERROR_KINDS:
            raise HarnessError(f"kind must be one of {ERROR_KINDS}.")
        if not (what or "").strip():
            raise HarnessError("Say what happened, plainly.")
        t = _now()
        day = t.date().isoformat()
        f = self._day_file("errors", day)
        data = _read(f, {}) or {"schema": 1, "day": day, "items": []}
        eid = f"e-{t.strftime('%Y%m%d-%H%M%S')}-{len(data['items']) + 1}"
        item = {"id": eid, "at": t.isoformat(timespec="minutes"), "project": project, "step": step,
                "kind": kind, "what": what.strip(), "helped": (helped or "").strip()}
        if follow_on:
            item["follow_on"] = follow_on
        data["items"].append(item)
        _write(f, data)
        self.ws.index.upsert(f"error:{eid}", "error", f"{what} {helped}",
                             {"scope": "reflection", "author": "tutor", "type": kind, "project": project,
                              "step": step, "date": day}, str(f.relative_to(self.ws.root)))
        return {"saved": eid}

    def error_patterns(self, project: str = "") -> dict:
        """Counts by kind and by concept, for the organizer and validator-to-mentor consults."""
        from .core import _read_yaml
        by_kind: dict[str, int] = {}
        by_concept: dict[str, int] = {}
        for f in (self._dir / "errors").glob("*.yaml"):
            for it in (_read(f, {}) or {}).get("items", []):
                if project and it.get("project") != project:
                    continue
                by_kind[it["kind"]] = by_kind.get(it["kind"], 0) + 1
                plan = _read_yaml(self.ws.project_dir(it["project"]) / "program.yaml", {}) or {}
                for s in plan.get("steps", []):
                    if s["id"] == it["step"]:
                        for c in s.get("concepts", []):
                            by_concept[c] = by_concept.get(c, 0) + 1
        return {"by_kind": by_kind, "by_concept": dict(sorted(by_concept.items(), key=lambda x: -x[1]))}

    # ------------------------------------------------------------------ journal
    def journal(self, since: str = "", until: str = "", project: str = "", write: bool = False) -> dict:
        """Look back: per day, newest first, everything the learner did and said. since/until are
        ISO dates (default: the last 14 days). write=true also saves it as a Markdown file in
        .private/journal/ for the learner to open."""
        from .core import _read_yaml
        today = _dt.date.today()
        since = since or (today - _dt.timedelta(days=13)).isoformat()
        until = until or today.isoformat()
        days: dict[str, dict[str, list]] = {}

        def day(d: str) -> dict:
            return days.setdefault(d, {k: [] for k in ("annotations", "responses", "content", "standards",
                                                        "exercises", "errors", "diary")})

        def in_range(d: str) -> bool:
            return since <= d <= until

        def proj_ok(p: str) -> bool:
            return not project or p == project

        for kind in ("annotations", "errors"):
            for f in sorted((self._dir / kind).glob("*.yaml")):
                if not in_range(f.stem):
                    continue
                for it in (_read(f, {}) or {}).get("items", []):
                    if proj_ok(it.get("project", "")) or (kind == "annotations" and not it.get("project")):
                        day(f.stem)[kind].append(it)

        plans: dict[str, dict] = {}

        def plan(p: str) -> dict:
            if p not in plans:
                plans[p] = _read_yaml(self.ws.project_dir(p) / "program.yaml", {}) or {}
            return plans[p]

        def step_of(p: str, s: str) -> dict:
            return next((x for x in plan(p).get("steps", []) if x.get("id") == s), {})

        touched: dict[str, set] = {}
        att_root = self.ws.private / "attempts"
        for f in sorted(att_root.glob("*/*/*.md")) if att_root.exists() else []:
            p, s = f.parent.parent.name, f.parent.name
            d = f.name[:10]  # attempt files are named <stamp>[-<follow-on>].md
            if not in_range(d) or not proj_ok(p):
                continue
            fo = f.stem[24:] if len(f.stem) > 23 else ""
            day(d)["responses"].append({"project": p, "step": s, "text": f.read_text(encoding="utf-8").strip(),
                                        **({"follow_on": fo} if fo else {}), "file": str(f.relative_to(self.ws.root))})
            touched.setdefault(d, set()).add((p, s))
        hand = self.ws.private / "handoff"
        for f in sorted(hand.glob("*/*/defense-2*.md")) if hand.exists() else []:
            p, s = f.parent.parent.name, f.parent.name
            d = f.stem[8:18]
            if in_range(d) and proj_ok(p):
                day(d)["responses"].append({"project": p, "step": s, "defense": True,
                                            "text": f.read_text(encoding="utf-8").strip()})
                touched.setdefault(d, set()).add((p, s))

        base = self.ws.root / "projects"
        for pdir in sorted(base.iterdir()) if base.exists() else []:
            if not proj_ok(pdir.name):
                continue
            prog = (_read_yaml(pdir / "progress.yaml", {}) or {}).get("steps", {})
            for sid, st in prog.items():
                for ev in st.get("seen_log", []):
                    d = str(ev.get("at", ""))[:10]
                    if in_range(d):
                        day(d)["exercises"].append({"project": pdir.name, "step": sid, "saw": ev.get("what"),
                                                    **({"follow_on": ev["follow_on"]} if ev.get("follow_on") else {})})
                        touched.setdefault(d, set()).add((pdir.name, sid))

        cites: dict[str, list] = {}
        with self.ws.index._conn() as c:
            for src, meta in c.execute("SELECT e.src, d.meta FROM edges e JOIN docs d ON d.id = e.dst "
                                       "WHERE e.rel = 'cites'").fetchall():
                cites.setdefault(src.removeprefix("concept:"), []).append(json.loads(meta).get("code"))
        for d, pairs in touched.items():
            codes: set[str] = set()
            for p, s in sorted(pairs):
                st = step_of(p, s)
                day(d)["content"].append({"project": p, "step": s, "does": st.get("does", ""),
                                          "concepts": st.get("concepts", [])})
                codes |= set(st.get("standards_cited", []))
                for cpt in st.get("concepts", []):
                    codes |= {x for x in cites.get(cpt, []) if x}
            day(d)["standards"] = sorted(codes)
            day(d)["exercises"] = [{"project": p, "step": s, "does": step_of(p, s).get("does", ""),
                                    "attempts": sum(1 for r in day(d)["responses"]
                                                    if r["project"] == p and r["step"] == s and not r.get("defense"))}
                                   for p, s in sorted(pairs)] + day(d)["exercises"]

        k = self.ws.knowledge._state()
        for doc_id, it in k.get("items", {}).items():
            for u in it.get("uses", []):
                d, _, how = u.partition(" ")
                if in_range(d) and doc_id.startswith("library:"):
                    doc = self.ws.index.doc(doc_id)
                    day(d)["content"].append({"library": doc_id, "title": (doc or {}).get("meta", {}).get("title", ""),
                                              "how": how})
        dia = self.ws.private / "diary"
        for f in sorted(dia.rglob("*.md")) if dia.exists() else []:
            d = f.name[:10]
            if in_range(d):
                day(d)["diary"].append(f.read_text(encoding="utf-8").split("---\n", 2)[-1].strip())

        ordered = [{"day": d, **v} for d, v in sorted(days.items(), reverse=True)
                   if any(v[x] for x in v)]
        out: dict[str, Any] = {"since": since, "until": until, "days": ordered,
                               "open_questions": self.open_questions(project)["open"][:5]}
        if write:
            out["file"] = self._write_markdown(out, project)
        return out

    def _write_markdown(self, j: dict, project: str) -> str:
        lines = [f"# Looking back{': ' + project if project else ''}", "",
                 f"_{j['since']} to {j['until']}. Your words are as you wrote them._", ""]
        if j["open_questions"]:
            lines += ["## Still open", ""] + [f"- {q['text']} ({q['at'][:10]})" for q in j["open_questions"]] + [""]
        for d in j["days"]:
            lines += [f"## {d['day']}", ""]
            if d["content"]:
                lines += ["**Covered**"] + [f"- {c.get('does') or c.get('title')}" for c in d["content"]] + [""]
            if d["standards"]:
                lines += [f"**Standards touched:** {', '.join(d['standards'])}", ""]
            if d["annotations"]:
                lines += ["**Your notes**"]
                for a in d["annotations"]:
                    tag = " (answered later)" if a.get("resolved_by") else ""
                    lines.append(f"- _{a['kind']}_: {a['text']}{tag}")
                lines.append("")
            if d["responses"]:
                lines += ["**What you worked out**"]
                lines += [f"- {'Defense of ' if r.get('defense') else ''}{r['step']}: "
                          f"{r['text'][:300]}{'…' if len(r['text']) > 300 else ''}" for r in d["responses"]]
                lines.append("")
            ex = [e for e in d["exercises"] if e.get("saw")]
            if ex:
                lines += ["**Looked at**"] + [f"- {e['step']}: the {e['saw']}" for e in ex] + [""]
            if d["errors"]:
                lines += ["**Where it went sideways, and what helped**"]
                lines += [f"- {e['what']}" + (f" → {e['helped']}" if e.get("helped") else "") for e in d["errors"]]
                lines.append("")
            if d["diary"]:
                lines += ["**Diary**"] + [f"> {x}" for x in d["diary"]] + [""]
        path = self.ws.private / "journal" / f"{j['until']}{'-' + project if project else ''}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return str(path.relative_to(self.ws.root))
