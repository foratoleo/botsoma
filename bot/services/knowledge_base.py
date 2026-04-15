"""
Knowledge Base service with FAISS embedding search.

Loads all .md and .txt files from the configured knowledge directory,
splits them into sections by headings, and provides semantic retrieval
using sentence-transformers embeddings and FAISS IndexFlatIP.

Falls back to keyword-based search if embedding dependencies are unavailable.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

import structlog

from bot.config import (
    EMBEDDING_DEVICE,
    EMBEDDING_MODEL,
    EMBEDDING_TOP_K,
    FAISS_INDEX_PATH,
    HYBRID_RRF_K,
    HYBRID_SEARCH_ENABLED,
    HYBRID_SPARSE_TOP_K,
    KNOWLEDGE_BASE_DIR,
)

try:
    import numpy as np

    _NUMPY_AVAILABLE = True
except ImportError:
    _NUMPY_AVAILABLE = False

logger = structlog.get_logger(__name__)


class KnowledgeBase:
    """Base knowledge base with heading-based document splitting.

    Provides the document loading, splitting, and keyword search
    infrastructure. Subclassed by EmbeddingKnowledgeBase for semantic
    search via FAISS.
    """

    EXCLUDED_DOCS: set[str] = set()

    def __init__(self, base_dir: Path = KNOWLEDGE_BASE_DIR):
        self.base_dir = Path(base_dir)
        self._sections: list[dict] = []
        self._loaded = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self) -> int:
        """Load (or reload) all documents from disk. Returns section count."""
        self._sections.clear()
        if not self.base_dir.is_dir():
            logger.warning("kb_directory_not_found", path=str(self.base_dir))
            return 0

        count = 0
        for filepath in sorted(self.base_dir.rglob("*")):
            if filepath.suffix.lower() in (".md", ".txt", ".markdown"):
                if filepath.name in self.EXCLUDED_DOCS:
                    logger.debug("kb_skip_excluded", filename=filepath.name)
                    continue
                count += self._load_file(filepath)

        self._loaded = True
        logger.info(
            "kb_loaded",
            sections=len(self._sections),
            files=count,
        )
        return len(self._sections)

    def search(self, query: str, max_results: int = 5) -> list[dict]:
        """Return top sections matching *query* by keyword overlap.

        Each result is a dict with keys:
          - source: relative file path
          - heading: section heading (or first line)
          - content: section text
          - score: keyword overlap count
        """
        if not self._loaded:
            self.load()

        query_tokens = set(self._tokenize(query))
        if not query_tokens:
            return []

        scored = []
        for section in self._sections:
            section_tokens = set(section["tokens"])
            overlap = len(query_tokens & section_tokens)
            if overlap > 0:
                scored.append({**section, "score": overlap})

        scored.sort(key=lambda s: s["score"], reverse=True)
        return scored[:max_results]

    def format_context(self, query: str, max_results: int = 5) -> str:
        """Return a formatted string of relevant sections for LLM context."""
        results = self.search(query, max_results)
        if not results:
            return ""

        parts = []
        for r in results:
            parts.append(f"### Fonte: {r['source']}")
            if r["heading"]:
                parts.append(f"## {r['heading']}")
            parts.append(r["content"])
            parts.append("")

        return "\n".join(parts)

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def section_count(self) -> int:
        return len(self._sections)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Lowercase, strip punctuation, split on whitespace."""
        return re.findall(r"[a-záàâãéèêíïóôõöúçñ]{2,}", text.lower())

    def _load_file(self, filepath: Path) -> int:
        """Parse a single file into heading-based sections."""
        try:
            text = filepath.read_text(encoding="utf-8")
        except Exception as exc:
            logger.error("kb_file_read_error", path=str(filepath), error=str(exc))
            return 0

        relative = filepath.relative_to(self.base_dir)
        sections = self._split_by_headings(text)

        for heading, content in sections:
            full_text = f"{heading}\n{content}" if heading else content
            self._sections.append(
                {
                    "source": str(relative),
                    "heading": heading,
                    "content": content.strip(),
                    "tokens": self._tokenize(full_text),
                }
            )

        logger.debug("kb_file_loaded", sections=len(sections), file=str(relative))
        return len(sections)

    @staticmethod
    def _split_by_headings(text: str) -> list[tuple[str, str]]:
        """Split markdown into sections by ## headings.

        Returns list of (heading, body) tuples.
        """
        pattern = re.compile(r"^(#{2,3})\s+(.+)$", re.MULTILINE)
        splits = list(pattern.finditer(text))

        if not splits:
            return [("", text)]

        sections = []
        for i, match in enumerate(splits):
            heading = match.group(2).strip()
            start = match.end()
            end = splits[i + 1].start() if i + 1 < len(splits) else len(text)
            body = text[start:end].strip()
            sections.append((heading, body))

        if splits[0].start() > 0:
            preamble = text[: splits[0].start()].strip()
            if preamble:
                sections.insert(0, ("", preamble))

        return sections


class EmbeddingKnowledgeBase(KnowledgeBase):
    """Knowledge base with FAISS embedding-based semantic search.

    Uses sentence-transformers to encode document sections into dense
    vectors and FAISS IndexFlatIP (inner product on L2-normalized
    vectors = cosine similarity) for fast nearest-neighbor retrieval.

    When hybrid search is enabled (default), combines dense FAISS
    results with sparse BM25 results using Reciprocal Rank Fusion
    (RRF) for higher-quality retrieval.

    Falls back to keyword search if FAISS or sentence-transformers are
    unavailable at import time.
    """

    def __init__(
        self,
        base_dir: Path = KNOWLEDGE_BASE_DIR,
        model_name: str = EMBEDDING_MODEL,
        device: str = EMBEDDING_DEVICE,
        index_cache_path: Path = FAISS_INDEX_PATH,
        top_k: int = EMBEDDING_TOP_K,
        hybrid_enabled: bool = HYBRID_SEARCH_ENABLED,
        hybrid_rrf_k: int = HYBRID_RRF_K,
        hybrid_sparse_top_k: int = HYBRID_SPARSE_TOP_K,
    ):
        super().__init__(base_dir)
        self._model_name = model_name
        self._device = device
        self._index_cache_path = Path(index_cache_path)
        self._top_k = top_k
        self._hybrid_enabled = hybrid_enabled
        self._hybrid_rrf_k = hybrid_rrf_k
        self._hybrid_sparse_top_k = hybrid_sparse_top_k

        self._model = None
        self._index = None
        self._embeddings = None  # Optional[np.ndarray] when numpy available
        self._embedding_dim: int = 0
        self._faiss_available = False
        self._hybrid_retriever = None

        self._init_embedding_model()
        self._init_hybrid_retriever()

    def _init_embedding_model(self) -> None:
        """Initialize the sentence-transformers model and verify FAISS."""
        try:
            from sentence_transformers import SentenceTransformer
            import faiss  # noqa: F401

            self._model = SentenceTransformer(self._model_name, device=self._device)
            self._embedding_dim = self._model.get_sentence_embedding_dimension()
            self._faiss_available = True
            logger.info(
                "embedding_model_loaded",
                model=self._model_name,
                dim=self._embedding_dim,
                device=self._device,
            )
        except ImportError as exc:
            logger.warning(
                "embedding_deps_unavailable",
                error=str(exc),
                fallback="keyword_search",
            )
            self._faiss_available = False

    def _init_hybrid_retriever(self) -> None:
        """Initialize hybrid retriever if enabled and BM25 is available."""
        if not self._hybrid_enabled:
            logger.info("hybrid_search_disabled")
            return

        try:
            from bot.services.hybrid_search import HybridRetriever

            self._hybrid_retriever = HybridRetriever(rrf_k=self._hybrid_rrf_k)
            logger.info(
                "hybrid_retriever_initialized",
                rrf_k=self._hybrid_rrf_k,
                sparse_top_k=self._hybrid_sparse_top_k,
            )
        except Exception as exc:
            logger.warning(
                "hybrid_retriever_init_failed",
                error=str(exc),
                fallback="dense_only",
            )
            self._hybrid_retriever = None

    def load(self) -> int:
        """Load documents and build FAISS index + BM25 sparse index."""
        section_count = super().load()

        if not self._faiss_available or not self._sections:
            return section_count

        if self._try_load_cached_index():
            logger.info(
                "faiss_index_loaded_from_cache",
                path=str(self._index_cache_path),
            )
        else:
            self._build_index()
            self._save_cached_index()

        # Build BM25 sparse index for hybrid search
        self._build_sparse_index()

        return section_count

    def _build_index(self) -> None:
        """Encode all sections and build FAISS IndexFlatIP."""
        import faiss

        texts = self._section_texts()
        logger.info(
            "encoding_sections",
            count=len(texts),
            model=self._model_name,
        )

        embeddings = self._model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
            batch_size=64,
        )
        self._embeddings = np.ascontiguousarray(embeddings, dtype=np.float32)

        self._index = faiss.IndexFlatIP(self._embedding_dim)
        self._index.add(self._embeddings)

        logger.info(
            "faiss_index_built",
            vectors=self._index.ntotal,
            dim=self._embedding_dim,
        )

    def _section_texts(self) -> list[str]:
        """Build searchable text for each section (heading + content)."""
        texts = []
        for section in self._sections:
            heading = section.get("heading", "")
            content = section.get("content", "")
            if heading:
                texts.append(f"{heading}\n{content}")
            else:
                texts.append(content)
        return texts

    def _try_load_cached_index(self) -> bool:
        """Attempt to load FAISS index and embeddings from disk cache."""
        import faiss

        index_file = self._index_cache_path / "index.faiss"
        embeddings_file = self._index_cache_path / "embeddings.npy"
        meta_file = self._index_cache_path / "meta.txt"

        if not all(f.exists() for f in (index_file, embeddings_file, meta_file)):
            return False

        try:
            cached_count = int(meta_file.read_text().strip())
            if cached_count != len(self._sections):
                logger.info(
                    "faiss_cache_stale",
                    cached=cached_count,
                    current=len(self._sections),
                )
                return False

            self._index = faiss.read_index(str(index_file))
            self._embeddings = np.load(str(embeddings_file))

            if self._index.ntotal != len(self._sections):
                logger.warning(
                    "faiss_cache_count_mismatch",
                    index_total=self._index.ntotal,
                    sections=len(self._sections),
                )
                self._index = None
                self._embeddings = None
                return False

            return True
        except Exception as exc:
            logger.warning("faiss_cache_load_failed", error=str(exc))
            return False

    def _save_cached_index(self) -> None:
        """Persist FAISS index and embeddings to disk for fast startup."""
        if self._index is None or self._embeddings is None:
            return

        try:
            import faiss

            self._index_cache_path.mkdir(parents=True, exist_ok=True)
            faiss.write_index(
                self._index,
                str(self._index_cache_path / "index.faiss"),
            )
            np.save(
                str(self._index_cache_path / "embeddings.npy"),
                self._embeddings,
            )
            (self._index_cache_path / "meta.txt").write_text(str(len(self._sections)))
            logger.info("faiss_index_cached", path=str(self._index_cache_path))
        except Exception as exc:
            logger.warning("faiss_cache_save_failed", error=str(exc))

    def _build_sparse_index(self) -> None:
        """Build BM25 sparse index for hybrid search."""
        if self._hybrid_retriever is None:
            return

        if not self._sections:
            return

        texts = self._section_texts()
        self._hybrid_retriever.build_sparse_index(texts)

    def _dense_search_raw(self, query: str, top_k: int) -> list[tuple[int, float]]:
        """Run FAISS dense search and return raw (index, score) pairs.

        Used internally by the hybrid search pipeline. Returns a wider
        result set for fusion with BM25.
        """
        query_embedding = self._model.encode(
            [query],
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        query_vector = np.ascontiguousarray(query_embedding, dtype=np.float32)

        k = min(top_k, self._index.ntotal)
        scores, indices = self._index.search(query_vector, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and idx < len(self._sections):
                results.append((int(idx), float(score)))

        return results

    def search(self, query: str, max_results: int = 5) -> list[dict]:
        """Search using hybrid (dense + sparse + RRF) or dense-only retrieval.

        When hybrid search is enabled and BM25 is available, combines
        FAISS cosine similarity with BM25 term matching via Reciprocal
        Rank Fusion. Otherwise falls back to dense-only or keyword search.

        Returns the same dict structure as KnowledgeBase.search() for
        full API compatibility:
          - source: relative file path
          - heading: section heading
          - content: section text
          - score: similarity or RRF score
          - retrieval_method: "hybrid", "dense", or "keyword" (when hybrid active)

        Falls back to keyword search if embeddings are unavailable.
        """
        if not self._loaded:
            self.load()

        if not self._faiss_available or self._index is None:
            return super().search(query, max_results)

        if self._index.ntotal == 0:
            return []

        # Retrieve more dense candidates for fusion
        dense_top_k = max(max_results * 3, self._hybrid_sparse_top_k)
        dense_results = self._dense_search_raw(query, top_k=dense_top_k)

        # Use hybrid retriever if available
        if self._hybrid_retriever is not None and self._hybrid_retriever.bm25_available:
            return self._hybrid_retriever.search(
                query=query,
                dense_results=dense_results,
                sections=self._sections,
                top_k=max_results,
                sparse_top_k=self._hybrid_sparse_top_k,
            )

        # Dense-only fallback
        results = []
        for idx, score in dense_results[:max_results]:
            section = self._sections[idx]
            results.append(
                {
                    "source": section["source"],
                    "heading": section["heading"],
                    "content": section["content"],
                    "score": score,
                }
            )

        return results

    def invalidate_cache(self) -> None:
        """Remove cached index files, forcing a full rebuild on next load."""
        if self._index_cache_path.exists():
            for f in self._index_cache_path.iterdir():
                f.unlink(missing_ok=True)
            self._index_cache_path.rmdir()
            logger.info(
                "faiss_cache_invalidated",
                path=str(self._index_cache_path),
            )

    @property
    def embedding_dim(self) -> int:
        """Dimensionality of the embedding vectors."""
        return self._embedding_dim

    @property
    def index_size(self) -> int:
        """Number of vectors currently in the FAISS index."""
        return self._index.ntotal if self._index else 0


# Module-level singleton
_kb: Optional[EmbeddingKnowledgeBase] = None


def get_knowledge_base() -> EmbeddingKnowledgeBase:
    """Return the singleton EmbeddingKnowledgeBase, loading on first access.

    Uses FAISS embedding search when sentence-transformers and faiss-cpu
    are installed. Falls back to keyword-based search automatically when
    those dependencies are missing.
    """
    global _kb
    if _kb is None:
        _kb = EmbeddingKnowledgeBase()
        _kb.load()
    return _kb
