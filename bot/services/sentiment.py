"""
Sentiment and frustration detection for support conversations.

Provides lightweight keyword/pattern-based frustration scoring (0.0--1.0)
with session-level trend tracking and configurable escalation thresholds.

The detector does NOT rely on external ML models -- it uses curated
Portuguese and English frustration patterns with weighted scores so the
bot can react in real time without additional latency.

Escalation rules
-----------------
* ``should_escalate_frustration`` returns ``True`` when:
  - A single message scores above ``IMMEDIATE_ESCALATION_THRESHOLD`` (0.8), OR
  - The rolling average of the last ``TREND_WINDOW`` messages exceeds
    ``TREND_ESCALATION_THRESHOLD`` (0.6).
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

import structlog

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

IMMEDIATE_ESCALATION_THRESHOLD: float = 0.8
TREND_ESCALATION_THRESHOLD: float = 0.6
TREND_WINDOW: int = 3

# ---------------------------------------------------------------------------
# Frustration patterns
# ---------------------------------------------------------------------------
# Each entry maps a regex pattern to a weight (0.0--1.0).
# Patterns are tested against NFKD-normalised, lower-cased text with
# combining marks stripped so accented and non-accented variants both match.

FRUSTRATION_PATTERNS: dict[str, float] = {
    # -- Portuguese: strong frustration / anger --
    r"\b(porcaria|lixo|droga|merda|porra|inferno|caramba)\b": 0.9,
    r"\b(ridiculo|absurdo|vergonha|palha[cç]ada|piada)\b": 0.85,
    r"\bnao\s+(funciona|resolve|adianta|presta)\b": 0.7,
    r"\b(inaceitavel|inadmissivel|revoltante)\b": 0.85,
    r"\bjá\s+(tentei|fiz|liguei|mandei)\s+(tudo|varias|diversas|muitas)\b": 0.6,
    r"\bja\s+(tentei|fiz|liguei|mandei)\s+(tudo|varias|diversas|muitas)\b": 0.6,
    r"\bninguem\s+(resolve|ajuda|responde)\b": 0.75,
    r"\b(cansado|cansada|farto|farta)\s+(disso|diss[oe]|de\s+esperar)\b": 0.7,
    r"\b(pessimo|horrivel|terrivel)\b": 0.8,
    r"\bvou\s+(cancelar|processar|reclamar|denunciar)\b": 0.85,
    r"\b(cancelar|encerrar)\s+(contrato|assinatura|conta|plano)\b": 0.75,
    r"\b(perdi|perdendo)\s+(tempo|paciencia|dinheiro)\b": 0.7,
    r"\bfaz\s+(dias|semanas|meses)\b": 0.55,
    r"\b(urgente|emergencia|critico|grave)\b": 0.6,
    r"\b(frustra[dç]|irritad[oa]|nervos[oa]|estressad[oa])\b": 0.65,
    r"\bque\s+(raiva|odio|saco)\b": 0.8,
    r"\bsaco\b": 0.6,
    r"\bvergonha\b": 0.7,
    r"\bexplor(acao|ando)\b": 0.65,
    r"\bdesrespeit(o|ando|aram)\b": 0.75,
    r"\bfalta\s+de\s+(respeito|competencia|profissionalismo)\b": 0.8,
    r"\bnunca\s+(mais|vi|funciona|funcionou)\b": 0.55,

    # -- Portuguese: moderate frustration --
    r"\binsatisfeit[oa]\b": 0.5,
    r"\bdecepciona[dor]\b": 0.5,
    r"\bdesapontad[oa]\b": 0.45,
    r"\bdificuldade\b": 0.25,
    r"\bproblema(s)?\b": 0.2,
    r"\berro(s)?\b": 0.2,
    r"\bconfus[oa]\b": 0.3,
    r"\bnao\s+sei\b": 0.15,
    r"\bnao\s+consigo\b": 0.3,
    r"\bnao\s+entend[oi]\b": 0.25,
    r"\btravou\b": 0.35,
    r"\bbugou\b": 0.4,
    r"\bsumiu\b": 0.35,

    # -- English: strong frustration --
    r"\b(terrible|horrible|awful|worst)\b": 0.8,
    r"\b(useless|worthless|garbage|trash|crap)\b": 0.85,
    r"\b(ridiculous|absurd|unacceptable|outrageous)\b": 0.8,
    r"\b(furious|livid|enraged|pissed)\b": 0.9,
    r"\bnot\s+working\b": 0.6,
    r"\bdoesn.?t\s+work\b": 0.6,
    r"\bwaste\s+of\s+(time|money)\b": 0.75,
    r"\bfed\s+up\b": 0.7,
    r"\bsick\s+(of|and\s+tired)\b": 0.7,
    r"\bcan.?t\s+believe\b": 0.55,
    r"\bno\s+one\s+(helps|cares|responds)\b": 0.75,
    r"\bgonna\s+(cancel|sue|report)\b": 0.8,
    r"\balready\s+tried\s+everything\b": 0.65,
    r"\bfor\s+(days|weeks|months)\b": 0.5,

    # -- English: moderate frustration --
    r"\b(frustrated|annoyed|disappointed|upset)\b": 0.55,
    r"\b(confused|stuck|lost)\b": 0.3,
    r"\bstill\s+(broken|not|waiting)\b": 0.5,
    r"\bagain\b": 0.15,
    r"\bproblem(s)?\b": 0.2,
    r"\berror(s)?\b": 0.2,

    # -- Punctuation emphasis (any language) --
    r"[!]{3,}": 0.4,
    r"[?!]{3,}": 0.5,
    r"\bCAPS\b": 0.0,  # placeholder; caps detection handled separately
}

# Pre-compile patterns for performance.
_COMPILED_PATTERNS: list[tuple[re.Pattern[str], float]] = [
    (re.compile(pattern, re.IGNORECASE), weight)
    for pattern, weight in FRUSTRATION_PATTERNS.items()
    if weight > 0
]


# ---------------------------------------------------------------------------
# Text normalisation
# ---------------------------------------------------------------------------

def _normalize_text(text: str) -> str:
    """Lower-case, strip combining marks (accents), collapse whitespace."""
    nfkd = unicodedata.normalize("NFKD", text.lower().strip())
    stripped = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", stripped).strip()


def _caps_ratio(text: str) -> float:
    """Return fraction of alphabetic characters that are upper-case."""
    alpha = [c for c in text if c.isalpha()]
    if len(alpha) < 4:
        return 0.0
    upper = sum(1 for c in alpha if c.isupper())
    return upper / len(alpha)


# ---------------------------------------------------------------------------
# Core scoring
# ---------------------------------------------------------------------------

def score_frustration(text: str) -> float:
    """Return a frustration score between 0.0 and 1.0 for a single message.

    The score is the maximum matched pattern weight, optionally boosted by
    caps-lock usage or excessive punctuation.

    Parameters
    ----------
    text:
        Raw user message (any language).

    Returns
    -------
    float
        Frustration intensity from 0.0 (neutral) to 1.0 (extreme).
    """
    if not text or not text.strip():
        return 0.0

    normalized = _normalize_text(text)
    max_score: float = 0.0

    # Pattern matching against normalised text.
    for pattern, weight in _COMPILED_PATTERNS:
        if pattern.search(normalized):
            max_score = max(max_score, weight)

    # Caps-lock boost: if >60% of alpha chars are caps, add 0.15.
    if _caps_ratio(text) > 0.6:
        max_score = min(1.0, max_score + 0.15)

    # Excessive exclamation/question marks in original text.
    exclamation_count = text.count("!")
    question_count = text.count("?")
    if exclamation_count >= 3 or question_count >= 3:
        max_score = max(max_score, 0.35)

    return round(min(1.0, max_score), 2)


# ---------------------------------------------------------------------------
# Session-level trend tracking
# ---------------------------------------------------------------------------

@dataclass
class FrustrationTracker:
    """Tracks per-message frustration scores across a conversation session.

    Attributes
    ----------
    scores:
        Chronological list of per-turn frustration scores (one per user message).
    peak_score:
        Highest single-message score observed in the session.
    """

    scores: list[float] = field(default_factory=list)
    peak_score: float = 0.0

    def record(self, score: float) -> None:
        """Append a new turn score and update the peak."""
        self.scores.append(score)
        if score > self.peak_score:
            self.peak_score = score

    @property
    def current_score(self) -> float:
        """Most recent turn score, or 0.0 if no turns recorded."""
        return self.scores[-1] if self.scores else 0.0

    @property
    def trend_average(self) -> float:
        """Rolling average over the last ``TREND_WINDOW`` turns."""
        if not self.scores:
            return 0.0
        window = self.scores[-TREND_WINDOW:]
        return round(sum(window) / len(window), 2)

    @property
    def is_escalating(self) -> bool:
        """Return ``True`` if frustration is trending upward over recent turns."""
        if len(self.scores) < 2:
            return False
        recent = self.scores[-TREND_WINDOW:]
        if len(recent) < 2:
            return False
        # Check if each successive score is >= the previous one
        # and the last score is meaningfully above zero.
        return recent[-1] > recent[0] and recent[-1] >= 0.3

    @property
    def turn_count(self) -> int:
        return len(self.scores)

    def to_dict(self) -> dict:
        """Serialize for JSON/Redis storage."""
        return {
            "scores": self.scores,
            "peak_score": self.peak_score,
        }

    @classmethod
    def from_dict(cls, data: dict) -> FrustrationTracker:
        """Reconstruct from stored dict."""
        tracker = cls(
            scores=data.get("scores", []),
            peak_score=data.get("peak_score", 0.0),
        )
        return tracker


# ---------------------------------------------------------------------------
# Escalation decision
# ---------------------------------------------------------------------------

def should_escalate_frustration(tracker: FrustrationTracker) -> bool:
    """Determine whether frustration level warrants automatic escalation.

    Returns ``True`` when:
    * The latest message score exceeds ``IMMEDIATE_ESCALATION_THRESHOLD``, OR
    * The rolling average of the last ``TREND_WINDOW`` messages exceeds
      ``TREND_ESCALATION_THRESHOLD``.

    Parameters
    ----------
    tracker:
        The session's ``FrustrationTracker`` instance.
    """
    if not tracker.scores:
        return False

    current = tracker.current_score
    trend = tracker.trend_average

    if current >= IMMEDIATE_ESCALATION_THRESHOLD:
        logger.info(
            "frustration_immediate_escalation",
            current_score=current,
            threshold=IMMEDIATE_ESCALATION_THRESHOLD,
        )
        return True

    if trend >= TREND_ESCALATION_THRESHOLD and tracker.turn_count >= 2:
        logger.info(
            "frustration_trend_escalation",
            trend_average=trend,
            threshold=TREND_ESCALATION_THRESHOLD,
            window_scores=tracker.scores[-TREND_WINDOW:],
        )
        return True

    return False


# ---------------------------------------------------------------------------
# Convenience: single-call detect + record
# ---------------------------------------------------------------------------

def detect_frustration(
    text: str,
    tracker: FrustrationTracker | None = None,
) -> tuple[float, bool]:
    """Score a message, optionally record it, and return escalation decision.

    Parameters
    ----------
    text:
        Raw user message.
    tracker:
        If provided, the score is recorded and trend-based escalation is
        evaluated.  If ``None``, only the immediate score threshold is checked.

    Returns
    -------
    tuple[float, bool]
        ``(frustration_score, should_escalate)``
    """
    score = score_frustration(text)

    if tracker is not None:
        tracker.record(score)
        escalate = should_escalate_frustration(tracker)
    else:
        escalate = score >= IMMEDIATE_ESCALATION_THRESHOLD

    logger.debug(
        "frustration_detected",
        score=score,
        escalate=escalate,
        trend_avg=tracker.trend_average if tracker else None,
        peak=tracker.peak_score if tracker else None,
    )

    return score, escalate
