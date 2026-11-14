"""Search index derived from the learner's files.

- Keyword: SQLite FTS5 over each record's text (for library documents, the summary).
- Semantic (opt-in): local embeddings, TurboQuant-compressed, in the same file.
- Graph: light edges (document -> area/concept, learning -> concept,
  concept -> prerequisite concept) used to widen a search by one hop.

The index is never the source of truth: every row is rebuilt from the files.
Each row carries a hash of its text; vectors whose hash no longer matches are
re-embedded by ``sync``, so the semantic rows never drift from the text.
Ranked lists are fused by reciprocal rank fusion (as in cat), with per-list
constants so a selective literal-match list can carry decisive weight.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from pathlib import Path

BITS = 4
SEED = 0
RRF_K = 60
KIND_SCOPE = {"log": "meta", "note": "meta", "checkpoint": "meta",
              "diary": "reflection", "defense": "reflection", "learning": "reflection",
              "concept_note": "reflection", "annotation": "reflection", "error": "reflection", "report": "reflection", "retro": "reflection",
              "library": "domain", "standard": "reference"}


def rrf(ranked: dict[str, list[str]], k_by_list: dict[str, int] | None = None) -> dict[str, dict]:
    k_by_list = k_by_list or {}
    scored: dict[str, dict] = {}
    for name, ids in ranked.items():
        k = k_by_list.get(name, RRF_K)
        for rank, doc_id in enumerate(ids):
            e = scored.setdefault(doc_id, {"score": 0.0, "signals": []})
            e["score"] += 1.0 / (k + rank + 1)
            e["signals"].append(name)
    return scored


HARD_KEYS = ("scope", "project", "origin")  # identity filters; every other metadata filter is soft
SOFT_FLOOR = 0.25                  # weight left to a strong text match with no metadata match


def _values(v) -> set:
    if isinstance(v, (list, tuple, set)):
        return {str(x).lower() for x in v if x not in (None, "")}
    return {str(v).lower()} if v not in (None, "") else set()


def matches(meta: dict, kind: str, kinds: list[str] | None, filters: dict | None) -> bool:
    """Hard filters only: kinds, scope and project. A record not tied to a project
    (a log, a diary entry) stays visible under a project filter."""
    if kinds and kind not in kinds:
        return False
    for key in HARD_KEYS:
        want = (filters or {}).get(key)
        if want in (None, "", []):
            continue
        haves = _values(meta.get(key))
        if key == "project" and not haves:
            continue
        if not (_values(want) & haves):
            return False
    return True


def metadata_match(meta: dict, filters: dict | None) -> float | None:
    """Soft filters as a union: the mean, over the requested keys, of how much of each
    request the record meets (a list counts the share of requested values it has; 'since'
    is met or not). None when no soft filter was given."""
    soft = {k: v for k, v in (filters or {}).items() if k not in HARD_KEYS and v not in (None, "", [])}
    if not soft:
        return None
    total = 0.0
    for key, want in soft.items():
        if key == "since":
            total += 1.0 if str(meta.get("date", "")) >= str(want) else 0.0
            continue
        wants, haves = _values(want), _values(meta.get(key))
        total += len(wants & haves) / len(wants)
    return total / len(soft)


class Index:
    def __init__(self, path: Path):
        self.path = path
        self._embedder = None
        self._tq = None

    # ------------------------------------------------------------- storage
    def _conn(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        c = sqlite3.connect(self.path)
        c.execute("CREATE TABLE IF NOT EXISTS docs (id TEXT PRIMARY KEY, kind TEXT, file TEXT, "
                  "meta TEXT, hash TEXT, body TEXT)")
        c.execute("CREATE VIRTUAL TABLE IF NOT EXISTS fts USING fts5(id UNINDEXED, body)")
        c.execute("CREATE TABLE IF NOT EXISTS vec (id TEXT PRIMARY KEY, hash TEXT, norm REAL, codes BLOB)")
        c.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS edges (src TEXT, rel TEXT, dst TEXT, "
                  "PRIMARY KEY (src, rel, dst))")
        cols = [r[1] for r in c.execute("PRAGMA table_info(docs)")]
        if "body" not in cols:  # index files from the keyword-only build
            c.execute("ALTER TABLE docs ADD COLUMN body TEXT")
        return c

    def _setting(self, c: sqlite3.Connection, key: str) -> str | None:
        r = c.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return r[0] if r else None

    def mode(self) -> str:
        with self._conn() as c:
            return "semantic" if self._setting(c, "semantic") == "on" and self._embedder else "keyword"

    # -------------------------------------------------------------- writes
    def upsert(self, doc_id: str, kind: str, body: str, meta: dict, file: str,
               edges: list[tuple[str, str]] | None = None) -> None:
        """edges: (rel, dst) pairs from this record, e.g. ("about", "concept:gradient")."""
        h = hashlib.sha256(body.encode("utf-8")).hexdigest()
        meta = dict(meta)
        meta.setdefault("scope", KIND_SCOPE.get(kind, "domain"))
        with self._conn() as c:
            if "tier" not in meta:
                old = c.execute("SELECT meta FROM docs WHERE id = ?", (doc_id,)).fetchone()
                meta["tier"] = json.loads(old[0]).get("tier") if old else None
                meta["tier"] = meta["tier"] or ("pinned" if meta["scope"] == "reference" else "active")
            c.execute("DELETE FROM fts WHERE id = ?", (doc_id,))
            c.execute("INSERT OR REPLACE INTO docs (id, kind, file, meta, hash, body) VALUES (?, ?, ?, ?, ?, ?)",
                      (doc_id, kind, file, json.dumps(meta), h, body))
            c.execute("INSERT INTO fts (id, body) VALUES (?, ?)", (doc_id, body))
            c.execute("DELETE FROM edges WHERE src = ?", (doc_id,))
            c.executemany("INSERT OR IGNORE INTO edges VALUES (?, ?, ?)",
                          [(doc_id, rel, dst) for rel, dst in (edges or [])])
            if self._embedder and self._setting(c, "semantic") == "on" and meta["tier"] != "cold":
                self._embed_rows(c, [(doc_id, body, h)])

    def set_tier(self, doc_id: str, tier: str) -> None:
        """Cold drops the vector (rebuilt from the summary on rewarming); active re-embeds."""
        with self._conn() as c:
            r = c.execute("SELECT meta, body, hash FROM docs WHERE id = ?", (doc_id,)).fetchone()
            if not r:
                return
            meta = json.loads(r[0])
            meta["tier"] = tier
            c.execute("UPDATE docs SET meta = ? WHERE id = ?", (json.dumps(meta), doc_id))
            if tier == "cold":
                c.execute("DELETE FROM vec WHERE id = ?", (doc_id,))
            elif self._embedder and self._setting(c, "semantic") == "on":
                self._embed_rows(c, [(doc_id, r[1], r[2])])

    def docs_in_scope(self, scope: str) -> list[tuple[str, dict]]:
        with self._conn() as c:
            rows = c.execute("SELECT id, kind, meta FROM docs").fetchall()
        out = []
        for doc_id, kind, meta in rows:
            m = json.loads(meta)
            if m.get("scope") == scope:
                m["_kind"] = kind
                out.append((doc_id, m))
        return out

    def add_edges(self, edges: list[tuple[str, str, str]]) -> None:
        with self._conn() as c:
            c.executemany("INSERT OR IGNORE INTO edges VALUES (?, ?, ?)", edges)

    def prerequisites(self, concepts: set[str]) -> set[str]:
        """Concept slugs one 'requires' step back from the given concept nodes."""
        if not concepts:
            return set()
        with self._conn() as c:
            q = ",".join("?" * len(concepts))
            return {r[0].removeprefix("concept:") for r in
                    c.execute(f"SELECT dst FROM edges WHERE rel = 'requires' AND src IN ({q})", list(concepts))}

    def vectors(self, doc_ids: list[str]) -> dict:
        """Dequantized unit vectors (rotated space) for clustering; empty when smart search is off."""
        if not doc_ids or not self._embedder:
            return {}
        with self._conn() as c:
            q = ",".join("?" * len(doc_ids))
            rows = c.execute(f"SELECT id, codes FROM vec WHERE id IN ({q})", doc_ids).fetchall()
        if not rows:
            return {}
        tq = self._quantizer(self._embedder.dim)
        mats = tq.decode_many([r[1] for r in rows])
        import numpy as np
        mats = mats / np.maximum(np.linalg.norm(mats, axis=1, keepdims=True), 1e-9)
        return {r[0]: mats[i] for i, r in enumerate(rows)}

    def pca_projection(self, scope: str = "domain", max_points: int = 600) -> dict:
        """Project TurboQuant-dequantized vectors to 3D with PCA for local exploration.

        The stored vectors are in the fixed rotated space; an orthogonal rotation preserves
        distances and PCA variance. Coordinates remain approximate because the vectors are quantized.
        """
        if not self._embedder:
            return {"points": [], "note": "Smart search must be on before a knowledge map can be built."}
        import numpy as np
        max_points = max(3, min(int(max_points), 2000))
        with self._conn() as c:
            rows = c.execute(
                "SELECT v.id, v.codes, d.kind, d.file, d.meta, d.body FROM vec v "
                "JOIN docs d ON d.id = v.id AND d.hash = v.hash ORDER BY v.id LIMIT ?", (max_points,)).fetchall()
        rows = [r for r in rows if scope == "all" or json.loads(r[4]).get("scope") == scope]
        if not rows:
            return {"points": [], "note": f"No TurboQuant vectors are available in the {scope!r} scope."}
        x = self._quantizer(self._embedder.dim).decode_many([r[1] for r in rows]).astype(np.float64)
        x /= np.maximum(np.linalg.norm(x, axis=1, keepdims=True), 1e-12)
        centered = x - x.mean(axis=0, keepdims=True)
        _, singular, vt = np.linalg.svd(centered, full_matrices=False)
        dims = min(3, len(vt))
        coords = centered @ vt[:dims].T
        if dims < 3:
            coords = np.pad(coords, ((0, 0), (0, 3 - dims)))
        scale = np.max(np.abs(coords), axis=0)
        coords /= np.where(scale > 1e-12, scale, 1.0)
        variance = singular ** 2
        explained = (variance[:3] / max(float(variance.sum()), 1e-12)).tolist()
        similarities = x @ x.T
        np.fill_diagonal(similarities, -np.inf)
        neighbor_count = min(3, max(0, len(rows) - 1))
        nearest = np.argsort(-similarities, axis=1)[:, :neighbor_count] if neighbor_count else np.empty((len(rows), 0), int)
        points = []
        for i, row in enumerate(rows):
            meta = json.loads(row[4])
            points.append({"id": row[0], "kind": row[2], "scope": meta.get("scope", "domain"),
                           "title": meta.get("title") or meta.get("name") or Path(row[3]).stem or row[0],
                           "area": meta.get("area", ""), "project": meta.get("project", ""),
                           "tier": meta.get("tier", ""), "snippet": _plain_snippet(row[5], 22),
                           "x": round(float(coords[i, 0]), 6), "y": round(float(coords[i, 1]), 6),
                           "z": round(float(coords[i, 2]), 6),
                           "neighbors": [{"id": rows[j][0], "similarity": round(float(similarities[i, j]), 4)}
                                         for j in nearest[i]]})
        return {"points": points, "scope": scope, "count": len(points), "max_points": max_points,
                "explained_variance": [round(float(v), 5) for v in explained] + [0.0] * (3 - len(explained)),
                "source": "TurboQuant-dequantized rotated vectors",
                "note": "PCA is a lossy three-dimensional projection of quantized embeddings; proximity is exploratory, not proof of conceptual equivalence."}

    def remove(self, doc_id: str) -> None:
        with self._conn() as c:
            for t, col in (("docs", "id"), ("fts", "id"), ("vec", "id"), ("edges", "src")):
                c.execute(f"DELETE FROM {t} WHERE {col} = ?", (doc_id,))

    def set_concept_edges(self, edges: list[tuple[str, str, str]]) -> None:
        """Concept-to-concept edges (from the programs), replaced as a set."""
        with self._conn() as c:
            c.execute("DELETE FROM edges WHERE src LIKE 'concept:%' AND rel != 'cites'")  # cites: standards
            c.executemany("INSERT OR IGNORE INTO edges VALUES (?, ?, ?)", edges)

    def clear(self) -> None:
        with self._conn() as c:
            for t in ("docs", "fts", "vec", "edges"):
                c.execute(f"DELETE FROM {t}")

    # ------------------------------------------------------------ semantic
    def _quantizer(self, dim: int):
        from .turboquant import TurboQuant
        if self._tq is None or self._tq.dim != dim:
            self._tq = TurboQuant(dim, bits=BITS, seed=SEED)
        return self._tq

    def _embed_rows(self, c: sqlite3.Connection, rows: list[tuple[str, str, str]]) -> int:
        if not rows:
            return 0
        tq = self._quantizer(self._embedder.dim)
        vectors = self._embedder.embed([r[1] or "" for r in rows])
        for (doc_id, _, h), v in zip(rows, vectors):
            codes, norm = tq.encode(v)
            c.execute("INSERT OR REPLACE INTO vec VALUES (?, ?, ?, ?)", (doc_id, h, norm, codes))
        return len(rows)

    def enable_semantic(self, embedder) -> dict:
        """Attach an embedder, check the fixed settings, and bring the vectors in step with the text."""
        self._embedder = embedder
        fixed = {"model": embedder.name, "dim": str(embedder.dim), "bits": str(BITS), "seed": str(SEED),
                 "fingerprint": getattr(embedder, "fingerprint", "")}
        with self._conn() as c:
            changed = any(self._setting(c, k) not in (None, v) for k, v in fixed.items())
            if changed:  # a different model or setting: every vector is rebuilt
                c.execute("DELETE FROM vec")
            for k, v in fixed.items():
                c.execute("INSERT OR REPLACE INTO settings VALUES (?, ?)", (k, v))
            c.execute("INSERT OR REPLACE INTO settings VALUES ('semantic', 'on')")
        return self.sync()

    def disable_semantic(self) -> None:
        with self._conn() as c:
            c.execute("INSERT OR REPLACE INTO settings VALUES ('semantic', 'off')")

    def semantic_wanted(self) -> bool:
        with self._conn() as c:
            return self._setting(c, "semantic") == "on"

    def sync(self) -> dict:
        """Re-embed rows whose text changed or that have no vector; drop vectors for removed rows."""
        if not self._embedder:
            return {"reembedded": 0, "removed": 0}
        with self._conn() as c:
            stale = [(i, b, h) for i, b, h, m in c.execute(
                "SELECT d.id, d.body, d.hash, d.meta FROM docs d LEFT JOIN vec v ON v.id = d.id "
                "WHERE v.id IS NULL OR v.hash != d.hash").fetchall() if json.loads(m).get("tier") != "cold"]
            removed = c.execute("DELETE FROM vec WHERE id NOT IN (SELECT id FROM docs)").rowcount
            n = 0
            for i in range(0, len(stale), 64):
                n += self._embed_rows(c, stale[i:i + 64])
        return {"reembedded": n, "removed": removed}

    # -------------------------------------------------------------- reads
    def doc(self, doc_id: str) -> dict | None:
        with self._conn() as c:
            r = c.execute("SELECT id, kind, file, meta, body FROM docs WHERE id = ?", (doc_id,)).fetchone()
        return None if not r else {"id": r[0], "kind": r[1], "file": r[2], "meta": json.loads(r[3]), "body": r[4]}

    def neighbors(self, doc_ids: list[str]) -> list[str]:
        """Docs one concept-hop away: concepts of these docs, their prerequisites and dependents,
        then the docs about those concepts."""
        if not doc_ids:
            return []
        with self._conn() as c:
            q = ",".join("?" * len(doc_ids))
            concepts = {r[0] for r in c.execute(f"SELECT dst FROM edges WHERE src IN ({q}) "
                                                "AND dst LIKE 'concept:%'", doc_ids)}
            if not concepts:
                return []
            cq = ",".join("?" * len(concepts))
            near = set(concepts)
            near |= {r[0] for r in c.execute(f"SELECT dst FROM edges WHERE src IN ({cq}) AND rel = 'requires'",
                                             list(concepts))}
            near |= {r[0] for r in c.execute(f"SELECT src FROM edges WHERE dst IN ({cq}) AND rel = 'requires'",
                                             list(concepts))}
            nq = ",".join("?" * len(near))
            rows = c.execute(f"SELECT src, COUNT(*) FROM edges WHERE dst IN ({nq}) AND src NOT LIKE 'concept:%' "
                             "GROUP BY src ORDER BY COUNT(*) DESC", list(near)).fetchall()
        return [r[0] for r in rows if r[0] not in doc_ids]

    @staticmethod
    def _fts_query(q: str) -> str:
        words = re.findall(r"\w+", q.lower())
        return " OR ".join(f'"{w}"' for w in words)

    def search(self, query: str, kinds: list[str] | None = None, filters: dict | None = None,
               limit: int = 8, extra: dict[str, list[str]] | None = None,
               k_by_list: dict[str, int] | None = None, hops: int = 0) -> list[dict]:
        """Hop 1 of two-hop search: rank records (for library documents, their summaries).
        extra: more ranked id lists to fuse (e.g. literal matches in the original files)."""
        fq = self._fts_query(query or "")
        info: dict[str, dict] = {}
        ranked: dict[str, list[str]] = {}
        with self._conn() as c:
            if fq:
                kw = c.execute(
                    "SELECT docs.id, docs.kind, docs.file, docs.meta, "
                    "snippet(fts, 1, '[', ']', ' … ', 14) FROM fts JOIN docs ON docs.id = fts.id "
                    "WHERE fts MATCH ? ORDER BY bm25(fts) LIMIT 200", (fq,)).fetchall()
                keep = []
                for doc_id, kind, file, meta, snip in kw:
                    m = json.loads(meta)
                    if matches(m, kind, kinds, filters):
                        keep.append(doc_id)
                        info[doc_id] = {"kind": kind, "file": file, "meta": m, "snippet": snip}
                ranked["keyword"] = keep
            if query and self._embedder and self._setting(c, "semantic") == "on":
                rows = c.execute("SELECT v.id, v.codes, d.kind, d.file, d.meta, d.body FROM vec v "
                                 "JOIN docs d ON d.id = v.id AND d.hash = v.hash").fetchall()
                rows = [r for r in rows if matches(json.loads(r[4]), r[2], kinds, filters)]
                if rows:
                    scores = self._quantizer(self._embedder.dim).scores(self._embedder.embed([query])[0],
                                                                        [r[1] for r in rows])
                    order = sorted(range(len(rows)), key=lambda i: -scores[i])[:200]
                    ranked["semantic"] = [rows[i][0] for i in order]
                    for i in order:
                        r = rows[i]
                        info.setdefault(r[0], {"kind": r[2], "file": r[3], "meta": json.loads(r[4]),
                                               "snippet": _plain_snippet(r[5])})
        for name, ids in (extra or {}).items():
            ranked[name] = [i for i in ids if self._visible(i, info, kinds, filters)]
        fused = rrf(ranked, k_by_list)
        if hops:
            top = sorted(fused, key=lambda d: -fused[d]["score"])[:limit]
            near = [i for i in self.neighbors(top) if self._visible(i, info, kinds, filters)]
            for rank, doc_id in enumerate(near):
                e = fused.setdefault(doc_id, {"score": 0.0, "signals": []})
                e["score"] += 0.5 / (RRF_K + rank + 1)
                e["signals"].append("graph")
        if metadata_match({}, filters) is not None:
            self._weigh_by_metadata(fused, info, kinds, filters)
        out = []
        for doc_id in sorted(fused, key=lambda d: -fused[d]["score"])[:limit]:
            d = info[doc_id]
            out.append({"id": doc_id, "kind": d["kind"], "file": d["file"], "snippet": d["snippet"],
                        "signals": fused[doc_id]["signals"], "score": round(fused[doc_id]["score"], 4),
                        **({"metadata_match": fused[doc_id]["metadata_match"]}
                           if "metadata_match" in fused[doc_id] else {}),
                        **{k: d["meta"][k] for k in ("path", "url", "title", "area", "pii", "status", "sections")
                           if d["meta"].get(k) not in (None, "", [])}})
        return out

    def _weigh_by_metadata(self, fused: dict, info: dict, kinds, filters) -> None:
        """Rank = text x metadata. Text is the fused score relative to the best one; records
        that meet the metadata but no text list join with a small text score. Both high ranks
        high; a strong text match with weak metadata, or the reverse, is pushed down."""
        best = max((e["score"] for e in fused.values()), default=0.0)
        floor = 0.1 * best if best else 1.0
        with self._conn() as c:
            for doc_id, kind, file, meta, body in c.execute(
                    "SELECT id, kind, file, meta, body FROM docs").fetchall():
                if doc_id in fused:
                    continue
                m = json.loads(meta)
                if matches(m, kind, kinds, filters) and metadata_match(m, filters):
                    info.setdefault(doc_id, {"kind": kind, "file": file, "meta": m,
                                             "snippet": _plain_snippet(body)})
                    fused[doc_id] = {"score": floor, "signals": ["metadata"]}
        best = max((e["score"] for e in fused.values()), default=0.0) or 1.0
        for doc_id, e in fused.items():
            m = metadata_match(info[doc_id]["meta"], filters) or 0.0
            e["metadata_match"] = round(m, 2)
            e["score"] = (e["score"] / best) * (SOFT_FLOOR + (1 - SOFT_FLOOR) * m)

    def _visible(self, doc_id: str, info: dict, kinds, filters) -> bool:
        if doc_id not in info:
            d = self.doc(doc_id)
            if not d:
                return False
            info[doc_id] = {"kind": d["kind"], "file": d["file"], "meta": d["meta"],
                            "snippet": _plain_snippet(d["body"])}
        d = info[doc_id]
        return matches(d["meta"], d["kind"], kinds, filters)


def _plain_snippet(body: str, words: int = 28) -> str:
    parts = (body or "").split()
    return " ".join(parts[:words]) + (" …" if len(parts) > words else "")
