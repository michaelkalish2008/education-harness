"""Deterministic, provider-independent fields: pii, secrets, wc, lang.

Ported from cat (catalog/derive.py). These are pure functions of content, so they
are recomputed from the file rather than trusted from any model. Regex-grade
hints, explicitly not compliance-grade. Bump DERIVE_VERSION whenever the rules
change; records pinned to an older version get their flags re-derived.
"""

from __future__ import annotations

import re
from pathlib import Path

DERIVE_VERSION = "1"

_EMAIL = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_PHONE = re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")

_SECRET_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),                       # AWS access key id
    re.compile(r"sk-[A-Za-z0-9]{20,}"),                    # OpenAI-style
    re.compile(r"sk-ant-[A-Za-z0-9\-_]{20,}"),             # Anthropic-style
    re.compile(r"ghp_[A-Za-z0-9]{36}"),                    # GitHub PAT
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"(?i)(?:api[_-]?key|secret|password|token)\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
]

TEXT_TYPES = {
    ".md": "markdown", ".txt": "text", ".rst": "text", ".tex": "latex", ".html": "html",
    ".htm": "html", ".csv": "csv", ".json": "json", ".yaml": "yaml", ".yml": "yaml",
    ".py": "python", ".ipynb": "notebook", ".r": "r", ".sql": "sql",
}
BINARY_TYPES = {".pdf": "pdf", ".docx": "docx", ".epub": "epub", ".png": "image", ".jpg": "image",
                ".jpeg": "image", ".heic": "image", ".webp": "image", ".gif": "image",
                ".mp4": "video", ".mov": "video", ".m4v": "video", ".webm": "video"}


def has_pii(content: str) -> bool:
    return bool(_EMAIL.search(content) or _SSN.search(content) or _PHONE.search(content))


def has_secrets(content: str) -> bool:
    return any(p.search(content) for p in _SECRET_PATTERNS)


def kind_of(path: str | Path) -> str:
    ext = Path(path).suffix.lower()
    return TEXT_TYPES.get(ext) or BINARY_TYPES.get(ext) or "other"


def is_text(path: str | Path) -> bool:
    return Path(path).suffix.lower() in TEXT_TYPES


def derive(path: str | Path, content: str | None) -> dict:
    """Flags for a file. Binary files (PDFs and the like) get null flags: unknown, not clean."""
    if content is None:
        return {"pii": None, "secrets": None, "wc": None, "type": kind_of(path)}
    return {"pii": has_pii(content), "secrets": has_secrets(content), "wc": len(content.split()),
            "type": kind_of(path)}
