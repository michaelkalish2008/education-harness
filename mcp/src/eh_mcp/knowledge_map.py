"""Generate a private, self-contained 3D PCA explorer for the local TurboQuant knowledge base."""
from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from .core import Workspace

PLACEHOLDER = "__KNOWLEDGE_MAP_DATA__"


def template_path() -> Path:
    return Path(__file__).resolve().parents[3] / "skills" / "start" / "knowledge-map.html"


class KnowledgeMap:
    def __init__(self, ws: "Workspace"):
        self.ws = ws

    def data(self, scope: str = "domain", max_points: int = 600) -> dict:
        if scope not in ("domain", "reflection", "reference", "meta", "all"):
            from .core import HarnessError
            raise HarnessError("scope must be domain, reflection, reference, meta or all.")
        learner_path = self.ws.private / "learner.yaml"
        learner = yaml.safe_load(learner_path.read_text(encoding="utf-8")) if learner_path.exists() else {}
        learner = learner or {}
        context, school_level = learner.get("learning_context"), str(learner.get("school_level", "")).lower()
        min_grade = None
        if context != "school" or any(x in school_level for x in ("high", "college", "university", "adult")):
            min_grade = 9
        data = self.ws.index.pca_projection(scope, max_points, standards_min_grade=min_grade)
        data["standards_min_grade"] = min_grade
        data["standards_default_note"] = ("High-school-and-above standards are shown by default for this learning context."
                                           if min_grade else "Standards follow the learner's school level.")
        return data

    def render(self, data: dict) -> str | None:
        path = template_path()
        if not path.exists():
            return None
        payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
        return path.read_text(encoding="utf-8").replace(PLACEHOLDER, payload, 1)

    def write(self, scope: str = "domain", max_points: int = 600) -> dict:
        from .core import HarnessError
        data = self.data(scope, max_points)
        if not data.get("points"):
            raise HarnessError(data.get("note", "No vectors are available for a knowledge map."))
        page = self.render(data)
        out: dict[str, Any] = {"data": data, "template": str(template_path())}
        if page is not None:
            path = self.ws.views_dir / "KNOWLEDGE-MAP.html"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(page, encoding="utf-8")
            self.ws.retire_root_page("KNOWLEDGE-MAP.html")
            out["file"] = str(path)
        return out
