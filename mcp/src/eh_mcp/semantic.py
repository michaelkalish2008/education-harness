"""Opt-in semantic search: a small local embedding model plus TurboQuant storage.

The model runs only on the learner's computer. Turning the mode on installs the
``semantic`` extra into the server's own environment and downloads the model,
in the background, so the tool returns at once and keyword search keeps working.
"""

from __future__ import annotations

import hashlib
import os
import importlib
import importlib.util
import shutil
import subprocess
import sys
import threading
from pathlib import Path
from typing import Protocol

MODEL = "BAAI/bge-small-en-v1.5"  # 384 dimensions, quantized ONNX build served by fastembed
FASTEMBED = "fastembed==0.9.1"
NUMPY = "numpy>=1.26"


class Embedder(Protocol):
    name: str
    dim: int

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class FastEmbedder:
    dim = 384

    def __init__(self, cache_dir: Path):
        from fastembed import TextEmbedding  # imported only once the extra is installed
        self.name = MODEL
        self._model = TextEmbedding(MODEL, cache_dir=str(cache_dir))
        self.fingerprint = self._fingerprint(cache_dir)

    @staticmethod
    def _fingerprint(cache_dir: Path) -> str:
        """Hash of the downloaded model files, recorded on first use and checked after."""
        h = hashlib.sha256()
        for p in sorted(cache_dir.rglob("*.onnx")):
            h.update(p.name.encode())
            with p.open("rb") as f:
                for chunk in iter(lambda: f.read(1 << 20), b""):
                    h.update(chunk)
        return h.hexdigest()

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [list(map(float, v)) for v in self._model.embed(texts)]


def model_cache() -> Path:
    """One model download per computer, shared by every workspace."""
    return Path(os.environ.get("EH_MODEL_CACHE", Path.home() / ".cache" / "education-harness" / "model"))


def extra_installed() -> bool:
    try:
        importlib.import_module("fastembed")
        importlib.import_module("numpy")
        return True
    except ImportError:
        return False


def _install_command() -> list[str]:
    """pip if this environment has it; otherwise uv (environments made by uv have no pip)."""
    if importlib.util.find_spec("pip") is not None:
        return [sys.executable, "-m", "pip", "install", FASTEMBED, NUMPY]
    uv = shutil.which("uv")
    if uv:
        return [uv, "pip", "install", "--python", sys.executable, FASTEMBED, NUMPY]
    raise RuntimeError("neither pip nor uv is available to install the semantic extra")


class SemanticSetup:
    """Background install and model download; status is readable at any time."""

    def __init__(self, index, private: Path):
        self.index = index
        self.private = private
        self.state = "off"
        self.detail = ""
        self._thread: threading.Thread | None = None

    @property
    def log_path(self) -> Path:
        return self.private / "index" / "semantic-setup.log"

    def start(self, embedder_factory=None) -> dict:
        if self._thread and self._thread.is_alive():
            return self.status()
        self.state, self.detail = "installing", "Setting up smart search in the background."
        self._thread = threading.Thread(target=self._run, args=(embedder_factory,), daemon=True)
        self._thread.start()
        return self.status()

    def _run(self, embedder_factory) -> None:
        try:
            if embedder_factory is None:
                if not extra_installed():
                    self.log_path.parent.mkdir(parents=True, exist_ok=True)
                    with self.log_path.open("a") as log:
                        subprocess.run(_install_command(), stdout=log, stderr=subprocess.STDOUT, check=True)
                    importlib.invalidate_caches()
                self.state, self.detail = "downloading", "Downloading the local model (about 70 MB, once; it stays on this computer)."
                embedder = FastEmbedder(model_cache())
            else:
                embedder = embedder_factory()
            self.state, self.detail = "indexing", "Indexing your records."
            self.index.enable_semantic(embedder)
            self.state, self.detail = "on", "Smart search is on."
        except Exception as e:  # any failure leaves keyword search in place
            self.state = "failed"
            self.detail = (f"Smart search couldn't be set up ({type(e).__name__}: {e}). "
                           "Keyword search still works; you can try again later.")
            self.index.disable_semantic()

    def status(self) -> dict:
        return {"semantic": self.state, "detail": self.detail, "mode": self.index.mode()}
