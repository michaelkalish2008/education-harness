"""The learner's library: a knowledge base for areas of interest.

Design ported from cat (the context layer):
- The summary is the durable artifact; vectors are a disposable cache rebuilt from it.
- Records are keyed by a SHA-256 of the file's content and frozen per hash: a version
  is summarized once. A changed file becomes 'stale' until the archivist writes a new
  summary; a missing file drops out of search.
- Two-hop search: hop 1 ranks summaries (plus a literal-match list over the original
  files, decisive only when the pattern is selective); hop 2 opens the 1-3 originals
  by path. Long documents carry a section map so hop 2 opens the right part.
- Flags (pii, secrets) are deterministic functions of the content, never the model's say.

Originals stay where the learner keeps them; records live in .private/library/.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from . import derive

if TYPE_CHECKING:
    from .core import Workspace

SCHEMA = 1
MAX_TEXT_BYTES = 5_000_000          # literal search and flags read text files up to this size
GREP_RRF_K = 10                     # decisive constant for a selective literal pattern (cat)
GREP_SELECTIVITY_MAX = 40           # the match-count gate that earns it (cat)
PLACEHOLDER = "placeholder"


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_text(path: Path) -> str | None:
    if not derive.is_text(path) or path.stat().st_size > MAX_TEXT_BYTES:
        return None
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


class Library:
    def __init__(self, ws: "Workspace"):
        self.ws = ws

    @property
    def dir(self) -> Path:
        return self.ws.private / "library"

    def _record_path(self, rid: str) -> Path:
        return self.dir / f"{rid}.yaml"

    def _records(self) -> list[dict]:
        if not self.dir.exists():
            return []
        return [yaml.safe_load(p.read_text(encoding="utf-8")) for p in sorted(self.dir.glob("*.yaml"))]

    @staticmethod
    def _id_for(path: Path) -> str:
        return "d" + hashlib.sha256(str(path).encode()).hexdigest()[:12]

    # ---------------------------------------------------------------- add
    def add(self, path: str, area: str, tags: list[str] | None = None, concepts: list[str] | None = None,
            recursive: bool = True) -> dict:
        """Register a file or a folder of files. Each gets a placeholder record until the
        archivist writes its summary. Nothing is copied or written next to the originals."""
        from .core import HarnessError, _check_name
        _check_name(area, "area")
        root = Path(path).expanduser().resolve()
        if not root.exists():
            raise HarnessError(f"Nothing at {root}.")
        files = [root] if root.is_file() else sorted(
            p for p in (root.rglob("*") if recursive else root.glob("*"))
            if p.is_file() and not any(part.startswith(".") for part in p.relative_to(root).parts))
        files = [f for f in files if derive.kind_of(f) != "other"]
        if not files:
            raise HarnessError("No readable documents there (text, markdown, PDF, Word, notebooks...).")
        self.ws.ensure_workspace()
        added, unchanged = [], []
        for f in files:
            rid = self._id_for(f)
            existing = self._load(rid)
            h = file_hash(f)
            if existing and existing["hash"] == h:
                unchanged.append(rid)
                continue
            text = read_text(f)
            rec = {
                "schema": SCHEMA, "id": rid, "path": str(f), "hash": h,
                "title": existing.get("title", f.stem) if existing else f.stem,
                "area": area, "tags": sorted(set(tags or [])), "concepts": sorted(set(concepts or [])),
                "summary": PLACEHOLDER, "sections": [],
                "flags": derive.derive(f, text), "status": "needs summary",
                "pins": {"gen": None, "derive": derive.DERIVE_VERSION},
                "added": (existing or {}).get("added") or _dt.date.today().isoformat(),
            }
            self._save(rec)
            added.append({"id": rid, "path": str(f), "type": rec["flags"]["type"],
                          "pii": rec["flags"]["pii"]})
        return {"needs_summary": added, "unchanged": len(unchanged),
                "next": "Read each original and save a summary with write_library_summary."}

    def write_summary(self, rid: str, title: str, summary: str, sections: list[dict] | None = None,
                      model: str = "", tags: list[str] | None = None, concepts: list[str] | None = None) -> dict:
        """Archivist: save the summary for the current version of a document.
        sections: [{heading, anchor, summary?}] for long documents (anchor = line or page)."""
        from .core import HarnessError
        rec = self._load(rid)
        if not rec:
            raise HarnessError(f"No library record {rid}.")
        p = Path(rec["path"])
        if not p.exists():
            raise HarnessError(f"The original is gone: {p}.")
        if file_hash(p) != rec["hash"]:
            raise HarnessError("The file changed since it was registered; run check_library first.")
        if rec["summary"] != PLACEHOLDER and rec["status"] == "summarized":
            raise HarnessError("This version already has a summary (records are frozen per version).")
        words = len((summary or "").split())
        if not 10 <= words <= 200:
            raise HarnessError("A summary should be 10 to 200 words, in your own words.")
        clean_sections = []
        for s in sections or []:
            if not str(s.get("heading", "")).strip() or s.get("anchor") in (None, ""):
                raise HarnessError("Each section needs a heading and an anchor (a line or page number).")
            clean_sections.append({"heading": s["heading"], "anchor": s["anchor"],
                                   "summary": s.get("summary", "")})
        rec.update({"title": title or rec["title"], "summary": summary.strip(), "sections": clean_sections,
                    "status": "summarized", "pins": {**rec["pins"], "gen": model or "unspecified"}})
        if tags:
            rec["tags"] = sorted(set(rec["tags"]) | set(tags))
        if concepts:
            rec["concepts"] = sorted(set(rec["concepts"]) | set(concepts))
        self._save(rec)
        return {"saved": rid, "status": "summarized"}

    def check(self) -> dict:
        """Hash-monitor every registered original: changed -> stale (needs a new summary),
        gone -> missing (out of search), flags re-derived when the rules version moved."""
        stale, missing, ok = [], [], 0
        for rec in self._records():
            p = Path(rec["path"])
            if not p.exists():
                if rec["status"] != "missing":
                    rec["status"] = "missing"
                    self._save(rec)
                missing.append({"id": rec["id"], "path": rec["path"]})
                continue
            h = file_hash(p)
            changed = False
            if h != rec["hash"]:
                rec.update({"hash": h, "status": "stale", "flags": derive.derive(p, read_text(p))})
                changed = True
            elif rec["pins"].get("derive") != derive.DERIVE_VERSION:
                rec["flags"] = derive.derive(p, read_text(p))
                rec["pins"]["derive"] = derive.DERIVE_VERSION
                changed = True
            elif rec["status"] == "missing":
                rec["status"] = "summarized" if rec["summary"] != PLACEHOLDER else "needs summary"
                changed = True
            if changed:
                self._save(rec)
            if rec["status"] in ("stale", "needs summary"):
                stale.append({"id": rec["id"], "path": rec["path"], "status": rec["status"]})
            else:
                ok += 1
        return {"up_to_date": ok, "need_summary": stale, "missing": missing}

    def list(self, area: str | None = None) -> dict:
        recs = [r for r in self._records() if not area or r["area"] == area]
        return {"documents": [{"id": r["id"], "title": r["title"], "area": r["area"], "status": r["status"],
                               "path": r["path"]} for r in recs],
                "areas": sorted({r["area"] for r in self._records()})}

    # ------------------------------------------------------------- search
    def grep(self, pattern: str, doc_ids_allowed: set[str] | None = None, limit: int = 200) -> list[str]:
        """Literal recall over the original text files (the summary-independent list, as in cat)."""
        try:
            rx = re.compile(pattern, re.IGNORECASE)
        except re.error:
            rx = re.compile(re.escape(pattern), re.IGNORECASE)
        counts = []
        for rec in self._records():
            if rec["status"] == "missing":
                continue
            doc_id = f"lib:{rec['id']}"
            if doc_ids_allowed is not None and doc_id not in doc_ids_allowed:
                continue
            p = Path(rec["path"])
            text = read_text(p) if p.exists() else None
            if text:
                n = len(rx.findall(text))
                if n:
                    counts.append((n, doc_id))
        counts.sort(reverse=True)
        return [d for _, d in counts[:limit]]

    # ------------------------------------------------------------ storage
    def _load(self, rid: str) -> dict | None:
        p = self._record_path(rid)
        return yaml.safe_load(p.read_text(encoding="utf-8")) if p.exists() else None

    def _save(self, rec: dict) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        p = self._record_path(rec["id"])
        tmp = p.with_suffix(".tmp")
        tmp.write_text(yaml.safe_dump(rec, sort_keys=False, allow_unicode=True), encoding="utf-8")
        tmp.replace(p)
        self.index_record(rec)

    def index_record(self, rec: dict) -> None:
        doc_id = f"lib:{rec['id']}"
        if rec["status"] == "missing":
            self.ws.index.remove(doc_id)
            return
        summary = "" if rec["summary"] == PLACEHOLDER else rec["summary"]
        sections = " ".join(f"{s['heading']}. {s.get('summary', '')}" for s in rec.get("sections", []))
        body = " ".join(x for x in (rec["title"], summary, sections) if x)
        meta: dict[str, Any] = {"area": rec["area"], "tags": rec["tags"], "concepts": rec["concepts"],
                                "type": rec["flags"]["type"], "date": rec["added"], "path": rec["path"],
                                "title": rec["title"], "pii": rec["flags"]["pii"], "status": rec["status"]}
        if rec.get("sections"):
            meta["sections"] = [{"heading": s["heading"], "anchor": s["anchor"]} for s in rec["sections"]]
        edges = [("in_area", f"area:{rec['area']}")] + [("about", f"concept:{c}") for c in rec["concepts"]]
        self.ws.index.upsert(doc_id, "library", body, meta, rec["path"], edges)
