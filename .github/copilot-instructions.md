# Botsoma - Instructions for GitHub Copilot

## Project Overview

Botsoma is a Python support chatbot for Microsoft Teams. It classifies user messages via LLM triage:
- **Question/usage doubt** -> answers from the knowledge base (RAG with FAISS + BM25 hybrid search)
- **Real system error** -> escalates to a human on Teams (proactive message via Bot Framework)

## Architecture

```
User (Teams)
  -> Azure Bot Service
    -> Container App (Azure)
      -> bot/app.py (aiohttp + BotFrameworkAdapter)
        -> triage_flow.py (state machine: ask -> explain | escalate)
          -> llm_service.py (Anthropic-compatible LLM calls)
          -> knowledge_base.py (FAISS + BM25 hybrid search over docs/knowledge/)
          -> cards.py (Adaptive Cards for Teams UI)
          -> escalation_service.py (proactive Teams messages)
```

## Key Files

| File | Purpose |
|---|---|
| `bot/app.py` | Teams bot entrypoint. ActivityHandler with Adaptive Cards, rate limiting, metrics |
| `bot/config.py` | All env vars. Single source of truth. `dotenv` loads from `.env` |
| `bot/services/triage_flow.py` | **Core logic**. Deterministic state machine. Max 3 questions, max 10 turns. Contains `TRIAGE_SYSTEM_PROMPT` (line ~190) which defines the bot's personality and decision criteria |
| `bot/services/llm_service.py` | LLM calls. `_call_llm()` sends Anthropic-compatible requests. Contains `CLASSIFY_SYSTEM_PROMPT` and `EXPLAIN_SYSTEM_PROMPT_TEMPLATE` |
| `bot/services/knowledge_base.py` | Loads `.md`/`.txt` from `docs/knowledge/`, splits by headings, FAISS embeddings. Excluded docs in `EXCLUDED_DOCS` set |
| `bot/services/hybrid_search.py` | BM25 sparse retrieval + FAISS dense retrieval + Reciprocal Rank Fusion (RRF) merging |
| `bot/services/cards.py` | All Adaptive Card builders: welcome, explanation, escalation, feedback, problem form (Task Module) |
| `bot/services/escalation_service.py` | Proactive messaging via Bot Framework REST API with OAuth2 token caching |
| `bot/services/confidence.py` | RAG confidence scoring for triage override decisions |
| `bot/services/sentiment.py` | Frustration detection. Auto-escalates when frustration is high |
| `bot/services/rate_limiter.py` | Per-user rate limiting |
| `bot/services/metrics.py` | Prometheus metrics (request count, latency, triage decisions) |
| `bot/services/redis_store.py` | Session persistence. Falls back to in-memory dict if Redis is unavailable |
| `docs/knowledge/` | **Knowledge base** - 466 `.md`/`.txt` files about DR AI Workforce platform. This is what the bot uses to answer questions |

## Knowledge Base

The bot answers questions **exclusively** from files in `docs/knowledge/`. When editing or adding documentation here:
- Files are loaded at startup (restart required to pick up changes)
- Content is split into sections by markdown headings (`##`, `###`)
- Embeddings are generated with `all-MiniLM-L6-v2` (sentence-transformers)
- Two files are excluded: `09-arquitetura-tecnica.md` and `exemplo-documentacao.md` (see `KnowledgeBase.EXCLUDED_DOCS`)
- The LLM is instructed to use ONLY documentation context, never invent information

## Tech Stack

- **Runtime**: Python 3.12 (Docker), aiohttp for Teams bot
- **LLM**: Anthropic-compatible API (z.ai endpoint, model `GLM-5-Turbo`). Configurable via `ZAI_BASE_URL`, `ZAI_MODEL`, `ZAI_API_KEY`
- **Embeddings**: sentence-transformers (`all-MiniLM-L6-v2`), FAISS CPU
- **Hybrid Search**: FAISS (dense) + BM25 (sparse) + RRF merging
- **Session Store**: Redis (optional, falls back to in-memory)
- **Deployment**: Azure Container Apps, Azure Container Registry, Azure Bot Service
- **Web Demo**: FastAPI in `web/server.py` (port 8000, separate from Teams bot)

## Coding Conventions

- Language: Python with type hints (`from __future__ import annotations`)
- Logging: `structlog` (never `print()` or bare `logging`)
- All env vars in `bot/config.py` only. Never hardcode secrets
- Async everywhere (`async def`, `await`)
- No `as any`, `@ts-ignore` - this is Python but same principle: no type suppression
- Docstrings on all public functions and classes
- Imports grouped: stdlib, third-party, local

## Important Constraints

- **Never commit `.env`** - contains Azure credentials and API keys
- **Never commit `botsoma-image.tar`** - 179MB, use `.gitignore`
- **Dockerfile** copies `bot/` and `docs/` but NOT `web/` - container runs Teams bot only
- Sessions are in-memory by default (no Redis). Not persisted across restarts
- The triage prompt is in Portuguese (Brazilian). The bot detects English and switches automatically
- Temperature is low (0.1) for deterministic triage decisions

## Common Tasks

```bash
# Run Teams bot
python -m bot.app

# Run web demo
python -m web.server

# Docker build & run
docker build -t botsoma .
docker run -p 3978:3978 --env-file .env botsoma
```

## What to Change for What

| Want to... | Edit... |
|---|---|
| Change bot personality/behavior | `bot/services/triage_flow.py` -> `TRIAGE_SYSTEM_PROMPT` |
| Change how bot explains answers | `bot/services/llm_service.py` -> `EXPLAIN_SYSTEM_PROMPT_TEMPLATE` |
| Change classification criteria | `bot/services/llm_service.py` -> `CLASSIFY_SYSTEM_PROMPT` |
| Add/remove knowledge content | `docs/knowledge/*.md` (restart required) |
| Change max questions before forced decision | `bot/services/triage_flow.py` -> `MAX_QUESTIONS` |
| Change card layout/buttons | `bot/services/cards.py` -> respective `build_*_card()` function |
| Change escalation targets | `.env` -> `SUPPORT_USER_IDS` |
| Change LLM provider/model | `.env` -> `ZAI_BASE_URL`, `ZAI_MODEL`, `ZAI_API_KEY` |
| Add excluded docs from KB | `bot/services/knowledge_base.py` -> `KnowledgeBase.EXCLUDED_DOCS` |
