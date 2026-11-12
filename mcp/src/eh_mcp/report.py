"""Progress reports, written through Dewey's lens.

The server gathers evidence; the mentor writes the report in plain words and saves it.
Dewey's test of an experience is whether it leads to further growth (continuity) and
whether it joins the learner to others (interaction). So the evidence covers:

- growth: what was built, confusions the learner later answered in their own words,
  slips that eased on a concept, reliance on reveals over time, defenses given;
- strengths: quoted from the learner's own annotations and responses, with the
  Mathematical Practices (MP1-MP8) the work touched, as reference points only;
- sociability: moments the learner shared the work (explained it, worked with
  someone, helped someone), recorded only when they mention one;
- opportunities: open questions, concepts with repeated slips, next steps on the arc,
  framed as the next experiences worth having, never as deficits;
- where it leads: the arc's goal and why, and who the work could help.

No grades, scores, rankings or comparisons with anyone else (principle 4).
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from .core import Workspace

SHARE_KINDS = ("explained", "worked-with", "helped", "asked", "showed", "heard-back")
PRACTICES = {f"MP{i}" for i in range(1, 9)}


def _read(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return yaml.safe_load(path.read_text(encoding="utf-8")) or default


class Reports:
    def __init__(self, ws: "Workspace"):
        self.ws = ws

    @property
    def _dir(self) -> Path:
        return self.ws.private / "reports"

    # ----------------------------------------------------------------- sharing
    def record_shared(self, how: str, text: str, who: str = "", project: str = "", step: str = "") -> dict:
        """A moment the learner shared the work: explained it to someone, worked with someone,
        helped someone, asked someone, showed it. Only when the learner mentions one. who is a
        relationship ('my sister', 'a coworker'), never a name or details about the person."""
        from .core import HarnessError
        if how not in SHARE_KINDS:
            raise HarnessError(f"how must be one of {SHARE_KINDS}.")
        r = self.ws.journal.annotate(text, kind="connection", anchor="step" if (project and step) else "day",
                                     project=project, step=step)
        aid = r["saved"]
        it, f, data = self.ws.journal._find(aid)
        it["shared"] = {"how": how, **({"who": who.strip()} if who.strip() else {})}
        from .journal import _write
        _write(f, data)
        return {"saved": aid, "shared": it["shared"]}

    # ---------------------------------------------------------------- evidence
    def report_evidence(self, since: str = "", until: str = "", project: str = "", arc: str = "") -> dict:
        """Everything a progress report rests on, for the period (default: since the last
        report, or the last 30 days)."""
        from .core import _read_yaml
        today = _dt.date.today()
        last = self.list_reports()["reports"]
        since = since or (last[0]["until"] if last else (today - _dt.timedelta(days=30)).isoformat())
        until = until or today.isoformat()
        j = self.ws.journal.journal(since, until, project)
        days = j["days"]

        notes = [a for d in days for a in d["annotations"]]
        resolved = []
        for a in notes:
            if a.get("responds_to"):
                try:
                    prev, _, _ = self.ws.journal._find(a["responds_to"])
                    resolved.append({"then": prev["text"], "then_at": prev["at"][:10],
                                     "now": a["text"], "now_at": a["at"][:10]})
                except Exception:
                    pass
        shared = [{"how": a["shared"]["how"], "who": a["shared"].get("who", ""), "text": a["text"],
                   "at": a["at"][:10]} for a in notes if a.get("shared")]

        built, defended, hints, reveals = [], [], [], {"hint": 0, "answer": 0, "method": 0}
        base = self.ws.root / "projects"
        for pdir in sorted(base.iterdir()) if base.exists() else []:
            if project and pdir.name != project:
                continue
            plan = _read_yaml(pdir / "program.yaml", {}) or {}
            prog = (_read_yaml(pdir / "progress.yaml", {}) or {}).get("steps", {})
            for s in plan.get("steps", []):
                st = prog.get(s["id"], {})
                if st.get("status") in ("drafted", "defended"):
                    built.append({"project": pdir.name, "step": s["id"], "does": s["does"],
                                  "status": st["status"], "concepts": s.get("concepts", [])})
                if st.get("status") == "defended":
                    defended.append({"project": pdir.name, "step": s["id"], "does": s["does"]})
                for ev in st.get("seen_log", []):
                    if since <= str(ev.get("at", ""))[:10] <= until:
                        reveals[ev["what"]] = reveals.get(ev["what"], 0) + 1
                if st.get("attempts"):
                    hints.append(st.get("hints_given", 0))

        errs = [e for d in days for e in d["errors"]]
        mid = since if not days else days[len(days) // 2]["day"]
        early = [e for e in errs if e["at"][:10] < mid]
        late = [e for e in errs if e["at"][:10] >= mid]

        def by_kind(es: list) -> dict:
            out: dict[str, int] = {}
            for e in es:
                out[e["kind"]] = out.get(e["kind"], 0) + 1
            return out

        standards = sorted({s for d in days for s in d["standards"]})
        practices = sorted({s for s in standards if s in PRACTICES})
        with self.ws.index._conn() as c:
            texts = {}
            import json
            for code in practices:
                r = c.execute("SELECT meta FROM docs WHERE kind = 'standard' AND body LIKE ?",
                              (f"{code} %",)).fetchone()
                if r:
                    texts[code] = json.loads(r[0]).get("statement", "")
        from .lenses import LENSES, lens_for
        arcs = self.ws.orient._arcs()
        key = arc and self.ws.orient._resolve_arc(arc)
        if not key and project:
            key = next((k for k, v in arcs.items() if any(i.get("project") == project for i in v.get("path", []))), None)
        if not key and len(arcs) == 1:
            key = next(iter(arcs))
        here = self.ws.orient.where_am_i(focus=key or project or "")
        arc = arcs.get(key, {}) if key else {}
        lens = lens_for(arc) if arc else ("math" if practices else "general")
        return {
            "period": {"since": since, "until": until, "active_days": len(days)},
            "arc": key or "",
            "lens": {"name": lens, **LENSES[lens]},
            "where_it_leads": {"goal": arc.get("goal"), "why": arc.get("why"),
                               "path": (here.get("arc") or {}).get("path", [])},
            "growth": {
                "built": built, "defended": defended,
                "confusions_answered": resolved,
                "slips": {"earlier": by_kind(early), "later": by_kind(late)},
                "looked_at": reveals,
                "hints_per_worked_step": round(sum(hints) / len(hints), 1) if hints else None,
            },
            "strengths_evidence": {
                "your_words": [{"kind": a["kind"], "text": a["text"], "at": a["at"][:10]}
                               for a in notes if a["kind"] in ("insight", "connection", "gist", "opinion")][:12],
                "responses": [{"step": r["step"], "text": r["text"][:400], "defense": r.get("defense", False)}
                              for d in days for r in d["responses"]][:8],
                "practices_touched": [{"code": k, "text": texts.get(k, "")} for k in practices] if lens == "math" else [],
            },
            "sociability": {"shared": shared, "count": len(shared),
                            "works_alone": (_read_yaml(self.ws.private / "learner.yaml", {}) or {}).get("works_alone")},
            "opportunities": {
                "still_open": [{"text": q["text"], "at": q["at"][:10]} for q in j["open_questions"]],
                "concepts_with_repeated_slips": {k: v for k, v in
                                                 self.ws.journal.error_patterns(project)["by_concept"].items() if v >= 2},
                "next": (here.get("current") or {}).get("now"),
                "next_on_arc": next((p["title"] for p in (here.get("arc") or {}).get("path", [])
                                     if p["state"] in ("not started", "planned")), None),
            },
            "retrospectives": [{"at": r["at"][:10], "project": r.get("project"), "answers": r["answers"]}
                               for r in self.ws.share.retrospectives(since, until, project)],
            "share_out": ({"audience": (self.ws.share.get_share(project) or {}).get("audience"),
                           "shared": self.ws.share.get_share(project)["shared"],
                           "heard_back": self.ws.share.get_share(project)["heard_back"]} if project else None),
            "standards_touched": standards,
            "attribution": "Knowledge Graph is provided by CZI-E under the CC BY-4.0 license. CZI-E received "
                           "state standards and written permission under CC BY-4.0 from 1EdTech." if standards else "",
        }

    # ------------------------------------------------------------------ saving
    def save_report(self, text: str, since: str, until: str, project: str = "", title: str = "") -> dict:
        """Save the report the mentor wrote and the learner has read, as Markdown in .private/reports/."""
        from .core import HarnessError, _slug
        if not (text or "").strip():
            raise HarnessError("The report is empty.")
        name = f"{until}{'-' + _slug(project) if project else ''}.md"
        path = self._dir / name
        n = 2
        while path.exists():
            path = path.with_name(f"{name[:-3]}-{n}.md")
            n += 1
        head = f"---\nsince: {since}\nuntil: {until}\nproject: {project}\ntitle: {title or 'Progress report'}\n---\n\n"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(head + text.strip() + "\n", encoding="utf-8")
        rel = str(path.relative_to(self.ws.root))
        self.ws.index.upsert(f"report:{path.stem}", "report", text,
                             {"scope": "reflection", "author": "mentor", "project": project, "date": until,
                              "title": title or "Progress report"}, rel)
        return {"saved": rel}

    def list_reports(self) -> dict:
        out = []
        for f in sorted(self._dir.glob("*.md"), reverse=True) if self._dir.exists() else []:
            head = f.read_text(encoding="utf-8").split("---\n")
            meta = yaml.safe_load(head[1]) if len(head) > 2 else {}
            out.append({"file": str(f.relative_to(self.ws.root)), "since": str(meta.get("since", "")),
                        "until": str(meta.get("until", "")), "project": meta.get("project") or "",
                        "title": meta.get("title", "")})
        return {"reports": out}
