"""Expectation sets: standards that come from somewhere other than the shared math standards.

- external: set for the learner by someone else (a class syllabus, a grade's expectations, a
  degree program's learning outcomes, a certification blueprint, an employer's competency matrix).
- personal: standards the learner holds for themselves, drafted in conversation and kept only on
  their yes, in their own words.

Each set is a plain file the learner owns, .private/expectations/<set>.yaml. Its items are indexed
into the same reference space as the common standards (kind 'standard', origin external or
personal), so planning retrieves them, lesson sidecars can align to them, and search can filter by
origin. They are kept apart from the common standards: their own id prefix (exp:), never removed
when the common standards are reloaded, and labeled by origin everywhere they are shown.

Nothing is extracted from a document unless the learner confirms the items; the source document is
referenced (library id, URL or title), never copied whole.
"""
from __future__ import annotations

import datetime as _dt
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .core import Workspace

ORIGINS = ("external", "personal")
LEVELS = ("", "aspiration", "expectation", "requirement")


def _today() -> str:
    return _dt.date.today().isoformat()


class Expectations:
    def __init__(self, ws: "Workspace"):
        self.ws = ws

    @property
    def dir(self) -> Path:
        return self.ws.private / "expectations"

    def _file(self, name: str) -> Path:
        from .knowledge import _slug
        return self.dir / f"{_slug(name)}.yaml"

    def _read(self, name: str) -> dict:
        from .core import HarnessError, _read_yaml
        f = self._file(name)
        if not f.exists():
            raise HarnessError(f"No expectation set named {name!r}. standards(action='sets') lists them.")
        return _read_yaml(f, {})

    def _write(self, data: dict) -> None:
        from .core import _write_yaml
        _write_yaml(self._file(data["set"]), data)

    # --------------------------------------------------------------- indexing
    def _prefix(self, data: dict) -> str:
        from .knowledge import _slug
        return {"personal": "ME", "external": "EXT"}[data["origin"]] + "-" + _slug(data["set"]).upper()

    def _index(self, data: dict) -> int:
        for doc_id, meta in self.ws.index.docs_in_scope("reference"):
            if meta.get("set") == data["set"] and doc_id.startswith("exp:"):
                self.ws.index.remove(doc_id)
        if data.get("archived"):
            return 0
        n = 0
        for it in data.get("items", []):
            if it.get("retired"):
                continue
            meta: dict[str, Any] = {
                "scope": "reference", "tier": "pinned", "origin": data["origin"], "set": data["set"],
                "code": it["code"], "title": it["code"], "statement": it["statement"],
                "domain": [x for x in (data.get("title"), it.get("area")) if x],
                "grade": data.get("context", {}).get("level", ""),
                "jurisdiction": data.get("issuer", "") or ("self" if data["origin"] == "personal" else ""),
                "attribution": data.get("attribution", "") or (
                    f"From {data['issuer']}" if data.get("issuer") else ""),
                "level": it.get("level", ""), "license": data.get("license", "")}
            body = " ".join([it["code"], it["statement"], it.get("area", ""), data.get("title", ""),
                             " ".join(it.get("keywords", []))])
            self.ws.index.upsert(f"exp:{data['set']}:{it['code']}", "standard", body, meta,
                                 str(self._file(data["set"]).relative_to(self.ws.root)))
            n += 1
        return n

    def reindex(self) -> int:
        from .core import _read_yaml
        return sum(self._index(_read_yaml(f, {})) for f in sorted(self.dir.glob("*.yaml"))) if self.dir.exists() else 0

    # ---------------------------------------------------------------- actions
    def manage(self, action: str = "list", set: str = "", origin: str = "", title: str = "", issuer: str = "",
               context: dict | None = None, source: dict | None = None, items: list[dict] | None = None,
               code: str = "", query: str = "", confirmed: bool = False, limit: int = 8) -> dict:
        from .core import HarnessError
        if action == "list":
            return self.list()
        if action == "search":
            return self.search(query, origin, set, limit)
        if not set.strip():
            raise HarnessError("Name the expectation set (set=...).")
        if action == "create":
            if origin not in ORIGINS:
                raise HarnessError("origin must be external (set by a school, program or employer) or personal.")
            if self._file(set).exists():
                raise HarnessError(f"An expectation set named {set!r} exists; add items to it instead.")
            if origin == "external" and not (issuer.strip() and ((source or {}).get("title") or (source or {}).get("url")
                                                                   or (source or {}).get("library_id"))):
                raise HarnessError("An external set needs who set it (issuer) and the document it comes from "
                                   "(source title, url or library_id), so every item is verifiable (principle 19).")
            src = {k: str(v).strip() for k, v in (source or {}).items()
                   if k in ("kind", "url", "title", "library_id", "accessed_on", "page") and str(v).strip()}
            data = {"schema": 1, "set": set.strip(), "origin": origin, "title": title.strip() or set.strip(),
                    "issuer": issuer.strip(), "context": {k: str(v) for k, v in (context or {}).items()},
                    "source": src, "created": _today(), "items": []}
            self._write(data)
            return {"created": self._summary(data)}
        data = self._read(set)
        if action == "show":
            return {"set": data, "file": str(self._file(set).relative_to(self.ws.root))}
        if action == "add":
            if not confirmed:
                raise HarnessError("Read the items back to the learner first, in their final wording; add them "
                                   "with confirmed=true on their yes.")
            added = []
            n = len(data["items"])
            have = {it["code"] for it in data["items"]}
            for raw in items or []:
                statement = str(raw.get("statement", "")).strip()
                if not statement:
                    raise HarnessError("Every item needs a statement.")
                n += 1
                c = str(raw.get("code") or f"{self._prefix(data)}.{n}").strip()
                if c in have:
                    raise HarnessError(f"{c} is already in {set}.")
                from .neutrality import check
                if data["origin"] == "external" and (issue := check(statement)):
                    raise HarnessError(f"{statement[:80]!r}: {issue} (principle 19)")
                level = str(raw.get("level", ""))
                if level not in LEVELS:
                    raise HarnessError(f"level must be one of {', '.join(x for x in LEVELS if x)}.")
                it = {"code": c, "statement": statement, "added": _today(),
                      **({"area": str(raw["area"])} if raw.get("area") else {}),
                      **({"level": level} if level else {}),
                      **({"keywords": [str(k) for k in raw["keywords"]]} if raw.get("keywords") else {}),
                      **({"why": str(raw["why"])} if raw.get("why") else {}),
                      **({"where_in_source": str(raw["where_in_source"])} if raw.get("where_in_source") else {})}
                data["items"].append(it)
                have.add(c)
                added.append(c)
        elif action == "retire":
            it = next((x for x in data["items"] if x["code"] == code), None)
            if not it:
                raise HarnessError(f"{code} is not in {set}.")
            it["retired"] = _today()        # kept: lessons aligned to it keep their history
        elif action in ("archive", "restore"):
            data["archived"] = action == "archive"
        else:
            raise HarnessError("action must be list, search, create, show, add, retire, archive or restore.")
        self._write(data)
        indexed = self._index(data)
        out = {"set": self._summary(data), "indexed": indexed}
        if action == "add":
            out["added"] = added
        return out

    def _summary(self, data: dict) -> dict:
        return {"set": data["set"], "origin": data["origin"], "title": data.get("title", ""),
                "issuer": data.get("issuer", ""), "context": data.get("context", {}),
                "source": data.get("source", {}), "archived": bool(data.get("archived")),
                "items": sum(not x.get("retired") for x in data.get("items", [])),
                "file": str(self._file(data["set"]).relative_to(self.ws.root))}

    def list(self) -> dict:
        from .core import _read_yaml
        sets = [self._summary(_read_yaml(f, {})) for f in sorted(self.dir.glob("*.yaml"))] if self.dir.exists() else []
        return {"sets": sets}

    def search(self, query: str, origin: str = "", set: str = "", limit: int = 8) -> dict:
        """Search standards across origins: common, external, personal (or one of them)."""
        from .core import HarnessError
        if origin and origin not in ("common", *ORIGINS):
            raise HarnessError("origin must be common, external or personal.")
        filters = {"origin": origin} if origin else None
        hits = self.ws.search_memory(query, kinds=["standard"], limit=limit * 3 if set else limit,
                                     scope="reference", filters=filters)["results"]
        out = []
        for h in hits:
            meta = (self.ws.index.doc(h["id"]) or {}).get("meta", {})
            if set and meta.get("set") != set:
                continue
            out.append({"code": meta.get("code", ""), "statement": meta.get("statement", ""),
                        "origin": meta.get("origin", "common"), "set": meta.get("set", ""),
                        "from": meta.get("jurisdiction", ""), "level": meta.get("level", "")})
        return {"query": query, "results": out[:limit]}
