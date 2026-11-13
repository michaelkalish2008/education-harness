"""One-time download of the Learning Commons Knowledge Graph files needed for standards.

Run on the learner's computer: `eh-mcp --fetch-standards`. The files stay in a shared
cache; nothing is redistributed by the harness. Each record keeps its own license and
attribution statement, and the loader pins only openly licensed records.
"""

from __future__ import annotations

import os
import sys
import urllib.request
from pathlib import Path

BASE = "https://aidt-knowledge-graph-datasets-public-prod.s3.us-west-2.amazonaws.com/knowledge-graph/v1.0.0/json/"
FILES = ["StandardsFrameworkItem.json", "Relationships.json"]


def default_folder() -> Path:
    return Path(os.environ.get("EH_STANDARDS", Path.home() / ".cache" / "education-harness" / "standards"))


def fetch(*, quiet: bool = False) -> int:
    dest = default_folder()
    dest.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        target = dest / name
        if not quiet:
            print(f"Downloading {name} ...", flush=True)
        try:
            with urllib.request.urlopen(BASE + name, timeout=120) as r, target.open("wb") as f:
                total = 0
                while chunk := r.read(1 << 20):
                    f.write(chunk)
                    total += len(chunk)
            if not quiet:
                print(f"  {total / 1e6:.1f} MB -> {target}")
        except Exception as e:  # report plainly; nothing half-loaded is pinned
            if not quiet:
                print(f"  failed: {type(e).__name__}: {e}", file=sys.stderr)
            return 1
    if not quiet:
        print("Done. Standards are ready for the harness knowledge base.")
    return 0
