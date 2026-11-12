from __future__ import annotations

import json
import re
import shutil
import sqlite3
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml


ROLES = {"tutor", "mentor", "validator", "organizer", "lesson-planner"}
STATUSES = {"not-started", "seen", "drafted", "defended"}
REVEAL_LEVELS = {"hint", "answer", "method"}


class HarnessError(ValueError):
    pass


class Harness:
    def __init__(self, workspace: str | Path):
        root = Path(workspace).expanduser().resolve()
        self.root = root if root.name == "learning" else root / "learning"

    def init_project(
        self,
        slug: str,
        question: str | None = None,
        source: str | Path | None = None,
    ) -> dict[str, Any]:
        slug = self._slug(slug)
        project = self.root / "projects" / slug
        if project.exists():
            raise HarnessError(f"Project already exists: {slug}")
        self._init_workspace()
        if source:
            source_path = Path(source).expanduser().resolve()
            if not source_path.is_dir():
                raise HarnessError(f"Default project not found: {source_path}")
            shutil.copytree(source_path, project)
        else:
            for folder in ("data", "solutions", "work", "portfolio"):
                (project / folder).mkdir(parents=True, exist_ok=True)
            self._write_yaml(
                project / "program.yaml",
                {
                    "schema": 1,
                    "project": {"question": question or ""},
                    "portfolio_addition": {},
                    "steps": [],
                    "constellation": {},
                },
            )
        program = self._read_yaml(project / "program.yaml")
        progress = {
            "schema": 1,
            "project": slug,
            "steps": {
                step["id"]: {"status": "not-started", "revealed": []}
                for step in program.get("steps", [])
            },
        }
        self._write_yaml(project / "progress.yaml", progress)
        (project / "commitment.md").touch(exist_ok=True)
        return {"project": slug, "path": str(project), "created": True}

    def get_plan(self, project: str) -> dict[str, Any]:
        return self._read_yaml(self._project(project) / "program.yaml")

    def get_progress(self, project: str, role: str, step_id: str | None = None) -> dict[str, Any]:
        role = self._role(role)
        progress = self._read_yaml(self._project(project) / "progress.yaml")
        base = self.root / ".private" / "handoff" / self._slug(project)
        folders = [base / self._slug(step_id)] if step_id else list(base.glob("*")) if base.exists() else []
        notes = []
        for folder in folders:
            for path in sorted(folder.glob("note-*.yaml")):
                note = self._read_yaml(path)
                if note.get("to") == role and note.get("status", "open") == "open":
                    notes.append(note | {"path": str(path.relative_to(self.root))})
        return {"progress": progress, "notes": notes}

    def write_solution(
        self,
        project: str,
        step_id: str,
        hints: list[str],
        method: str,
        follow_on_problems: list[dict[str, str]],
        caller_role: str,
    ) -> dict[str, Any]:
        if self._role(caller_role) != "lesson-planner":
            raise HarnessError("Only the lesson-planner may write solutions")
        if len(follow_on_problems) < 2 or any(
            not follow_on.get("problem", "").strip() for follow_on in follow_on_problems
        ):
            raise HarnessError("Each solution needs at least two nonblank follow-on problems")
        self._step(project, step_id)
        path = self._project(project) / "solutions" / f"{self._slug(step_id)}.yaml"
        self._write_yaml(path, {"schema": 1, "step": step_id, "hints": hints, "method": method, "follow_on_problems": follow_on_problems})
        return {"saved": str(path.relative_to(self.root))}

    def record_attempt(self, project: str, step_id: str, text: str, kind: str = "attempt") -> dict[str, Any]:
        if not text.strip():
            raise HarnessError("An attempt cannot be blank")
        self._step(project, step_id)
        path = self._dated_path("attempts", project, step_id, kind, ".md")
        path.write_text(text.strip() + "\n", encoding="utf-8")
        self._index(path, text, {"project": project, "step": step_id, "outcome": kind})
        return {"saved": str(path.relative_to(self.root))}

    def reveal_solution(self, project: str, step_id: str, level: str, hint_number: int = 1) -> dict[str, Any]:
        if level not in REVEAL_LEVELS:
            raise HarnessError(f"Reveal level must be one of {sorted(REVEAL_LEVELS)}")
        step = self._step(project, step_id)
        solution = self._read_yaml(self._project(project) / "solutions" / f"{self._slug(step_id)}.yaml")
        if level == "hint":
            hints = solution.get("hints", [])
            if not 1 <= hint_number <= len(hints):
                raise HarnessError("That hint does not exist")
            content: Any = hints[hint_number - 1]
        elif level == "answer":
            if "answer" not in step:
                raise HarnessError("This step has no shown answer")
            content = step["answer"]
        else:
            content = solution.get("method", "")
        follow_ons = solution.get("follow_on_problems", [])
        if not follow_ons or not follow_ons[0].get("problem", "").strip():
            raise HarnessError("A reveal cannot be served without a follow-on problem")
        progress_path = self._project(project) / "progress.yaml"
        progress = self._read_yaml(progress_path)
        state = progress.setdefault("steps", {}).setdefault(step_id, {"status": "not-started", "revealed": []})
        marker = level if level != "hint" else f"hint-{hint_number}"
        if marker not in state.setdefault("revealed", []):
            state["revealed"].append(marker)
        self._write_yaml(progress_path, progress)
        return {"level": level, "content": content, "follow_on": {"problem": follow_ons[0]["problem"]}}

    def record_defense(self, project: str, step_id: str, learner_words: str, parked_questions: list[str] | None = None) -> dict[str, Any]:
        if not learner_words.strip():
            raise HarnessError("A defense must contain the learner's own words")
        self._step(project, step_id)
        path = self._dated_path("handoff", project, step_id, "defense", ".yaml")
        self._write_yaml(path, {"schema": 1, "learner_words": learner_words.strip(), "parked_questions": parked_questions or [], "reviewed_by_learner": True})
        self._index(path, learner_words, {"project": project, "step": step_id, "outcome": "defense"})
        return {"saved": str(path.relative_to(self.root))}

    def post_note(self, project: str, step_id: str, to_role: str, from_role: str, text: str) -> dict[str, Any]:
        to_role, from_role = self._role(to_role), self._role(from_role)
        if not text.strip():
            raise HarnessError("A note cannot be blank")
        self._step(project, step_id)
        path = self._dated_path("handoff", project, step_id, "note", ".yaml")
        note = {"schema": 1, "to": to_role, "from": from_role, "status": "open", "text": text.strip()}
        self._write_yaml(path, note)
        self._index(path, text, {"project": project, "step": step_id})
        return {"saved": str(path.relative_to(self.root))}

    def set_status(self, project: str, step_id: str, status: str, caller_role: str, evidence: dict[str, Any] | None = None) -> dict[str, Any]:
        if status not in STATUSES:
            raise HarnessError(f"Status must be one of {sorted(STATUSES)}")
        role = self._role(caller_role)
        evidence = evidence or {}
        if status == "defended":
            if role != "validator":
                raise HarnessError("Only the validator may mark a step defended")
            required = {"explained_work", "three_questions", "path_not_taken", "named_limit", "unseen_problem"}
            if not all(evidence.get(item) for item in required):
                raise HarnessError(f"Defended requires evidence for {sorted(required)}")
        if status == "drafted" and not evidence.get("follow_on_attempt"):
            raise HarnessError("Drafted requires an attempt on a follow-on problem")
        progress_path = self._project(project) / "progress.yaml"
        progress = self._read_yaml(progress_path)
        state = progress.setdefault("steps", {}).setdefault(step_id, {"revealed": []})
        state["status"] = status
        state["evidence"] = evidence
        self._write_yaml(progress_path, progress)
        return {"step": step_id, "status": status}

    def propose_profile_change(self, proposal: dict[str, Any], accepted: bool = False) -> dict[str, Any]:
        path = self.root / ".private" / "proposals.yaml"
        data = self._read_yaml(path)
        item = {"id": self._stamp(), "proposal": proposal, "status": "accepted" if accepted else "pending"}
        data.setdefault("proposals", []).append(item)
        self._write_yaml(path, data)
        if accepted:
            learner_path = self.root / ".private" / "learner.yaml"
            learner = self._read_yaml(learner_path)
            learner.update(proposal)
            self._write_yaml(learner_path, learner)
        return item

    def log_session(self, text: str) -> dict[str, Any]:
        if not text.strip():
            raise HarnessError("A session log cannot be blank")
        now = datetime.now(UTC)
        path = self.root / ".private" / "log" / now.strftime("%Y") / now.strftime("%m") / f"{self._stamp()}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text.strip() + "\n", encoding="utf-8")
        self._index(path, text, {"outcome": "session"})
        return {"saved": str(path.relative_to(self.root))}

    def add_diary_entry(self, text: str, tags: dict[str, str] | None = None) -> dict[str, Any]:
        if not text.strip():
            raise HarnessError("A diary entry cannot be blank")
        now = datetime.now(UTC)
        path = self.root / ".private" / "diary" / now.strftime("%Y") / now.strftime("%m") / f"{self._stamp()}-entry.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text.strip() + "\n", encoding="utf-8")
        self._index(path, text, tags or {})
        return {"saved": str(path.relative_to(self.root))}

    def check_links(self, urls: list[str], timeout: float = 8) -> list[dict[str, Any]]:
        results = []
        for url in urls:
            try:
                request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "education-harness/0.1"})
                with urllib.request.urlopen(request, timeout=timeout) as response:
                    results.append({"url": url, "ok": 200 <= response.status < 400, "status": response.status})
            except Exception as exc:
                results.append({"url": url, "ok": False, "error": str(exc)})
        return results

    def search_memory(self, query: str, tags: dict[str, str] | None = None, limit: int = 8) -> list[dict[str, Any]]:
        db = self._db()
        clauses, params = ["memory_fts MATCH ?"], [query]
        for key, value in (tags or {}).items():
            clauses.append("json_extract(memory.tags, ?) = ?")
            params.extend([f"$.{key}", value])
        params.append(limit)
        rows = db.execute(
            f"SELECT memory.id, memory.path, snippet(memory_fts, 0, '[', ']', '...', 18) AS snippet, memory.tags FROM memory_fts JOIN memory ON memory_fts.rowid = memory.rowid WHERE {' AND '.join(clauses)} ORDER BY bm25(memory_fts) LIMIT ?",
            params,
        ).fetchall()
        return [{"id": row[0], "path": row[1], "snippet": row[2], "tags": json.loads(row[3])} for row in rows]

    def extract_learnings(self, project: str, learning: dict[str, Any]) -> dict[str, Any]:
        source = learning.get("source")
        if not source or not (self.root / source).is_file():
            raise HarnessError("A learning must link to an existing source")
        concepts = set(learning.get("tags", {}).get("concept", []))
        valid = {concept for step in self.get_plan(project).get("steps", []) for concept in step.get("concepts", [])}
        if not concepts or not concepts <= valid:
            raise HarnessError("Learning concept tags must come from program.yaml")
        path = self._dated_path("learnings", project, None, "learning", ".yaml")
        self._write_yaml(path, {"schema": 1, **learning})
        self._index(path, learning.get("what_happened", ""), learning.get("tags", {}))
        return {"saved": str(path.relative_to(self.root))}

    def enable_semantic_search(self, enabled: bool) -> dict[str, Any]:
        path = self.root / ".private" / "index" / "settings.yaml"
        settings = self._read_yaml(path) if path.exists() else {"schema": 1}
        settings["semantic_requested"] = enabled
        settings["semantic_status"] = "not-installed" if enabled else "off"
        self._write_yaml(path, settings)
        return settings

    def _init_workspace(self) -> None:
        for folder in ("inbox", "projects", ".private/index"):
            (self.root / folder).mkdir(parents=True, exist_ok=True)
        ignore = self.root / ".gitignore"
        if not ignore.exists():
            ignore.write_text(".private/\n", encoding="utf-8")
        for name, value in (("learner.yaml", {"schema": 1}), ("proposals.yaml", {"schema": 1, "proposals": []})):
            path = self.root / ".private" / name
            if not path.exists():
                self._write_yaml(path, value)
        self._db().close()

    def _project(self, project: str) -> Path:
        path = self.root / "projects" / self._slug(project)
        if not path.is_dir():
            raise HarnessError(f"Project not found: {project}")
        return path

    def _step(self, project: str, step_id: str) -> dict[str, Any]:
        for step in self.get_plan(project).get("steps", []):
            if step.get("id") == step_id:
                return step
        raise HarnessError(f"Step not found: {step_id}")

    def _dated_path(self, category: str, project: str | None, step_id: str | None, prefix: str, suffix: str) -> Path:
        path = self.root / ".private" / category
        if project:
            path /= self._slug(project)
        if step_id:
            path /= self._slug(step_id)
        path.mkdir(parents=True, exist_ok=True)
        return path / f"{prefix}-{self._stamp()}{suffix}"

    def _index(self, path: Path, text: str, tags: dict[str, Any]) -> None:
        db = self._db()
        record_id = str(path.relative_to(self.root))
        db.execute("INSERT OR REPLACE INTO memory(id, path, text, tags) VALUES (?, ?, ?, ?)", (record_id, record_id, text.strip(), json.dumps(tags, sort_keys=True)))
        db.commit()
        db.close()

    def _db(self) -> sqlite3.Connection:
        path = self.root / ".private" / "index" / "memory.sqlite3"
        path.parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(path)
        db.execute("CREATE TABLE IF NOT EXISTS memory (id TEXT UNIQUE NOT NULL, path TEXT NOT NULL, text TEXT NOT NULL, tags TEXT NOT NULL)")
        db.execute("CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(text, content='memory', content_rowid='rowid')")
        db.executescript("CREATE TRIGGER IF NOT EXISTS memory_ai AFTER INSERT ON memory BEGIN INSERT INTO memory_fts(rowid, text) VALUES (new.rowid, new.text); END; CREATE TRIGGER IF NOT EXISTS memory_ad AFTER DELETE ON memory BEGIN INSERT INTO memory_fts(memory_fts, rowid, text) VALUES('delete', old.rowid, old.text); END; CREATE TRIGGER IF NOT EXISTS memory_au AFTER UPDATE ON memory BEGIN INSERT INTO memory_fts(memory_fts, rowid, text) VALUES('delete', old.rowid, old.text); INSERT INTO memory_fts(rowid, text) VALUES (new.rowid, new.text); END;")
        return db

    @staticmethod
    def _read_yaml(path: Path) -> dict[str, Any]:
        if not path.is_file():
            raise HarnessError(f"Required file not found: {path}")
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("schema") != 1:
            raise HarnessError(f"Unsupported or missing schema in {path}")
        return data

    @staticmethod
    def _write_yaml(path: Path, data: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")

    @staticmethod
    def _slug(value: str) -> str:
        if not value or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value):
            raise HarnessError("Names must be lowercase, hyphenated, and contain no spaces")
        return value

    @staticmethod
    def _role(role: str) -> str:
        if role not in ROLES:
            raise HarnessError(f"Role must be one of {sorted(ROLES)}")
        return role

    @staticmethod
    def _stamp() -> str:
        return datetime.now(UTC).strftime("%Y-%m-%d-%H%M%S-%f")

