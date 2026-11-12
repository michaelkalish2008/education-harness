"""TurboQuant-style vector compression (MSE stage), in NumPy.

Each vector is compressed on its own: a fixed random rotation, then scalar
quantization of every coordinate against a codebook computed from the math
(Lloyd-Max for the coordinate distribution after rotation), not learned from
the data. Nothing is trained on the learner's records, so adding or changing
one record never affects any other row.

After a random rotation, each coordinate of a unit vector in d dimensions is
close to normal with variance 1/d for the dimensions used here (384+); the
codebook uses that Gaussian approximation. Scoring is asymmetric: the query is
rotated but not quantized, and compared with the dequantized codes.

Reference: Zandieh, Daliri, Hadian, Mirrokni, "TurboQuant: Online Vector
Quantization with Near-optimal Distortion Rate" (ICLR 2026), arXiv:2504.19874.
"""

from __future__ import annotations

import math
from functools import lru_cache

import numpy as np


@lru_cache(maxsize=None)
def _lloyd_max_gaussian(levels: int, iters: int = 200) -> np.ndarray:
    """Optimal scalar quantizer centroids for a standard normal, computed numerically."""
    grid = np.linspace(-6.0, 6.0, 200_001)
    pdf = np.exp(-0.5 * grid ** 2)
    c = np.quantile(np.random.default_rng(0).standard_normal(200_000), (np.arange(levels) + 0.5) / levels)
    for _ in range(iters):
        b = (c[:-1] + c[1:]) / 2
        idx = np.searchsorted(b, grid)
        num = np.bincount(idx, weights=grid * pdf, minlength=levels)
        den = np.bincount(idx, weights=pdf, minlength=levels)
        c = num / np.maximum(den, 1e-300)
    return tuple(np.sort(c))


class TurboQuant:
    def __init__(self, dim: int, bits: int = 4, seed: int = 0):
        if bits not in (2, 4, 8):
            raise ValueError("bits must be 2, 4 or 8")
        self.dim, self.bits, self.seed = dim, bits, seed
        rng = np.random.default_rng(seed)
        q, r = np.linalg.qr(rng.standard_normal((dim, dim)))
        self.rotation = q * np.sign(np.diag(r))  # a uniformly random orthogonal matrix
        self.centroids = (np.array(_lloyd_max_gaussian(2 ** bits)) / math.sqrt(dim)).astype(np.float32)
        self.bounds = (self.centroids[:-1] + self.centroids[1:]) / 2
        self.per_byte = 8 // bits

    @property
    def code_bytes(self) -> int:
        return math.ceil(self.dim / self.per_byte)

    def settings(self) -> dict:
        return {"dim": self.dim, "bits": self.bits, "seed": self.seed}

    def encode(self, v: np.ndarray) -> tuple[bytes, float]:
        """Return packed codes and the vector's norm."""
        v = np.asarray(v, dtype=np.float64)
        norm = float(np.linalg.norm(v))
        if norm == 0:
            return bytes(self.code_bytes), 0.0
        y = self.rotation @ (v / norm)
        codes = np.searchsorted(self.bounds, y).astype(np.uint8)
        pad = (-len(codes)) % self.per_byte
        codes = np.concatenate([codes, np.zeros(pad, np.uint8)]).reshape(-1, self.per_byte)
        packed = np.zeros(len(codes), np.uint8)
        for i in range(self.per_byte):
            packed |= codes[:, i] << (i * self.bits)
        return packed.tobytes(), norm

    def decode_many(self, blobs: list[bytes]) -> np.ndarray:
        """Dequantize packed codes into rotated unit vectors (rows)."""
        if not blobs:
            return np.zeros((0, self.dim), np.float32)
        b = np.frombuffer(b"".join(blobs), np.uint8).reshape(len(blobs), -1)
        mask = (1 << self.bits) - 1
        codes = np.stack([(b >> (i * self.bits)) & mask for i in range(self.per_byte)], axis=-1)
        codes = codes.reshape(len(blobs), -1)[:, : self.dim]
        return self.centroids[codes]

    def scores(self, query: np.ndarray, blobs: list[bytes]) -> np.ndarray:
        """Approximate cosine similarity of the query with each stored vector."""
        q = np.asarray(query, dtype=np.float64)
        n = np.linalg.norm(q)
        if n == 0 or not blobs:
            return np.zeros(len(blobs))
        qr = (self.rotation @ (q / n)).astype(np.float32)
        return self.decode_many(blobs) @ qr
