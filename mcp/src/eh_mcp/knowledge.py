"""Knowledge lifecycle: scopes, tiers, use over time, just-in-time demand, clusters, standards.

Scopes (a hard filter on every search):
- meta: knowledge about the learner and the harness (diary, logs, notes, defenses).
- domain: what the learner is learning (library documents, learnings). Has tiers.
- reference: pinned standards. Never cooled, never forgotten.

Domain tiers: active (summary + vector + graph), cold (summary + graph, vector dropped,
keyword-searchable), forgotten (a one-line marker; only ever on the learner's yes).

Relevance is recomputed deterministically at each check-in (sweep):
use fading with a 30-day half-life, plus demand from the plan: the concepts of the
learner's current steps and their prerequisites. Demand rewarms cold items just in
time (algebra notes come back when calculus needs them).
"""

from __future__ import annotations

import datetime as _dt
import json
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from .core import Workspace

HALF_LIFE_DAYS = 30
ACTIVE_SCORE = 0.25
NEW_DAYS = 30
FORGET_AFTER_DAYS = 365
ACTIVE_CAP_PER_AREA = 50
OPEN_LICENSES = ("creativecommons.org/licenses/by/", "creativecommons.org/publicdomain/zero/")


def _today() -> _dt.date:
    return _dt.date.today()


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")


REL_EDGES = {"buildsTowards": "builds_towards", "relatesTo": "relates_to", "hasChild": "hasChild"}


def _code_key(code: str) -> str:
    return re.sub(r"[^A-Za-z0-9-]", "", str(code)).upper()


def _records(files: list[Path], wanted_line):
    """Yield records from NDJSON, JSON-array or CSV files without loading a file whole."""
    import csv
    for f in files:
        if f.suffix == ".csv":
            with f.open(encoding="utf-8", newline="") as fh:
                yield from csv.DictReader(fh)
            continue
        with f.open(encoding="utf-8") as fh:
            head = fh.read(1)
            while head and head.isspace():
                head = fh.read(1)
            if head == "[":                       # a JSON array: small exports only
                fh.seek(0)
                yield from (o for o in json.load(fh) if isinstance(o, dict))
                continue
            fh.seek(0)
            for line in fh:
                if line.strip() and wanted_line(line):
                    o = json.loads(line)
                    if isinstance(o, dict):
                        yield o


class Knowledge:
    def __init__(self, ws: "Workspace"):
        self.ws = ws

    # ---------------------------------------------------------- durable state
    @property
    def state_path(self) -> Path:
        return self.ws.private / "knowledge.yaml"

    def _state(self) -> dict:
        p = self.state_path
        data = yaml.safe_load(p.read_text(encoding="utf-8")) if p.exists() else None
        data = data or {}
        data.setdefault("schema", 1)
        data.setdefault("items", {})
        return data

    def _save(self, data: dict) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.state_path.with_suffix(".tmp")
        tmp.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
        tmp.replace(self.state_path)

    def tier_of(self, doc_id: str) -> str:
        return self._state()["items"].get(doc_id, {}).get("tier", "active")

    def relevant_standards(self, query: str, limit: int = 6, expand: bool = True) -> dict:
        """Return standards that may describe prerequisites for a learner's topic.

        This is orientation evidence, not a curriculum: the project still determines
        what is learned.  Full statements and attribution are returned so a planner can
        judge relevance rather than treating a code or search rank as sufficient.
        """
        source = self._state().get("standards_source")
        if not source and self.ws.expectations.list()["sets"]:
            source = {"subject": "expectation sets only"}
        if not source:
            return {"loaded": False, "query": query.strip(), "matches": [],
                    "note": "No standards are loaded; do not claim they were checked."}
        search_query = query.strip()
        stop = {"a", "an", "and", "as", "by", "for", "in", "of", "on", "the", "to", "with", "intro"}
        def topic_words(text: str) -> set[str]:
            return {w[:-1] if len(w) > 4 and w.endswith("s") else w
                    for w in _slug(text).split("-") if w and w not in stop}
        query_words = topic_words(search_query)
        # The default program already records which standards describe each idea.
        # Use those authored concept/code links to bridge a topic name such as
        # "transformers" to standards language such as vectors or periodic functions.
        from .core import PROGRAMS
        for track_file in PROGRAMS.glob("*/track.yaml") if expand else []:
            track = yaml.safe_load(track_file.read_text(encoding="utf-8")) or {}
            for idea in track.get("ideas", []):
                label = " ".join([str(idea.get("id", "")), str(idea.get("idea", ""))])
                label_words = topic_words(label)
                if query_words & label_words:
                    search_query += " " + " ".join(
                        [label, *[str(c.get("name", "")) for c in idea.get("concepts", [])],
                         *[str(code) for code in idea.get("standards", [])]])
        hits = self.ws.search_memory(search_query, kinds=["standard"], limit=limit,
                                     scope="reference")["results"] if query.strip() else []
        matches = []
        for hit in hits:
            doc = self.ws.index.doc(hit["id"])
            meta = (doc or {}).get("meta", {})
            matches.append({
                "id": hit["id"],
                "code": meta.get("code", ""),
                "statement": meta.get("statement", ""),
                "grade": meta.get("grade", ""),
                "domain": meta.get("domain", []),
                "jurisdiction": meta.get("jurisdiction", ""),
                "attribution": meta.get("attribution", ""),
                "license": meta.get("license", ""),
                "origin": meta.get("origin", "common"),
                **({"set": meta["set"]} if meta.get("set") else {}),
                "signals": hit.get("signals", []),
            })
        return {"loaded": True, "query": query.strip(), "expanded_query": search_query, "matches": matches,
                "source": source,
                "note": "Matches are reference points to inspect for prerequisites; they do not set the project."}

    # ------------------------------------------------------------------ use
    def record_use(self, doc_ids: list[str], how: str = "opened") -> dict:
        """A use: the original was opened (hop 2), cited in a lesson, or linked to a learning.
        Search hits alone don't count. A cold item that gets used is rewarmed at once."""
        data = self._state()
        rewarmed = []
        for doc_id in doc_ids:
            if not self.ws.index.doc(doc_id):
                continue
            it = data["items"].setdefault(doc_id, {"tier": "active", "uses": []})
            it["uses"] = (it.get("uses", []) + [f"{_today().isoformat()} {how}"])[-50:]
            if it.get("tier") == "cold":
                it["tier"] = "active"
                rewarmed.append(doc_id)
        self._save(data)
        for doc_id in rewarmed:
            self.ws.index.set_tier(doc_id, "active")
        return {"recorded": len(doc_ids), "rewarmed": rewarmed}

    @staticmethod
    def score(uses: list[str], today: _dt.date | None = None) -> float:
        today = today or _today()
        s = 0.0
        for u in uses:
            try:
                d = _dt.date.fromisoformat(u.split()[0])
            except ValueError:
                continue
            s += 0.5 ** (max((today - d).days, 0) / HALF_LIFE_DAYS)
        return s

    # --------------------------------------------------------------- demand
    def demanded_concepts(self) -> set[str]:
        """Concepts of every step not yet defended, plus their prerequisites (one hop)."""
        concepts: set[str] = set()
        projects = self.ws.root / "projects"
        for plan_file in projects.glob("*/program.yaml") if projects.exists() else []:
            plan = yaml.safe_load(plan_file.read_text(encoding="utf-8")) or {}
            prog_file = plan_file.with_name("progress.yaml")
            prog = (yaml.safe_load(prog_file.read_text(encoding="utf-8")) or {}) if prog_file.exists() else {}
            done = {k for k, v in (prog.get("steps") or {}).items() if v.get("status") == "defended"}
            for step in plan.get("steps", []):
                if step.get("id") not in done:
                    concepts |= {_slug(c) for c in step.get("concepts", [])}
        return concepts | self.ws.index.prerequisites({f"concept:{c}" for c in concepts})

    # ---------------------------------------------------------------- sweep
    def sweep(self, today: _dt.date | None = None) -> dict:
        """Recompute relevance for every domain item; move items between active and cold;
        propose (never perform) forgetting. Reference (standards) and meta are untouched."""
        today = today or _today()
        demand = self.demanded_concepts()
        data = self._state()
        rows = self.ws.index.docs_in_scope("domain")
        decisions: dict[str, dict] = {}
        for doc_id, meta in rows:
            it = data["items"].setdefault(doc_id, {"tier": "active", "uses": []})
            concepts = {c.removeprefix("concept:") for c in meta.get("concepts", [])}
            added = meta.get("date") or today.isoformat()
            try:
                age_added = (today - _dt.date.fromisoformat(str(added)[:10])).days
            except ValueError:
                age_added = 0
            last = max([u.split()[0] for u in it.get("uses", [])] or [str(added)[:10]])
            try:
                idle = (today - _dt.date.fromisoformat(last)).days
            except ValueError:
                idle = 0
            sc = self.score(it.get("uses", []), today)
            wanted = bool(concepts & demand)
            decisions[doc_id] = {"score": sc, "demanded": wanted, "new": age_added <= NEW_DAYS,
                                 "idle": idle, "area": meta.get("area", ""), "kind": meta.get("_kind", ""),
                                 "title": meta.get("title", "")}
            decisions[doc_id]["active"] = wanted or decisions[doc_id]["new"] or sc >= ACTIVE_SCORE
        by_area: dict[str, list[str]] = {}
        for doc_id, d in decisions.items():
            if d["active"] and not d["demanded"]:
                by_area.setdefault(d["area"], []).append(doc_id)
        for area, ids in by_area.items():
            demanded_n = sum(1 for d in decisions.values() if d["area"] == area and d["demanded"])
            room = max(ACTIVE_CAP_PER_AREA - demanded_n, 0)
            for doc_id in sorted(ids, key=lambda i: -decisions[i]["score"])[room:]:
                decisions[doc_id]["active"] = False
        cooled, rewarmed, forget = [], [], []
        for doc_id, d in decisions.items():
            new_tier = "active" if d["active"] else "cold"
            old = data["items"][doc_id].get("tier", "active")
            if new_tier != old:
                data["items"][doc_id]["tier"] = new_tier
                self.ws.index.set_tier(doc_id, new_tier)
                (rewarmed if new_tier == "active" else cooled).append(doc_id)
            if (new_tier == "cold" and not d["demanded"] and d["idle"] >= FORGET_AFTER_DAYS
                    and doc_id.startswith("lib:")):
                forget.append({"id": doc_id, "title": d["title"], "idle_days": d["idle"]})
        self._save(data)
        return {"demanded_concepts": sorted(demand), "cooled": cooled, "rewarmed": rewarmed,
                "forget_proposals": forget,
                "note": "Forgetting happens only if the learner says yes (forget_library_item)."}

    # -------------------------------------------------------------- forget
    def forget(self, doc_id: str, learner_confirmed: bool) -> dict:
        from .core import HarnessError
        if not learner_confirmed:
            raise HarnessError("Forgetting needs the learner's yes; ask them first.")
        if not doc_id.startswith("lib:"):
            raise HarnessError("Only library documents can be forgotten; learnings and standards are kept.")
        rid = doc_id.removeprefix("lib:")
        rec = self.ws.library._load(rid)
        if not rec:
            raise HarnessError(f"No library record {doc_id}.")
        marker_file = self.ws.private / "library" / "forgotten.yaml"
        markers = (yaml.safe_load(marker_file.read_text(encoding="utf-8")) or []) if marker_file.exists() else []
        markers.append({"title": rec["title"], "path": rec["path"], "area": rec["area"],
                        "concepts": rec["concepts"], "forgotten": _today().isoformat()})
        marker_file.write_text(yaml.safe_dump(markers, sort_keys=False), encoding="utf-8")
        self.ws.library._record_path(rid).unlink()
        self.ws.index.remove(doc_id)
        data = self._state()
        data["items"].pop(doc_id, None)
        self._save(data)
        return {"forgotten": doc_id, "kept": "a one-line marker in .private/library/forgotten.yaml",
                "original": "untouched, where the learner keeps it"}

    # ------------------------------------------------------------ clusters
    def clusters(self, area: str | None = None, threshold: float = 0.55) -> dict:
        """Computed on demand, never stored. Items group by shared concept; items without
        concepts group by similarity of their vectors (when smart search is on), then by tag."""
        rows = [(i, m) for i, m in self.ws.index.docs_in_scope("domain")
                if m.get("_kind") == "library" and (not area or m.get("area") == area)]
        groups: dict[str, list[str]] = {}
        loose = []
        for doc_id, m in rows:
            cs = sorted(m.get("concepts", []))
            if cs:
                groups.setdefault(cs[0].removeprefix("concept:"), []).append(doc_id)
            else:
                loose.append((doc_id, m))
        vecs = self.ws.index.vectors([d for d, _ in loose]) if loose else {}
        used: set[str] = set()
        for doc_id, m in loose:
            if doc_id in used:
                continue
            label = (m.get("tags") or ["unsorted"])[0]
            members = [doc_id]
            used.add(doc_id)
            if doc_id in vecs:
                for other, _ in loose:
                    if other not in used and other in vecs and float(vecs[doc_id] @ vecs[other]) >= threshold:
                        members.append(other)
                        used.add(other)
            groups.setdefault(f"similar: {label}", []).extend(members)
        meta = dict(rows)
        state = self._state()["items"]
        out = []
        for label, ids in sorted(groups.items(), key=lambda kv: -len(kv[1])):
            out.append({"label": label, "size": len(ids),
                        "items": [{"id": i, "title": meta[i].get("title", ""),
                                   "tier": state.get(i, {}).get("tier", "active"),
                                   "last_used": max([u.split()[0] for u in state.get(i, {}).get("uses", [])] or
                                                    [""])} for i in ids]})
        return {"area": area or "all", "clusters": out,
                "next": "Name clusters for the learner; offer to move an unused cluster to cold."}

    def set_tier(self, doc_ids: list[str], tier: str) -> dict:
        from .core import HarnessError
        if tier not in ("active", "cold"):
            raise HarnessError("tier must be active or cold.")
        data = self._state()
        moved = []
        for doc_id in doc_ids:
            d = self.ws.index.doc(doc_id)
            if not d or d["meta"].get("scope") != "domain":
                continue
            data["items"].setdefault(doc_id, {"uses": []})["tier"] = tier
            self.ws.index.set_tier(doc_id, tier)
            moved.append(doc_id)
        self._save(data)
        return {"moved": moved, "tier": tier}

    # ----------------------------------------------------------- standards
    def load_standards(self, folder: str, subject: str = "Mathematics",
                       jurisdictions: list[str] | None = None) -> dict:
        """Pin academic standards from a Learning Commons Knowledge Graph download on this
        computer (newline-delimited JSON as published, a JSON array, or CSV). Files are read a
        line at a time. Only records carrying an open license (CC BY or CC0) are pinned, each
        with its own attribution statement. Pinned records are never cooled or forgotten.
        Headings without a code are not pinned; their names become each standard's 'domain'."""
        from .core import HarnessError
        src = Path(folder).expanduser().resolve()
        if not src.exists():
            raise HarnessError(f"No standards download at {src}.")
        juris = [j for j in (jurisdictions or ["Multi-State"])]
        juris_l = {j.lower() for j in juris}
        files = sorted([*src.rglob("*.json"), *src.rglob("*.jsonl"), *src.rglob("*.csv")])
        items: dict[str, dict] = {}   # uuid -> fields, every open record in scope (headings too)
        parent: dict[str, str] = {}
        links: list[tuple[str, str, str]] = []
        skipped_license = 0
        quoted = [json.dumps(j) for j in juris]

        def wanted_line(line: str) -> bool:  # cheap test before parsing a 200 MB file
            return "relationshipType" in line or not quoted or any(q in line for q in quoted)

        for o in _records(files, wanted_line):
            rel = o.get("relationshipType")
            if rel:
                s, t = o.get("sourceEntityValue"), o.get("targetEntityValue")
                if s and t and rel in REL_EDGES:
                    links.append((str(s), rel, str(t)))
                continue
            text_ = o.get("description") or o.get("fullStatement")
            subj, jur = str(o.get("academicSubject") or ""), str(o.get("jurisdiction") or "")
            if not text_ or (subject and subject.lower() not in subj.lower()) or (juris_l and jur.lower() not in juris_l):
                continue
            lic = str(o.get("license") or "")
            if not any(x in lic for x in OPEN_LICENSES):
                skipped_license += 1
                continue
            code = o.get("statementCode") or o.get("humanCodingScheme") or ""
            uid = str(o.get("caseIdentifierUUID") or o.get("identifier") or code)
            items[uid] = {"code": str(code), "text": str(text_), "subject": subj, "jurisdiction": jur,
                          "url": str(o.get("caseIdentifierURI") or ""),
                          "license": lic, "attribution": str(o.get("attributionStatement") or ""),
                          "grade": o.get("gradeLevel") or "", "type": o.get("normalizedStatementType") or ""}
        edges = []
        for s, rel, t in links:
            if s in items and t in items:
                if rel == "hasChild":
                    parent[t] = s
                elif items[s]["code"] and items[t]["code"]:
                    edges.append((f"std:{s}", REL_EDGES[rel], f"std:{t}"))

        def headings(uid: str) -> list[str]:
            out, seen = [], set()
            while uid in parent and uid not in seen:
                seen.add(uid)
                uid = parent[uid]
                if not items[uid]["code"]:
                    out.append(items[uid]["text"])
            return out[::-1]

        keep = {f"std:{u}" for u, it in items.items() if it["code"]}
        for doc_id, _ in self.ws.index.docs_in_scope("reference"):
            if doc_id.startswith("std:") and doc_id not in keep:
                self.ws.index.remove(doc_id)       # from an earlier download or id scheme
        pinned, attributions, id_by_code = 0, {}, {}
        for uid, it in items.items():
            if not it["code"]:
                continue
            up = parent.get(uid)
            if up and items[up]["code"]:
                edges.append((f"std:{uid}", "part_of", f"std:{up}"))
            domain = headings(uid)
            meta: dict[str, Any] = {"scope": "reference", "tier": "pinned", "origin": "common",
                                    "code": it["code"], "title": it["code"],
                                    "grade": it["grade"], "subject": it["subject"], "domain": domain,
                                    "jurisdiction": it["jurisdiction"], "license": it["license"],
                                    "attribution": it["attribution"], "type": it["type"],
                                    "statement": it["text"], "url": it["url"]}
            body = " ".join([it["code"], it["text"], *domain[-2:]])
            self.ws.index.upsert(f"std:{uid}", "standard", body, meta, f"standards:{src.name}")
            id_by_code[it["code"]] = f"std:{uid}"
            attributions[it["attribution"]] = attributions.get(it["attribution"], 0) + 1
            pinned += 1
        self.ws.index.add_edges(edges)
        data = self._state()
        data["standards_source"] = {"folder": str(src), "subject": subject, "jurisdictions": sorted(juris),
                                    "loaded": _today().isoformat(), "pinned": pinned}
        self._save(data)
        cited, missing = self._link_track_codes(id_by_code)
        return {"pinned": pinned, "skipped_without_open_license": skipped_license,
                "progression_edges": sum(1 for e in edges if e[1] != "part_of"),
                "structure_edges": sum(1 for e in edges if e[1] == "part_of"),
                "program_codes_linked": cited, "program_codes_missing": missing,
                "attributions": attributions,
                "note": "Show these attribution statements wherever standards are displayed."}

    def _link_track_codes(self, id_by_code: dict[str, str]) -> tuple[int, list[str]]:
        """Link each idea's concepts to the standards it cites, so the graph reaches them.
        Codes compare without punctuation, so HSF-LE.A.1b finds HSF-LE.A.1.b."""
        from .core import PROGRAMS
        norm = {_code_key(k): v for k, v in id_by_code.items()}
        edges, linked, missing = [], set(), []
        for track_file in PROGRAMS.glob("*/track.yaml"):
            track = yaml.safe_load(track_file.read_text(encoding="utf-8")) or {}
            for idea in track.get("ideas", []):
                for code in idea.get("standards", []):
                    hit = norm.get(_code_key(code))
                    if not hit:
                        missing.append(code)
                        continue
                    linked.add(code)
                    edges += [(f"concept:{c['id']}", "cites", hit) for c in idea.get("concepts", [])]
        self.ws.index.add_edges(edges)
        return len(linked), sorted(set(missing)) if id_by_code else []

    def reload_standards(self) -> dict | None:
        src = self._state().get("standards_source")
        if src and Path(src["folder"]).exists():
            return self.load_standards(src["folder"], src.get("subject", "Mathematics"), src.get("jurisdictions"))
        return None
