"""Text embeddings for hybrid search, and an optional cross-encoder reranker (Phase 3).

Why: the Phase 2 answer misses were retrieval misses on paraphrases (eval/RESULTS.md, finding 1).

Optional: needs `pip install -e ".[embed]"` (fastembed, ONNX on CPU, no torch). Without it, search stays BM25.
Vectors are cached on disk per model, keyed by a hash of the text, so the index is embedded once and
re-embedded only where a document changed. The cache holds vectors, not text.

An embedder is any object with `name`, `embed_documents(texts) -> (n, d) array` and
`embed_query(text) -> (d,) array`, both L2-normalised (tests use an invented one). A reranker is any object
with `name` and `score(query, texts) -> list[float]` (higher = more relevant).
"""

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path
from typing import Protocol

from .index import DENSE_WEIGHT

DEFAULT_MODEL = "BAAI/bge-small-en-v1.5"
DEFAULT_RERANKER = "Xenova/ms-marco-MiniLM-L-6-v2"
# bge models embed queries with this prefix and documents without one
QUERY_PREFIX = {"BAAI/bge-small-en-v1.5": "Represent this sentence for searching relevant passages: ",
                "BAAI/bge-base-en-v1.5": "Represent this sentence for searching relevant passages: "}


class Embedder(Protocol):
    name: str

    def embed_documents(self, texts: list[str]): ...

    def embed_query(self, text: str): ...


class Reranker(Protocol):
    name: str

    def score(self, query: str, texts: list[str]) -> list[float]: ...


def default_cache_dir() -> Path:
    base = os.environ.get("SPACESTD_CACHE") or os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache"
    return Path(base) / "space-standards-mcp"


class FastEmbedder:
    """fastembed model with an on-disk vector cache."""

    def __init__(self, model: str = DEFAULT_MODEL, cache_dir: Path | None = None):
        import numpy as np
        from fastembed import TextEmbedding

        self.name = model
        self._np = np
        self._model = TextEmbedding(model)
        slug = re.sub(r"[^A-Za-z0-9.-]+", "_", model)
        self._cache_file = (cache_dir or default_cache_dir()) / f"vectors-{slug}.npz"
        self._cache: dict[str, object] = {}
        if self._cache_file.exists():
            data = np.load(self._cache_file)
            self._cache = dict(zip(data["keys"].tolist(), data["vecs"]))

    def _encode(self, texts: list[str]):
        np = self._np
        vecs = np.array(list(self._model.embed(texts)), dtype=np.float32).reshape(len(texts), -1)
        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        return vecs / np.where(norms == 0, 1, norms)

    def embed_documents(self, texts: list[str]):
        np = self._np
        keys = [hashlib.sha256(t.encode("utf-8")).hexdigest()[:32] for t in texts]
        todo = list(dict.fromkeys(k for k in keys if k not in self._cache))
        if todo:
            first = {k: t for k, t in zip(keys, texts)}
            for k, v in zip(todo, self._encode([first[k] for k in todo])):
                self._cache[k] = v
            self._cache_file.parent.mkdir(parents=True, exist_ok=True)
            tmp = self._cache_file.with_suffix(".tmp.npz")
            np.savez(tmp, keys=np.array(list(self._cache)), vecs=np.stack(list(self._cache.values())))
            tmp.replace(self._cache_file)
        if not keys:
            return np.zeros((0, 0), dtype=np.float32)
        return np.stack([self._cache[k] for k in keys])

    def embed_query(self, text: str):
        return self._encode([QUERY_PREFIX.get(self.name, "") + text])[0]


def load_embedder(model: str | None) -> Embedder | None:
    """FastEmbedder for `model` ('' / None / 'none' -> None, i.e. BM25 only)."""
    if not model or model.lower() in {"none", "off", "0"}:
        return None
    try:
        return FastEmbedder(DEFAULT_MODEL if model.lower() in {"1", "on", "default"} else model)
    except ImportError as e:
        raise SystemExit(f"Hybrid search needs the optional dependency: pip install -e \".[embed]\" ({e})") from e


class FastReranker:
    """fastembed cross-encoder: scores (query, record) pairs; used on the top of the ranking only."""

    def __init__(self, model: str = DEFAULT_RERANKER):
        from fastembed.rerank.cross_encoder import TextCrossEncoder

        self.name = model
        self._model = TextCrossEncoder(model)

    def score(self, query: str, texts: list[str]) -> list[float]:
        return [float(x) for x in self._model.rerank(query, texts)]


def load_reranker(model: str | None) -> Reranker | None:
    """FastReranker for `model` ('' / None / 'none' -> None)."""
    if not model or model.lower() in {"none", "off", "0"}:
        return None
    try:
        return FastReranker(DEFAULT_RERANKER if model.lower() in {"1", "on", "default"} else model)
    except ImportError as e:
        raise SystemExit(f"Reranking needs the optional dependency: pip install -e \".[embed]\" ({e})") from e


def index_options_from_env() -> dict:
    """StandardsIndex keyword arguments from SPACESTD_EMBED / SPACESTD_RERANK / SPACESTD_DENSE_WEIGHT."""
    return {"embedder": load_embedder(os.environ.get("SPACESTD_EMBED")),
            "reranker": load_reranker(os.environ.get("SPACESTD_RERANK")),
            "dense_weight": float(os.environ.get("SPACESTD_DENSE_WEIGHT") or DENSE_WEIGHT)}
