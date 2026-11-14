"""Generate a private, self-contained 3D PCA explorer for the local TurboQuant knowledge base."""
from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

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
        return self.ws.index.pca_projection(scope, max_points)

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
            path = self.ws.root / "KNOWLEDGE-MAP.html"
            path.write_text(page, encoding="utf-8")
            out["file"] = str(path)
        return out
