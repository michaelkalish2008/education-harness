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
import html
import ipaddress
import re
import socket
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
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
MAX_URL_BYTES = 2_000_000
MAX_URL_TEXT = 500_000
TOOL_CONTENT_LIMIT = 60_000


class _PageText(HTMLParser):
    """Small dependency-free HTML-to-text extractor for public lesson sources."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip = 0
        self.parts: list[str] = []
        self.title_parts: list[str] = []
        self.in_title = False

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in {"script", "style", "noscript", "svg"}:
            self.skip += 1
        if tag == "title":
            self.in_title = True
        if tag in {"p", "div", "section", "article", "li", "br", "h1", "h2", "h3", "h4", "tr"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg"} and self.skip:
            self.skip -= 1
        if tag == "title":
            self.in_title = False
        if tag in {"p", "div", "section", "article", "li", "h1", "h2", "h3", "h4", "tr"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self.skip:
            return
        if self.in_title:
            self.title_parts.append(data)
        self.parts.append(data)

    def result(self) -> tuple[str, str]:
        title = " ".join(" ".join(self.title_parts).split())
        lines = [" ".join(line.split()) for line in "".join(self.parts).splitlines()]
        return title, "\n".join(line for line in lines if line)


def _assert_public_url(url: str) -> str:
    from .core import HarnessError
    parsed = urllib.parse.urlsplit((url or "").strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise HarnessError("Use a public http(s) URL without embedded credentials.")
    try:
        default_port = 443 if parsed.scheme == "https" else 80
        addresses = {row[4][0] for row in socket.getaddrinfo(parsed.hostname, parsed.port or default_port)}
    except socket.gaierror as exc:
        raise HarnessError(f"Could not resolve that URL: {type(exc).__name__}.") from exc
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if not ip.is_global:
            raise HarnessError("The URL must resolve to a public internet address.")
    return urllib.parse.urlunsplit(parsed)


def fetch_public_page(url: str, timeout: float = 15.0) -> dict:
    """Fetch public HTML/plain text with a size cap; never fetch private-network URLs."""
    from .core import HarnessError
    safe_url = _assert_public_url(url)
    req = urllib.request.Request(safe_url, headers={"User-Agent": "education-harness/0.9 (+lesson-source)"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            final_url = _assert_public_url(response.geturl())
            content_type = response.headers.get_content_type().lower()
            if content_type not in {"text/html", "text/plain", "text/markdown"}:
                raise HarnessError(f"That URL returned unsupported content ({content_type}); use a public HTML or text page.")
            raw = response.read(MAX_URL_BYTES + 1)
            if len(raw) > MAX_URL_BYTES:
                raise HarnessError("That page is too large to use as a lesson source (2 MB maximum).")
            charset = response.headers.get_content_charset() or "utf-8"
    except urllib.error.HTTPError as exc:
        raise HarnessError(f"The public page could not be opened (HTTP {exc.code}).") from exc
    except urllib.error.URLError as exc:
        raise HarnessError(f"The public page could not be opened ({type(exc.reason).__name__}).") from exc
    decoded = raw.decode(charset, errors="replace")
    if content_type == "text/html":
        parser = _PageText()
        parser.feed(decoded)
        title, text = parser.result()
    else:
        title, text = "", html.unescape(decoded)
    text = text[:MAX_URL_TEXT].strip()
    if len(text.split()) < 10:
        raise HarnessError("The URL did not expose enough public text to inform a lesson plan.")
    return {"url": final_url, "title": title, "text": text, "content_type": content_type}


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

    @staticmethod
    def _id_for_url(url: str) -> str:
        return "u" + hashlib.sha256(url.encode()).hexdigest()[:12]

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

    def add_url(self, url: str, area: str, tags: list[str] | None = None,
                concepts: list[str] | None = None) -> dict:
        """Capture the text publicly exposed by a URL as a versioned lesson source."""
        from .core import _check_name
        _check_name(area, "area")
        page = fetch_public_page(url)
        self.ws.ensure_workspace()
        rid = self._id_for_url(page["url"])
        source_dir = self.dir / "sources"
        source_dir.mkdir(parents=True, exist_ok=True)
        snapshot = source_dir / f"{rid}.txt"
        content = f"Source: {page['url']}\nTitle: {page['title']}\n\n{page['text']}\n"
        h = hashlib.sha256(content.encode()).hexdigest()
        existing = self._load(rid)
        if not snapshot.exists() or snapshot.read_text(encoding="utf-8", errors="replace") != content:
            snapshot.write_text(content, encoding="utf-8")
        unchanged = bool(existing and existing.get("hash") == h)
        rec = existing if unchanged else {
            "schema": SCHEMA, "id": rid, "path": str(snapshot), "url": page["url"], "hash": h,
            "title": page["title"] or urllib.parse.urlsplit(page["url"]).hostname,
            "area": area, "tags": sorted(set(tags or [])), "concepts": sorted(set(concepts or [])),
            "summary": PLACEHOLDER, "sections": [],
            "flags": derive.derive(snapshot, content), "status": "needs summary",
            "pins": {"gen": None, "derive": derive.DERIVE_VERSION},
            "added": (existing or {}).get("added") or _dt.date.today().isoformat(),
        }
        if unchanged:
            rec.update({"area": area, "tags": sorted(set(rec.get("tags", [])) | set(tags or [])),
                        "concepts": sorted(set(rec.get("concepts", [])) | set(concepts or []))})
        self._save(rec)
        shown = page["text"][:TOOL_CONTENT_LIMIT]
        return {"source": {"id": rid, "url": page["url"], "title": rec["title"], "content": shown,
                           "truncated": len(page["text"]) > len(shown), "status": rec["status"],
                           "accessed_on": _dt.date.today().isoformat()},
                "unchanged": unchanged,
                "next": "Use only the exposed content, then save a 10-200 word summary and cite this URL in the plan."}

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
                               "path": r["path"], **({"url": r["url"]} if r.get("url") else {})} for r in recs],
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
        if rec.get("url"):
            meta["url"] = rec["url"]
        if rec.get("sections"):
            meta["sections"] = [{"heading": s["heading"], "anchor": s["anchor"]} for s in rec["sections"]]
        edges = [("in_area", f"area:{rec['area']}")] + [("about", f"concept:{c}") for c in rec["concepts"]]
        self.ws.index.upsert(doc_id, "library", body, meta, rec["path"], edges)
