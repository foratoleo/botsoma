"""
Prometheus metrics for Botsoma bot observability.

Exposes counters, histograms, and gauges for triage decisions, LLM calls,
RAG retrieval scores, and active sessions. Provides aiohttp handler
functions for ``/metrics`` and ``/health`` endpoints.

Usage::

    from bot.services.metrics import (
        TRIAGE_DECISIONS,
        LLM_CALLS,
        TRIAGE_LATENCY,
        RAG_RETRIEVAL_SCORE,
        ACTIVE_SESSIONS,
        metrics_handler,
        health_handler,
    )
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import AsyncIterator

from aiohttp import web
from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------
# Use the default global registry so all metrics are collected automatically.
# If isolation is needed (e.g. testing), replace with a custom registry.

REGISTRY = CollectorRegistry()

# ---------------------------------------------------------------------------
# Counters
# ---------------------------------------------------------------------------

TRIAGE_DECISIONS = Counter(
    "bot_triage_decisions_total",
    "Total number of triage decisions made by the bot",
    labelnames=["decision", "urgency"],
    registry=REGISTRY,
)

LLM_CALLS = Counter(
    "bot_llm_calls_total",
    "Total number of LLM API calls",
    labelnames=["status"],
    registry=REGISTRY,
)

ESCALATION_EVENTS = Counter(
    "bot_escalation_events_total",
    "Total number of escalation events sent to support",
    labelnames=["status"],
    registry=REGISTRY,
)

# ---------------------------------------------------------------------------
# Histograms
# ---------------------------------------------------------------------------

TRIAGE_LATENCY = Histogram(
    "bot_triage_latency_seconds",
    "Latency of the triage process_turn call in seconds",
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
    registry=REGISTRY,
)

RAG_RETRIEVAL_SCORE = Histogram(
    "bot_rag_retrieval_score",
    "Distribution of RAG retrieval similarity scores",
    buckets=(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
    registry=REGISTRY,
)

LLM_LATENCY = Histogram(
    "bot_llm_latency_seconds",
    "Latency of individual LLM API calls in seconds",
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
    registry=REGISTRY,
)

# ---------------------------------------------------------------------------
# Gauges
# ---------------------------------------------------------------------------

ACTIVE_SESSIONS = Gauge(
    "bot_active_sessions",
    "Number of currently active bot sessions",
    registry=REGISTRY,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@asynccontextmanager
async def track_triage_latency() -> AsyncIterator[None]:
    """Context manager that records triage latency to the histogram.

    Usage::

        async with track_triage_latency():
            step = await process_turn(session, user_text)
    """
    start = time.monotonic()
    try:
        yield
    finally:
        elapsed = time.monotonic() - start
        TRIAGE_LATENCY.observe(elapsed)


def record_triage_decision(decision: str, urgency: str | None = None) -> None:
    """Increment the triage decision counter with labels."""
    TRIAGE_DECISIONS.labels(
        decision=decision,
        urgency=urgency or "normal",
    ).inc()


def record_llm_call(status: str = "success") -> None:
    """Increment the LLM calls counter."""
    LLM_CALLS.labels(status=status).inc()


def record_llm_latency(seconds: float) -> None:
    """Record LLM call latency."""
    LLM_LATENCY.observe(seconds)


def record_escalation(status: str = "success") -> None:
    """Increment escalation events counter."""
    ESCALATION_EVENTS.labels(status=status).inc()


def record_rag_score(score: float) -> None:
    """Record a RAG retrieval similarity score."""
    RAG_RETRIEVAL_SCORE.observe(score)


def session_opened() -> None:
    """Increment active sessions gauge."""
    ACTIVE_SESSIONS.inc()


def session_closed() -> None:
    """Decrement active sessions gauge."""
    ACTIVE_SESSIONS.dec()


# ---------------------------------------------------------------------------
# aiohttp handlers
# ---------------------------------------------------------------------------


async def metrics_handler(request: web.Request) -> web.Response:
    """Expose Prometheus metrics at ``/metrics``."""
    body = generate_latest(REGISTRY)
    return web.Response(
        body=body,
        content_type=CONTENT_TYPE_LATEST,
    )


async def health_handler(request: web.Request) -> web.Response:
    """Health check endpoint at ``/health``.

    Returns 200 with a JSON body containing component statuses.
    Useful for container orchestrators (Docker HEALTHCHECK, Kubernetes
    liveness/readiness probes).
    """
    from bot.services.redis_store import get_session_store

    store = get_session_store()
    redis_ok = store.is_redis_connected

    # Check if knowledge base is loaded
    try:
        from bot.services.knowledge_base import get_knowledge_base

        kb = get_knowledge_base()
        kb_ok = kb.section_count > 0
        kb_sections = kb.section_count
    except Exception:
        kb_ok = False
        kb_sections = 0

    all_healthy = kb_ok  # Redis is optional (fallback to memory)

    status_code = 200 if all_healthy else 503
    payload = {
        "status": "healthy" if all_healthy else "degraded",
        "components": {
            "knowledge_base": {
                "status": "ok" if kb_ok else "error",
                "sections": kb_sections,
            },
            "redis": {
                "status": "connected" if redis_ok else "fallback_memory",
            },
        },
    }

    return web.json_response(payload, status=status_code)
