# Task Plan: Modernize Botsoma Support Agent

**Task Name:** modernize-support-agent
**Task Type:** feature
**Task Path:** .dr_ai/tasks/modernize-support-agent/
**Created:** 2026-04-08
**Status:** planning

---

## Objective

Transform the Botsoma bot from a basic text-only support agent into a modern, interactive, and intelligent support system in Microsoft Teams. This covers 4 areas: UX Conversacional, RAG Moderno, Escalacao Inteligente, and Arquitetura de Producao.

## Research Reference

`.dr_ai/research/agente-atendimento-teams-moderno/summary.md` and all 8 research files.

---

## Current Architecture

```
bot/app.py              → TriageBot (ActivityHandler), aiohttp server
bot/config.py           → Environment variables
bot/services/
  triage_flow.py        → State machine: Session, process_turn(), _sessions dict
  knowledge_base.py     → Keyword-based search (regex tokenize)
  llm_service.py        → Anthropic-compatible LLM calls via httpx
  escalation_service.py → OAuth2 token + proactive message
web/server.py           → FastAPI demo interface
manifest/manifest.json  → Teams app manifest v1.25
Dockerfile              → Python 3.12-slim, port 3978
```

### Key Gaps

| Component | Current | Target |
|-----------|---------|--------|
| Knowledge search | regex keyword match | FAISS embeddings + hybrid search |
| Session storage | in-memory `_sessions: dict` | Redis with TTL |
| User interactions | plain text only | Adaptive Cards + Task Modules |
| Escalation | binary (explain/escalate) | confidence scoring + sentiment + warm handoff |
| Observability | basic logging | structlog + Prometheus metrics |
| Manifest | minimal | Adaptive Cards permissions + Messaging Extensions |

---

## Implementation Plan

### Sprint 1: Foundation (RAG + Sessions + Logging)

#### 1.1 Replace keyword search with FAISS embeddings
- **File:** `bot/services/knowledge_base.py`
- **Changes:**
  - Add `sentence-transformers` with `all-MiniLM-L6-v2`
  - Create `EmbeddingKnowledgeBase` class replacing `KnowledgeBase`
  - Implement chunking by headings (reuse existing `_split_by_headings`)
  - Build FAISS `IndexFlatIP` index at startup
  - Replace `search()` with cosine similarity search
  - Keep `format_context()` API compatible
- **Dependencies:** `sentence-transformers`, `faiss-cpu`, `torch` (CPU)
- **Testing:** Manual test with existing docs, verify search quality

#### 1.2 Redis session persistence
- **New file:** `bot/services/redis_store.py`
- **File:** `bot/services/triage_flow.py`
- **Changes:**
  - Create `RedisSessionStore` class (get/save/delete with TTL 7 days)
  - Replace `_sessions: dict[str, Session]` with Redis-backed store
  - Update `get_or_create_session()` and `reset_session()`
  - Serialize/deserialize Session dataclass to/from JSON
  - Fallback to in-memory if Redis is unavailable
- **Dependencies:** `redis`
- **Config:** Add `REDIS_URL` env var to `config.py`

#### 1.3 Structured logging with structlog
- **File:** `bot/app.py` (and all services)
- **Changes:**
  - Replace `logging.basicConfig` with structlog JSON configuration
  - Add structured log events: `triage_decision`, `escalation_sent`, `session_created`
  - Include session_id, decision, confidence, latency in all logs
- **Dependencies:** `structlog`

#### 1.4 Update requirements.txt and Dockerfile
- **File:** `requirements.txt`
- **File:** `Dockerfile`
- **Changes:**
  - Add new dependencies
  - Add torch CPU-only install
  - Add embedding model download step in Dockerfile
  - Add `libgomp1` system dependency for FAISS

### Sprint 2: Interactive UX (Adaptive Cards + Task Modules)

#### 2.1 Adaptive Cards service
- **New file:** `bot/services/cards.py`
- **Changes:**
  - Create card builder functions: `build_welcome_card()`, `build_explanation_card()`, `build_escalation_card()`, `build_feedback_card()`
  - All cards use `Action.Execute` (Universal Action Model)
  - Include `fallbackText` on all cards
  - Card JSON templates for each triage decision type

#### 2.2 Invoke activity handler
- **File:** `bot/app.py`
- **Changes:**
  - Add `on_invoke_activity()` to TriageBot
  - Handle `adaptiveCard/action` verbs: `login_issue`, `feature_question`, `system_error`, `escalate`, `back_to_menu`, `feedback_yes`, `feedback_no`
  - Handle `task/fetch` and `task/submit` for Task Modules
  - Route card actions through `process_turn()` in triage_flow

#### 2.3 Integrate cards with triage flow
- **File:** `bot/services/triage_flow.py`
- **Changes:**
  - Add `suggested_actions: list[dict] | None` to `TriageStep`
  - When decision is `explain`, include feedback buttons ("Ajudou? Sim/Nao")
  - When decision is `ask`, include quick-reply buttons
  - When decision is `escalate`, include confirmation card

#### 2.4 Task Module for problem reporting
- **New file:** `bot/services/cards.py` (add task module cards)
- **Changes:**
  - Create `build_problem_form_card()` with Input.ChoiceSet, Input.Text, urgency selector
  - Handle `task/submit` to process form data through triage

#### 2.5 Update manifest
- **File:** `manifest/manifest.json`
- **Changes:**
  - Add `webApplicationInfo` for Graph API permissions (future)
  - Add `composeExtensions` for Messaging Extensions (optional, Sprint 4)

### Sprint 3: Intelligent Escalation (Confidence + Sentiment + Warm Handoff)

#### 3.1 Confidence scoring
- **New file:** `bot/services/confidence.py`
- **File:** `bot/services/triage_flow.py`
- **Changes:**
  - Create `ConfidenceMetrics` dataclass (retrieval_score, retrieval_coverage, llm_entropy, kb_relevance)
  - Compute confidence from RAG results + LLM response
  - Apply thresholds: >=0.8 explain, 0.6-0.79 clarify, <0.4 escalate
  - Integrate into `process_turn()` decision logic

#### 3.2 Sentiment / frustration detection
- **New file:** `bot/services/sentiment.py`
- **Changes:**
  - Create `FRUSTRATION_PATTERNS` dict with keywords and scores
  - Implement `detect_frustration()` returning 0-1 score
  - Trigger escalation rules based on frustration thresholds
  - Track frustration trend across session turns

#### 3.3 Warm handoff with EscalationContext
- **New file:** `bot/services/escalation_context.py`
- **File:** `bot/services/triage_flow.py`
- **File:** `bot/app.py`
- **Changes:**
  - Create `EscalationContext` dataclass with full conversation metadata
  - Generate conversation summary via LLM
  - Build escalation Adaptive Card with all context
  - Replace plain-text escalation message with rich card

#### 3.4 Rate limiting
- **New file:** `bot/services/rate_limiter.py`
- **File:** `bot/app.py`
- **Changes:**
  - Create `RateLimiter` class (10 req/min per conversation)
  - Apply before triage processing
  - Return rate-limit message when exceeded

### Sprint 4: Quality + Production (Hybrid Search + Metrics + Deploy)

#### 4.1 BM25 hybrid search + RRF
- **New file:** `bot/services/hybrid_search.py`
- **File:** `bot/services/knowledge_base.py`
- **Changes:**
  - Implement `BM25Retriever` for sparse retrieval
  - Implement `reciprocal_rank_fusion()` for merging dense + sparse
  - Create `HybridRetriever` combining both
  - Wire into knowledge_base search pipeline

#### 4.2 Cross-encoder reranking
- **File:** `bot/services/hybrid_search.py` (extend)
- **Changes:**
  - Add `Reranker` class with `cross-encoder/ms-marco-MiniLM-L-6-v2`
  - Apply reranking after hybrid retrieval
  - Configurable top_k for reranking pass

#### 4.3 Prometheus metrics + health check
- **New file:** `bot/services/metrics.py`
- **File:** `bot/app.py`
- **Changes:**
  - Add Prometheus counters: `bot_triage_decisions_total`, `bot_llm_calls_total`
  - Add histograms: `bot_triage_latency_seconds`, `bot_rag_retrieval_score`
  - Add gauge: `bot_active_sessions`
  - Add `/metrics` and `/health` aiohttp endpoints
  - Instrument `process_turn()` with latency tracking

#### 4.4 Dockerfile and deployment updates
- **File:** `Dockerfile`
- **Changes:**
  - Multi-stage build with torch CPU
  - Embedding model download at build time
  - HEALTHCHECK directive
  - Proper signal handling for graceful shutdown

---

## File Change Summary

| File | Sprint | Action | Description |
|------|--------|--------|-------------|
| `requirements.txt` | 1 | MODIFY | Add sentence-transformers, faiss-cpu, redis, structlog |
| `Dockerfile` | 1,4 | MODIFY | torch CPU, libgomp1, model download, healthcheck |
| `bot/config.py` | 1 | MODIFY | Add REDIS_URL, EMBEDDING_MODEL settings |
| `bot/services/knowledge_base.py` | 1,4 | REWRITE | FAISS embeddings + hybrid search pipeline |
| `bot/services/redis_store.py` | 1 | CREATE | RedisSessionStore + RedisBotStorage |
| `bot/services/triage_flow.py` | 2,3 | MODIFY | Redis sessions, card actions, confidence integration |
| `bot/app.py` | 2,3,4 | MODIFY | invoke handler, cards, metrics, health, structlog |
| `bot/services/cards.py` | 2 | CREATE | Adaptive Card builders + Task Module forms |
| `bot/services/confidence.py` | 3 | CREATE | ConfidenceMetrics + threshold logic |
| `bot/services/sentiment.py` | 3 | CREATE | Frustration detection via keyword patterns |
| `bot/services/escalation_context.py` | 3 | CREATE | EscalationContext + warm handoff card |
| `bot/services/rate_limiter.py` | 3 | CREATE | RateLimiter per conversation |
| `bot/services/hybrid_search.py` | 4 | CREATE | BM25 + RRF + cross-encoder reranking |
| `bot/services/metrics.py` | 4 | CREATE | Prometheus counters, histograms, gauges |
| `manifest/manifest.json` | 2 | MODIFY | webApplicationInfo, composeExtensions |

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| sentence-transformers too heavy for Docker | Slow build, large image | Use CPU-only torch, slim model (80MB) |
| Redis unavailable at runtime | Sessions lost on restart | Fallback to in-memory with warning log |
| FAISS index rebuild slow | Slow startup | Build index once, cache to disk |
| Adaptive Cards not rendering | Poor UX | Include fallbackText, test in Teams client |
| LLM response parsing failures | Wrong decisions | Existing fallback logic in triage_flow.py |

---

## Execution Order

Sprints must be executed sequentially (1 → 2 → 3 → 4) because:
- Sprint 2 depends on Sprint 1's new knowledge_base API
- Sprint 3 depends on Sprint 1's confidence scores from RAG
- Sprint 4 depends on Sprint 1's base search to add hybrid layer

Within each sprint, tasks can be parallelized when independent.
