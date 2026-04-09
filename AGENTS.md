# Botsoma — Agent Context

## What This Is

Python support-bot for Microsoft Teams that classifies user messages via LLM triage:
- **Error/problem** → escalates to a human on Teams (proactive message via Bot Framework)
- **Question/info** → answers from a local knowledge base (`.md`/`.txt` files + RAG)

There are **two runtimes**:
1. `bot/app.py` — Teams bot via Bot Framework SDK (aiohttp, port 3978)
2. `web/server.py` — Standalone FastAPI web chat (port 8000) for testing/demo

Both share the same service layer under `bot/services/`.

## Quick Commands

```bash
# Setup
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Run Teams bot
python -m bot.app          # → http://localhost:3978/api/messages

# Run web demo (separate entrypoint!)
python -m web.server        # → http://localhost:8000

# Test locally with ngrok (Teams bot)
ngrok http 3978

# Docker
docker build -t botsoma .
docker run -p 3978:3978 --env-file .env botsoma
```

## Architecture

```
bot/
  app.py                  # Teams bot entry (aiohttp + BotFrameworkAdapter)
  config.py               # All env vars loaded here — single source of truth
  services/
    llm_service.py        # LLM calls (classify + explain), Anthropic-compatible API
    knowledge_base.py     # In-memory .md/.txt loader with keyword search
    escalation_service.py  # Proactive Teams messages (OAuth token caching)
    triage_flow.py         # State-machine triage: ask → explain | escalate (max 3 questions)
web/
  server.py               # FastAPI demo server (POST /api/chat, GET /api/health)
  index.html              # Chat UI (vanilla JS, no build step)
docs/knowledge/           # Knowledge-base docs (loaded at startup, excluded files in KnowledgeBase.EXCLUDED_DOCS)
manifest/
  manifest.json           # Teams App Manifest (replace botId placeholder)
```

## Key Patterns

- **Config**: All env vars in `bot/config.py`. dotenv loads from project-root `.env`.
- **LLM provider**: Defaults to `z.ai` (Anthropic-compatible endpoint). Change `ZAI_BASE_URL` / `ZAI_MODEL` / `ZAI_API_KEY` for other providers.
- **Knowledge base**: Singleton loaded once at startup (`get_knowledge_base()`). Add `.md`/`.txt` files to `docs/knowledge/`. Files in `KnowledgeBase.EXCLUDED_DOCS` are skipped.
- **Triage flow** (`triage_flow.py`): Deterministic state machine, max 3 clarifying questions, then forced decide. Detects greetings, gibberish, language (pt/en), and duplicate questions. Fallback to keyword matching if LLM JSON parse fails.
- **Sessions**: In-memory dict (`_sessions` in triage_flow.py). Not persisted across restarts.
- **Escalation**: Uses Azure Bot Framework proactive messaging with OAuth2 token caching. Requires `MICROSOFT_APP_ID`, `MICROSOFT_APP_PASSWORD`, `MICROSOFT_APP_TENANT_ID`.
- **Web demo** (`web/server.py`): Uses simulated support agents (round-robin `SUPPORT_AGENTS` list), not real Teams users.

## Environment Variables

Copy `.env.example` → `.env`. Required for Teams bot:

| Variable | Purpose |
|---|---|
| `MICROSOFT_APP_ID` | Azure AD App Registration ID |
| `MICROSOFT_APP_PASSWORD` | Azure AD client secret |
| `MICROSOFT_APP_TENANT_ID` | Azure AD tenant |
| `ZAI_API_KEY` | LLM API key |
| `ZAI_MODEL` | LLM model name (default: `GLM-4.5-Air`) |
| `ZAI_BASE_URL` | LLM endpoint (default: `https://api.z.ai/api/anthropic/v1/messages`) |
| `SUPPORT_USER_IDS` | Comma-separated Teams user IDs for escalation |

Web demo only needs `ZAI_*` for LLM calls.

## Gotchas

- **No `.gitignore` at root** — `venv/`, `.env`, `__pycache__/`, `.ruff_cache/` are not excluded. Add one if initializing git.
- **Dockerfile copies `bot/` and `docs/`** but not `web/` — the container runs the Teams bot only.
- **`requirements.txt` pins **6** packages** — no dev dependencies, no test runner configured.
- **Python 3.12** in Dockerfile but 3.14 in local venv — `KnowledgeBase.EXCLUDED_DOCS` uses set literal syntax requiring 3.9+.
- **No test suite exists yet.**
- **No linter/formatter configured** (`.ruff_cache/` exists suggesting ad-hoc ruff use).
- **Knowledge base is read at startup** — adding docs requires a restart.
- **Web server assigns fake agents** in round-robin. Real escalation needs `SUPPORT_USER_IDS` and Azure Bot credentials.