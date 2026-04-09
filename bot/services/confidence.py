"""
Confidence scoring for triage decisions.

Computes a weighted confidence score from multiple signals:
  - retrieval_score:   best cosine-similarity from the RAG search
  - retrieval_coverage: fraction of top-k results above a relevance floor
  - kb_relevance:      ratio of query tokens present in retrieved content
  - llm_coherence:     1.0 when the LLM returns valid structured JSON, degraded on parse errors

The composite score drives decision overrides:
  >=0.80  →  high confidence, prefer "explain"
  0.40–0.79  →  medium, allow "ask" for clarification
  <0.40  →  low confidence, prefer "escalate"
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import structlog

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------
THRESHOLD_HIGH = 0.80
THRESHOLD_MEDIUM = 0.40

# Weights for the composite score (must sum to 1.0)
WEIGHT_RETRIEVAL_SCORE = 0.35
WEIGHT_RETRIEVAL_COVERAGE = 0.25
WEIGHT_KB_RELEVANCE = 0.25
WEIGHT_LLM_COHERENCE = 0.15

# Minimum cosine similarity to consider a retrieved section "relevant"
RELEVANCE_FLOOR = 0.25


@dataclass
class ConfidenceMetrics:
    """Individual signals that compose the confidence score."""

    retrieval_score: float = 0.0
    retrieval_coverage: float = 0.0
    kb_relevance: float = 0.0
    llm_coherence: float = 1.0

    @property
    def composite(self) -> float:
        """Weighted composite confidence in [0.0, 1.0]."""
        raw = (
            WEIGHT_RETRIEVAL_SCORE * self.retrieval_score
            + WEIGHT_RETRIEVAL_COVERAGE * self.retrieval_coverage
            + WEIGHT_KB_RELEVANCE * self.kb_relevance
            + WEIGHT_LLM_COHERENCE * self.llm_coherence
        )
        return max(0.0, min(1.0, raw))

    @property
    def level(self) -> str:
        """Human-readable confidence level: high, medium, or low."""
        score = self.composite
        if score >= THRESHOLD_HIGH:
            return "high"
        if score >= THRESHOLD_MEDIUM:
            return "medium"
        return "low"

    def as_dict(self) -> dict:
        """Serialize for structured logging."""
        return {
            "retrieval_score": round(self.retrieval_score, 4),
            "retrieval_coverage": round(self.retrieval_coverage, 4),
            "kb_relevance": round(self.kb_relevance, 4),
            "llm_coherence": round(self.llm_coherence, 4),
            "composite": round(self.composite, 4),
            "level": self.level,
        }


# ---------------------------------------------------------------------------
# Computation helpers
# ---------------------------------------------------------------------------

def _tokenize_simple(text: str) -> set[str]:
    """Lowercase alpha tokens of length >= 2."""
    return set(re.findall(r"[a-záàâãéèêíïóôõöúçñ]{2,}", text.lower()))


def compute_confidence(
    search_results: list[dict],
    query: str,
    llm_parse_ok: bool = True,
) -> ConfidenceMetrics:
    """Build ConfidenceMetrics from RAG search results and query.

    Parameters
    ----------
    search_results:
        List of dicts from KnowledgeBase.search(), each with at least
        ``score`` (float) and ``content`` (str).
    query:
        The user query used for retrieval.
    llm_parse_ok:
        False when the LLM response failed JSON parsing (degrades coherence).

    Returns
    -------
    ConfidenceMetrics with all four signals populated.
    """
    metrics = ConfidenceMetrics()

    if not search_results:
        metrics.retrieval_score = 0.0
        metrics.retrieval_coverage = 0.0
        metrics.kb_relevance = 0.0
        metrics.llm_coherence = 1.0 if llm_parse_ok else 0.5
        return metrics

    # 1) retrieval_score — best similarity from the top results
    scores = [r.get("score", 0.0) for r in search_results]
    metrics.retrieval_score = max(scores) if scores else 0.0

    # 2) retrieval_coverage — fraction of results above the relevance floor
    above_floor = sum(1 for s in scores if s >= RELEVANCE_FLOOR)
    metrics.retrieval_coverage = above_floor / len(scores) if scores else 0.0

    # 3) kb_relevance — token overlap between query and retrieved content
    query_tokens = _tokenize_simple(query)
    if query_tokens:
        all_content = " ".join(r.get("content", "") for r in search_results)
        content_tokens = _tokenize_simple(all_content)
        overlap = len(query_tokens & content_tokens)
        metrics.kb_relevance = overlap / len(query_tokens)
        # Cap at 1.0 (overlap can exceed query length if content is rich)
        metrics.kb_relevance = min(1.0, metrics.kb_relevance)
    else:
        metrics.kb_relevance = 0.0

    # 4) llm_coherence — binary for now, extendable to entropy-based later
    metrics.llm_coherence = 1.0 if llm_parse_ok else 0.5

    return metrics


def should_override_decision(
    current_decision: str,
    metrics: ConfidenceMetrics,
    questions_asked: int,
    max_questions: int,
) -> str | None:
    """Return an overridden decision or None to keep the current one.

    Override rules:
      - If confidence is HIGH and decision is "escalate" → override to "explain"
        (the KB clearly covers the topic, LLM was wrong to escalate).
      - If confidence is LOW and decision is "explain" → override to "escalate"
        (the KB does not cover the topic well enough to answer).
      - If confidence is LOW and decision is "ask" and questions remain →
        keep "ask" (give the user a chance to clarify).
      - If confidence is LOW and no questions remain → override to "escalate".

    Returns
    -------
    The overridden decision string, or None if no override is needed.
    """
    level = metrics.level

    if level == "high" and current_decision == "escalate":
        logger.info(
            "confidence_override",
            from_decision="escalate",
            to_decision="explain",
            confidence=metrics.composite,
            reason="high confidence — KB covers the topic",
        )
        return "explain"

    if level == "low" and current_decision == "explain":
        logger.info(
            "confidence_override",
            from_decision="explain",
            to_decision="escalate",
            confidence=metrics.composite,
            reason="low confidence — KB does not cover the topic",
        )
        return "escalate"

    if level == "low" and current_decision == "ask":
        if questions_asked >= max_questions:
            logger.info(
                "confidence_override",
                from_decision="ask",
                to_decision="escalate",
                confidence=metrics.composite,
                reason="low confidence and no questions remaining",
            )
            return "escalate"
        # Let the clarifying question proceed
        return None

    return None
