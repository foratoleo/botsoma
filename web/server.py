import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel

from bot.services.knowledge_base import get_knowledge_base
from bot.services.triage_flow import (
    MAX_QUESTIONS,
    get_or_create_session,
    process_turn,
    reset_session,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

HTML_PATH = Path(__file__).parent / "index.html"

app = FastAPI(title="Botsoma - Triagem Deterministica")

# Simulated "humanos no Teams" pool — in a real deployment this would come from
# SUPPORT_USER_IDS / Teams Graph API. For the simulator we round-robin between agents.
SUPPORT_AGENTS = [
    {"name": "Joana Martins", "role": "Engenheira de Suporte — API e Integracoes", "teams_handle": "@joana.martins"},
    {"name": "Carlos Silva", "role": "Analista de Suporte — Documentos e Navegacao", "teams_handle": "@carlos.silva"},
    {"name": "Ana Costa", "role": "Tech Lead Suporte — Autenticacao e Configuracao", "teams_handle": "@ana.costa"},
]

_agent_counter = 0


def _next_agent() -> dict:
    global _agent_counter
    agent = SUPPORT_AGENTS[_agent_counter % len(SUPPORT_AGENTS)]
    _agent_counter += 1
    return agent


class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str
    reset: bool = False


class ChatResponse(BaseModel):
    session_id: str
    decision: str  # "ask" | "explain" | "escalate"
    reply: str
    reason: str = ""
    sources: list[str] = []
    questions_asked: int = 0
    max_questions: int = MAX_QUESTIONS
    closed: bool = False
    # Escalation-only fields
    urgency: str | None = None
    assignee: dict | None = None
    handoff_notice: str | None = None


@app.get("/", response_class=HTMLResponse)
async def index():
    return HTML_PATH.read_text(encoding="utf-8")


@app.get("/favicon.ico")
async def favicon():
    return Response(status_code=204)


@app.post("/api/chat")
async def chat(req: ChatRequest) -> ChatResponse:
    if req.reset and req.session_id:
        reset_session(req.session_id)

    session = get_or_create_session(req.session_id)

    if not req.message.strip():
        return ChatResponse(
            session_id=session.id,
            decision="ask",
            reply="Descreva em uma frase o que aconteceu ou o que voce esta tentando fazer.",
            questions_asked=session.questions_asked,
        )

    if session.closed:
        # Previous session ended with escalation — start fresh.
        reset_session(session.id)
        session = get_or_create_session(None)

    logger.info("[%s] turn %d/%d: %s", session.id[:8], session.questions_asked + 1, MAX_QUESTIONS, req.message[:120])

    try:
        step = await process_turn(session, req.message)
    except Exception as exc:
        logger.error("Triage error: %s", exc, exc_info=True)
        agent = _next_agent()
        return ChatResponse(
            session_id=session.id,
            decision="escalate",
            reply="Tivemos um problema tecnico ao processar sua mensagem.",
            reason=str(exc),
            urgency="urgente",
            assignee=agent,
            handoff_notice=_handoff_text(agent, "urgente"),
            closed=True,
        )

    logger.info(
        "[%s] decision=%s reason=%s",
        session.id[:8],
        step.decision,
        (step.reason or "")[:80],
    )

    response = ChatResponse(
        session_id=session.id,
        decision=step.decision,
        reply=step.message,
        reason=step.reason,
        sources=step.sources,
        questions_asked=session.questions_asked,
        closed=session.closed,
    )

    if step.decision == "escalate":
        agent = _next_agent()
        response.urgency = step.urgency or "urgente"
        response.assignee = agent
        response.handoff_notice = _handoff_text(agent, response.urgency)

    return response


def _handoff_text(agent: dict, urgency: str) -> str:
    return (
        f"Estou direcionando seu caso agora para {agent['name']} "
        f"({agent['role']}) no Microsoft Teams ({agent['teams_handle']}), "
        f"marcado como **{urgency.upper()}**. "
        f"Voce recebera uma mensagem direta em instantes — pode continuar o atendimento por la."
    )


@app.get("/api/health")
async def health():
    kb = get_knowledge_base()
    return {
        "status": "ok",
        "knowledge_base_sections": kb.section_count,
        "knowledge_base_loaded": kb.is_loaded,
        "max_questions": MAX_QUESTIONS,
    }


@app.on_event("startup")
async def startup():
    kb = get_knowledge_base()
    logger.info(
        "Web server started — knowledge base: %d sections loaded", kb.section_count
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("web.server:app", host="0.0.0.0", port=8000, reload=True)
