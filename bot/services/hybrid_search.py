"""
Hybrid search combining dense (FAISS) and sparse (BM25) retrieval
with optional cross-encoder reranking.

Implements BM25 sparse retrieval, Reciprocal Rank Fusion (RRF) for
merging ranked lists, cross-encoder reranking for precision, and a
HybridRetriever that orchestrates all stages to produce higher-quality
results than any single retriever alone.

Falls back gracefully to dense-only or keyword-only search when
BM25 dependencies are unavailable, and skips reranking when the
cross-encoder model is not installed.
"""

from __future__ import annotations

import re
from typing import Optional

import structlog

logger = structlog.get_logger(__name__)

try:
    from rank_bm25 import BM25Okapi

    _BM25_AVAILABLE = True
except ImportError:
    _BM25_AVAILABLE = False
    logger.warning(
        "bm25_deps_unavailable",
        fallback="dense_only",
        install="pip install rank-bm25",
    )

try:
    from sentence_transformers import CrossEncoder

    _CROSS_ENCODER_AVAILABLE = True
except ImportError:
    _CROSS_ENCODER_AVAILABLE = False
    logger.warning(
        "cross_encoder_deps_unavailable",
        fallback="no_reranking",
        install="pip install sentence-transformers",
    )


def _tokenize(text: str) -> list[str]:
    """Lowercase tokenizer matching KnowledgeBase._tokenize pattern."""
    return re.findall(r"[a-záàâãéèêíïóôõöúçñ]{2,}", text.lower())


class BM25Retriever:
    """Sparse retriever using BM25 (Okapi variant).

    Tokenizes document sections at build time and scores queries
    against the corpus using term-frequency / inverse-document-frequency
    weighting.
    """

    def __init__(self) -> None:
        self._index: Optional[BM25Okapi] = None
        self._corpus_size: int = 0

    @property
    def is_available(self) -> bool:
        """Whether the BM25 dependency is installed and index is built."""
        return _BM25_AVAILABLE and self._index is not None

    def build(self, texts: list[str]) -> None:
        """Build BM25 index from a list of document texts.

        Args:
            texts: List of document section texts (heading + content).
        """
        if not _BM25_AVAILABLE:
            logger.warning("bm25_build_skipped", reason="rank_bm25 not installed")
            return

        if not texts:
            logger.warning("bm25_build_skipped", reason="empty_corpus")
            return

        tokenized_corpus = [_tokenize(text) for text in texts]
        self._index = BM25Okapi(tokenized_corpus)
        self._corpus_size = len(texts)

        logger.info(
            "bm25_index_built",
            documents=self._corpus_size,
        )

    def search(self, query: str, top_k: int = 10) -> list[tuple[int, float]]:
        """Return ranked (index, score) pairs for the query.

        Args:
            query: User search query.
            top_k: Maximum number of results.

        Returns:
            List of (document_index, bm25_score) sorted by score descending.
        """
        if not self.is_available:
            return []

        query_tokens = _tokenize(query)
        if not query_tokens:
            return []

        scores = self._index.get_scores(query_tokens)

        # Build (index, score) pairs, filter zero scores
        scored = [
            (idx, float(score))
            for idx, score in enumerate(scores)
            if score > 0.0
        ]

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    @property
    def corpus_size(self) -> int:
        return self._corpus_size


def reciprocal_rank_fusion(
    *ranked_lists: list[tuple[int, float]],
    k: int = 60,
) -> list[tuple[int, float]]:
    """Merge multiple ranked lists using Reciprocal Rank Fusion (RRF).

    RRF assigns each document a score of 1/(k + rank) for each list it
    appears in, then sums scores across all lists. This produces a
    robust merged ranking that balances precision across retrieval
    strategies.

    Reference: Cormack, Clarke, Buettcher (2009) - "Reciprocal Rank
    Fusion outperforms Condorcet and individual Rank Learning Methods"

    Args:
        *ranked_lists: Variable number of ranked result lists. Each list
            contains (document_index, score) tuples sorted by score desc.
        k: RRF constant (default 60). Higher values reduce the influence
            of top-ranked documents. Standard value from the paper.

    Returns:
        Merged list of (document_index, rrf_score) sorted by rrf_score
        descending.
    """
    rrf_scores: dict[int, float] = {}

    for ranked_list in ranked_lists:
        for rank, (doc_idx, _original_score) in enumerate(ranked_list, start=1):
            rrf_scores[doc_idx] = rrf_scores.get(doc_idx, 0.0) + 1.0 / (k + rank)

    merged = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    return merged


class Reranker:
    """Cross-encoder reranker for precision improvement after retrieval.

    Uses a cross-encoder model (default: cross-encoder/ms-marco-MiniLM-L-6-v2)
    to jointly encode (query, document) pairs and produce fine-grained
    relevance scores. Cross-encoders are more accurate than bi-encoders
    because they attend to both query and document tokens simultaneously.

    The model is loaded lazily on first use to avoid slowing startup
    when reranking is disabled.
    """

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        top_k: int = 5,
    ) -> None:
        """Initialize the reranker.

        Args:
            model_name: HuggingFace model identifier for the cross-encoder.
                Default is ms-marco-MiniLM-L-6-v2 (~80MB, fast inference).
            top_k: Maximum number of results to return after reranking.
        """
        self._model_name = model_name
        self._top_k = top_k
        self._model: Optional[CrossEncoder] = None

    @property
    def is_available(self) -> bool:
        """Whether the cross-encoder dependency is installed."""
        return _CROSS_ENCODER_AVAILABLE

    @property
    def top_k(self) -> int:
        """Maximum number of results returned after reranking."""
        return self._top_k

    @top_k.setter
    def top_k(self, value: int) -> None:
        if value < 1:
            raise ValueError("top_k must be >= 1")
        self._top_k = value

    def _ensure_model(self) -> bool:
        """Lazy-load the cross-encoder model on first use.

        Returns:
            True if model is ready, False if loading failed.
        """
        if self._model is not None:
            return True

        if not _CROSS_ENCODER_AVAILABLE:
            return False

        try:
            self._model = CrossEncoder(self._model_name)
            logger.info(
                "cross_encoder_loaded",
                model=self._model_name,
            )
            return True
        except Exception as exc:
            logger.warning(
                "cross_encoder_load_failed",
                model=self._model_name,
                error=str(exc),
            )
            return False

    def rerank(
        self,
        query: str,
        results: list[dict],
        top_k: Optional[int] = None,
    ) -> list[dict]:
        """Rerank search results using cross-encoder scoring.

        Takes the output of hybrid or dense retrieval and re-scores each
        result by jointly encoding (query, document_text) through the
        cross-encoder. Returns results sorted by cross-encoder score.

        Args:
            query: User search query.
            results: List of result dicts from HybridRetriever or dense
                search. Each dict must have at least 'heading' and
                'content' keys.
            top_k: Override the default top_k for this call. If None,
                uses the instance default.

        Returns:
            Reranked list of result dicts, truncated to top_k. Each dict
            gains a 'reranker_score' key with the cross-encoder score
            and 'retrieval_method' is updated to include '+reranked'.
        """
        if not results:
            return results

        if not self._ensure_model():
            logger.debug("rerank_skipped", reason="model_unavailable")
            return results

        effective_top_k = top_k if top_k is not None else self._top_k

        # Build (query, document) pairs for cross-encoder
        pairs: list[list[str]] = []
        for result in results:
            heading = result.get("heading", "")
            content = result.get("content", "")
            doc_text = f"{heading}\n{content}" if heading else content
            pairs.append([query, doc_text])

        try:
            scores = self._model.predict(pairs)
        except Exception as exc:
            logger.warning(
                "rerank_prediction_failed",
                error=str(exc),
                fallback="original_order",
            )
            return results

        # Attach scores and sort by cross-encoder relevance
        scored_results = []
        for idx, result in enumerate(results):
            reranked = dict(result)
            reranked["reranker_score"] = float(scores[idx])
            method = reranked.get("retrieval_method", "unknown")
            if "+reranked" not in method:
                reranked["retrieval_method"] = f"{method}+reranked"
            scored_results.append(reranked)

        scored_results.sort(key=lambda x: x["reranker_score"], reverse=True)

        logger.debug(
            "rerank_completed",
            input_count=len(results),
            output_count=min(len(scored_results), effective_top_k),
            top_score=scored_results[0]["reranker_score"] if scored_results else 0.0,
        )

        return scored_results[:effective_top_k]


class HybridRetriever:
    """Orchestrates dense (FAISS) and sparse (BM25) retrieval with RRF fusion.

    Usage:
        retriever = HybridRetriever(rrf_k=60)
        retriever.build_sparse_index(section_texts)

        # At query time, pass dense results from FAISS:
        results = retriever.search(
            query="como resetar senha",
            dense_results=[(idx, score), ...],
            sections=sections_list,
            top_k=5,
        )
    """

    def __init__(
        self,
        rrf_k: int = 60,
        reranker_enabled: bool = False,
        reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        reranker_top_k: int = 5,
    ) -> None:
        """Initialize hybrid retriever.

        Args:
            rrf_k: RRF fusion constant. Default 60 (standard from paper).
            reranker_enabled: Whether to apply cross-encoder reranking
                after retrieval. Default False.
            reranker_model: HuggingFace model identifier for the
                cross-encoder. Only used when reranker_enabled is True.
            reranker_top_k: Number of results to keep after reranking.
        """
        self._bm25 = BM25Retriever()
        self._rrf_k = rrf_k
        self._reranker: Optional[Reranker] = None

        if reranker_enabled:
            self._reranker = Reranker(
                model_name=reranker_model,
                top_k=reranker_top_k,
            )
            if self._reranker.is_available:
                logger.info(
                    "reranker_configured",
                    model=reranker_model,
                    top_k=reranker_top_k,
                )
            else:
                logger.warning(
                    "reranker_configured_but_unavailable",
                    model=reranker_model,
                    fallback="no_reranking",
                )

    @property
    def bm25_available(self) -> bool:
        """Whether BM25 sparse retrieval is operational."""
        return self._bm25.is_available

    @property
    def reranker_available(self) -> bool:
        """Whether cross-encoder reranking is configured and available."""
        return self._reranker is not None and self._reranker.is_available

    def build_sparse_index(self, texts: list[str]) -> None:
        """Build the BM25 sparse index from section texts.

        Should be called after documents are loaded, using the same
        texts used for FAISS embedding.

        Args:
            texts: List of section texts (heading + content).
        """
        self._bm25.build(texts)

    def search(
        self,
        query: str,
        dense_results: list[tuple[int, float]],
        sections: list[dict],
        top_k: int = 5,
        sparse_top_k: int = 20,
    ) -> list[dict]:
        """Execute hybrid search combining dense and sparse results.

        When BM25 is available, merges dense and sparse rankings using
        RRF. Otherwise, returns dense results directly.

        Args:
            query: User search query.
            dense_results: Pre-computed dense retrieval results as
                (section_index, similarity_score) pairs.
            sections: Full list of document sections (for building results).
            top_k: Number of final results to return.
            sparse_top_k: Number of BM25 candidates to consider before fusion.

        Returns:
            List of section dicts with keys: source, heading, content, score,
            retrieval_method.
        """
        if not self._bm25.is_available:
            logger.debug("hybrid_search_dense_only", reason="bm25_unavailable")
            results = self._build_results(
                dense_results[:top_k],
                sections,
                method="dense",
            )
            return self._apply_reranking(query, results)

        # Sparse retrieval
        sparse_results = self._bm25.search(query, top_k=sparse_top_k)

        if not sparse_results:
            logger.debug("hybrid_search_dense_only", reason="no_sparse_hits")
            results = self._build_results(
                dense_results[:top_k],
                sections,
                method="dense",
            )
            return self._apply_reranking(query, results)

        # RRF fusion — retrieve more candidates when reranking is active
        # so the cross-encoder has a wider pool to re-score
        rerank_multiplier = 2 if self._reranker is not None else 1
        fused_top_k = top_k * rerank_multiplier

        fused = reciprocal_rank_fusion(
            dense_results,
            sparse_results,
            k=self._rrf_k,
        )

        logger.debug(
            "hybrid_search_fused",
            dense_candidates=len(dense_results),
            sparse_candidates=len(sparse_results),
            fused_total=len(fused),
            top_k=top_k,
            reranking=self._reranker is not None,
        )

        results = self._build_results(
            fused[:fused_top_k], sections, method="hybrid"
        )
        return self._apply_reranking(query, results)

    @staticmethod
    def _build_results(
        ranked: list[tuple[int, float]],
        sections: list[dict],
        method: str,
    ) -> list[dict]:
        """Convert (index, score) pairs into section result dicts.

        Args:
            ranked: List of (section_index, score) pairs.
            sections: Full sections list to look up data.
            method: Retrieval method label (dense, sparse, hybrid).

        Returns:
            List of result dicts compatible with KnowledgeBase.search() API.
        """
        results = []
        for idx, score in ranked:
            if idx < 0 or idx >= len(sections):
                continue
            section = sections[idx]
            results.append(
                {
                    "source": section["source"],
                    "heading": section["heading"],
                    "content": section["content"],
                    "score": float(score),
                    "retrieval_method": method,
                }
            )
        return results
