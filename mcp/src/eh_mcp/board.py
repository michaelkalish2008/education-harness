"""What the learner knows about a concept, in their own words.

- Recall: the learner's own notes on a concept ("remember this"), kept in
  ``.private/concepts/<concept>.yaml`` and indexed. ``recall`` gathers them with the
  learnings, the steps where the concept appeared, its prerequisites and the standards
  it touches, so "what do I know about the chain rule?" has one answer.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from .core import Workspace



def _read(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return yaml.safe_load(path.read_text(encoding="utf-8")) or default


def _write(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    tmp.replace(path)


class Board:
    def __init__(self, ws: "Workspace"):
        self.ws = ws

    # ------------------------------------------------------------------- recall
    def _concept_file(self, slug: str) -> Path:
        return self.ws.private / "concepts" / f"{slug}.yaml"

    def _names(self) -> dict[str, str]:
        """Program concept ids -> names, so 'chain rule' finds 'chain-rule'."""
        from .core import PROGRAMS
        out = {}
        for f in PROGRAMS.glob("*/track.yaml"):
            for idea in (_read(f, {}) or {}).get("ideas", []):
                for c in idea.get("concepts", []):
                    out[c["id"]] = c["name"]
        return out

    def _slug(self, concept: str) -> str:
        from .core import HarnessError, _slug
        if not (concept or "").strip():
            raise HarnessError("Name the concept, e.g. 'chain rule'.")
        names = self._names()
        s = _slug(concept)
        if s in names:
            return s
        low = concept.strip().lower()
        for article in ("the ", "a ", "an "):
            low = low.removeprefix(article)
        if _slug(low) in names:
            return _slug(low)
        for cid, name in names.items():  # a whole name, or two or more words of its start
            n = name.lower()
            if low == n or (len(low.split()) >= 2 and n.startswith(low)):
                return cid
        return s

    def remember(self, concept: str, text: str, project: str = "", step: str = "") -> dict:
        """Keep what the learner understands about a concept, in their words."""
        from .core import HarnessError, _now
        if not (text or "").strip():
            raise HarnessError("Nothing to remember yet: what does the learner want to keep, in their words?")
        slug = self._slug(concept)
        f = self._concept_file(slug)
        data = _read(f, {}) or {"schema": 1, "concept": slug,
                                "name": self._names().get(slug, concept.strip()), "notes": []}
        note = {"at": _now().isoformat(timespec="minutes"), "text": text.strip()}
        if project:
            note["project"] = project
        if step:
            note["step"] = step
        data["notes"].append(note)
        _write(f, data)
        self._index_concept(data, f)
        return {"saved": str(f.relative_to(self.ws.root)), "concept": slug, "notes": len(data["notes"])}

    def _index_concept(self, data: dict, f: Path) -> None:
        body = data.get("name", "") + ". " + " ".join(n["text"] for n in data.get("notes", []))
        self.ws.index.upsert(f"concept-note:{data['concept']}", "concept_note", body,
                             {"concepts": [data["concept"]], "title": data.get("name"), "scope": "reflection", "author": "learner",
                              "date": data["notes"][-1]["at"][:10] if data.get("notes") else ""},
                             str(f.relative_to(self.ws.root)), edges=[("about", f"concept:{data['concept']}")])

    def recall(self, concept: str) -> dict:
        """Everything the learner has on a concept, newest first: their notes, learnings, the
        steps where it came up (with status), prerequisites, and standards it touches."""
        from .core import _read_yaml
        slug = self._slug(concept)
        names = self._names()
        data = _read(self._concept_file(slug), {}) or {}
        out: dict[str, Any] = {"concept": slug, "name": data.get("name") or names.get(slug, concept),
                               "your_notes": list(reversed(data.get("notes", [])))[:5]}
        learn = []
        for p in sorted((self.ws.private / "learnings").rglob("*.yaml"), reverse=True):
            d = _read_yaml(p, {}) or {}
            if d.get("concept") == slug or slug in ((d.get("tags") or {}).get("concept") or []):
                learn.append({"what_happened": d.get("what_happened"), "format": d.get("format"),
                              "project": p.parent.name, "step": d.get("step")})
        out["learnings"] = learn[:5]
        seen_in = []
        base = self.ws.root / "projects"
        for d in sorted(base.iterdir()) if base.exists() else []:
            plan = _read_yaml(d / "program.yaml", {}) or {}
            prog = (_read_yaml(d / "progress.yaml", {}) or {}).get("steps", {})
            for s in plan.get("steps", []):
                if slug in s.get("concepts", []):
                    seen_in.append({"project": d.name, "step": s["id"], "does": s.get("does"),
                                    "status": prog.get(s["id"], {}).get("status", "not started")})
        out["seen_in"] = seen_in
        out["builds_on"] = [{"concept": c, "name": names.get(c, c),
                             "you_have_notes": self._concept_file(c).exists()}
                            for c in sorted(self.ws.index.prerequisites({f"concept:{slug}"}))]
        with self.ws.index._conn() as c:
            rows = c.execute("SELECT d.meta FROM edges e JOIN docs d ON d.id = e.dst "
                             "WHERE e.src = ? AND e.rel = 'cites'", (f"concept:{slug}",)).fetchall()
        import json
        out["standards"] = sorted({json.loads(r[0]).get("code") for r in rows} - {None})
        if not (out["your_notes"] or learn or seen_in):
            out["note"] = "Nothing yet on this concept. Offer to work it out together, or to keep a note."
        return out

    def list_concepts(self) -> dict:
        d = self.ws.private / "concepts"
        items = []
        for f in sorted(d.glob("*.yaml")) if d.exists() else []:
            c = _read(f, {}) or {}
            items.append({"concept": c.get("concept"), "name": c.get("name"), "notes": len(c.get("notes", [])),
                          "last": (c.get("notes") or [{}])[-1].get("at", "")})
        items.sort(key=lambda x: x["last"], reverse=True)
        return {"concepts": items}
