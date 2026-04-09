"""
Deterministic triage flow.

State machine for a guided RAG conversation that converges to a decision in
at most 3 clarifying questions:

  - explain:  the situation is a user misuse / wrong action — answer from docs
  - escalate: the situation is a real error — hand off to a human on Teams

Guarantees:
  * Pure greetings ("ola", "oi", "bom dia") do NOT consume a question.
  * The bot never repeats the same question twice — if the LLM tries, the
    flow force-advances to a decision.
  * Once the question cap is hit, the LLM is re-prompted in "forced decide"
    mode and cannot return `ask`.
  * Fallbacks always produce a meaningful error summary (uses the full user
    history, never a single token like "iniciar").
"""

from __future__ import annotations

import json
import logging
import re
import unicodedata
import uuid
from dataclasses import dataclass, field
from typing import Literal

from bot.services.knowledge_base import get_knowledge_base
from bot.services.llm_service import _call_llm

logger = logging.getLogger(__name__)

MAX_QUESTIONS = 3
MAX_TURNS = 10

Decision = Literal["ask", "explain", "escalate"]

GREETING_PATTERNS = {
    "ola",
    "ola!",
    "olá",
    "oi",
    "oie",
    "eae",
    "eai",
    "hi",
    "hello",
    "bom dia",
    "boa tarde",
    "boa noite",
    "tudo bem",
    "tudo bem?",
    "opa",
}

WELCOME_MESSAGE = (
    "Ola! Sou o Workforce Help. "
    "Me descreva o que voce precisa ou o que aconteceu, vou tentar te ajudar."
)


@dataclass
class Session:
    id: str
    turns: list[dict] = field(default_factory=list)  # [{role, content}]
    questions_asked: int = 0
    closed: bool = False
    last_bot_question: str = ""
    in_follow_up: bool = False

    def add_user(self, text: str) -> None:
        self.turns.append({"role": "user", "content": text})

    def add_bot(self, text: str) -> None:
        self.turns.append({"role": "assistant", "content": text})

    def user_text_joined(self) -> str:
        return " | ".join(
            t["content"].strip()
            for t in self.turns
            if t["role"] == "user" and t["content"].strip()
        )

    def meaningful_user_text(self) -> str:
        """Join user turns that actually carry information (>2 chars, not a greeting)."""
        parts = []
        for t in self.turns:
            if t["role"] != "user":
                continue
            txt = t["content"].strip()
            if not txt or _is_greeting(txt):
                continue
            parts.append(txt)
        return " | ".join(parts) if parts else self.user_text_joined()

    def history_as_text(self) -> str:
        parts = []
        for t in self.turns:
            who = "USUARIO" if t["role"] == "user" else "BOT"
            parts.append(f"{who}: {t['content']}")
        return "\n".join(parts)


_sessions: dict[str, Session] = {}


def get_or_create_session(session_id: str | None) -> Session:
    if session_id and session_id in _sessions:
        return _sessions[session_id]
    sid = session_id or str(uuid.uuid4())
    s = Session(id=sid)
    _sessions[sid] = s
    return s


def reset_session(session_id: str) -> None:
    _sessions.pop(session_id, None)


def _normalize(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text.lower().strip())
    stripped = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"[^\w\s]", "", stripped).strip()


def _is_greeting(text: str) -> bool:
    norm = _normalize(text)
    if not norm:
        return False
    if norm in {_normalize(g) for g in GREETING_PATTERNS}:
        return True
    # Very short and matches greeting words
    if len(norm.split()) <= 2 and norm.split()[0] in {
        "ola",
        "oi",
        "opa",
        "eai",
        "eae",
        "hi",
        "hello",
    }:
        return True
    return False


def _similar_question(a: str, b: str) -> bool:
    """Detect near-duplicate bot questions."""
    na, nb = _normalize(a), _normalize(b)
    if not na or not nb:
        return False
    if na == nb:
        return True
    # High token overlap on short strings → treat as duplicate
    ta, tb = set(na.split()), set(nb.split())
    if not ta or not tb:
        return False
    overlap = len(ta & tb) / max(len(ta | tb), 1)
    return overlap >= 0.75


TRIAGE_SYSTEM_PROMPT = """Voce e o agente de suporte da plataforma DR AI Workforce.

OBJETIVO PRINCIPAL: Resolver a duvida do usuario usando a DOCUMENTACAO DISPONIVEL abaixo.
Voce deve SEMPRE tentar explicar primeiro. So escalar para humano em casos de erro REAL do sistema.

FLUXO DE DECISAO (siga NESTA ORDEM):

1. VERIFICAR DOCUMENTACAO: A documentacao abaixo contem informacoes relevantes sobre o tema do usuario?
   Se SIM -> EXPLICAR com base na documentacao.

2. DUVIDAS DE USO (NUNCA escalar, sempre EXPLICAR):
   - "nao consigo logar", "nao consigo acessar", "nao consigo entrar"
   - "como faco para...", "onde fica...", "nao encontro..."
   - "nao sei usar", "como funciona...", "onde clico..."
   - Qualquer pergunta sobre COMO usar a plataforma
   Estas sao DUVIDAS DE USO. Resolva pela documentacao. NAO escale.

3. SO ESCALAR para erros REAIS do sistema:
   - Erro 500, 502, 503, 404 persistente
   - Sistema fora do ar / tela branca / carregamento infinito
   - Dados perdidos ou corrompidos
   - Funcionalidade que ANTES funcionava e agora parou (bug confirmado)
   - Mensagens de erro do sistema (nao do usuario)

4. IMPORTANTE: "Nao consigo logar" e uma DUVIDA DE USO, nao um erro do sistema.
   O usuario pode estar errando a senha, nao saber onde acessar, ter conta desativada, etc.
   -> EXPLICAR os passos de login baseado na documentacao.

5. Se ambiguo e AINDA ha perguntas disponiveis, faca UMA pergunta curta para desambiguar.
   NUNCA repita uma pergunta ja feita.

6. Na duvida entre EXPLICAR e ESCALAR -> PREFIRA EXPLICAR.

Voce ja fez {questions_asked} pergunta(s). Restam {questions_remaining}.

{language_instruction}

SCHEMA DE RESPOSTA (APENAS JSON, SEM TEXTO EXTRA, SEM MARKDOWN):
{{
  "decision": "ask" | "explain" | "escalate",
  "question": "pergunta curta e DIFERENTE das anteriores (se decision=ask)",
  "explanation": "resposta clara e util baseada EXCLUSIVAMENTE na documentacao fornecida (se decision=explain)",
  "error_summary": "resumo de 1 linha do problema real para o time de suporte (se decision=escalate)",
  "urgency": "urgente" | "normal" | "baixa",
  "emotion_detected": "frustrado" | "triste" | "ansioso" | null,
  "reason": "justificativa curta em 1 linha"
}}

EMPATIA: Se o usuario demonstra frustracao, inicie a explicacao com validacao emocional breve (1 frase).
Exemplo: "Entendo que isso deve ser frustrante. Vou te ajudar."

PERGUNTAS JA FEITAS (NAO REPITA):
{asked_questions}

HISTORICO DA CONVERSA:
{history}

DOCUMENTACAO RELEVANTE (use EXCLUSIVAMENTE isto para explicar):
{kb_context}

Responda AGORA com o JSON exato."""


FORCED_DECIDE_PROMPT = """Voce atingiu o LIMITE de perguntas. Decida AGORA.

PREFERENCIA: EXPLICAR se a documentacao cobre o tema. So ESCALE para erros REAIS do sistema
(erro 500, sistema fora do ar, dados perdidos, bug confirmado).
"Nao consigo logar" e DUVIDA DE USO, nao erro do sistema -> EXPLICAR.

SCHEMA JSON (sem texto extra):
{{
  "decision": "explain" | "escalate",
  "explanation": "...",
  "error_summary": "...",
  "urgency": "urgente" | "normal" | "baixa",
  "reason": "..."
}}

HISTORICO:
{history}

DOCUMENTACAO:
{kb_context}

Responda AGORA."""


@dataclass
class TriageStep:
    decision: Decision
    message: str
    reason: str
    sources: list[str]
    urgency: str | None = None
    error_summary: str | None = None


def _parse_llm_json(raw: str) -> dict:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    if not cleaned.startswith("{"):
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1:
            cleaned = cleaned[start : end + 1]
    return json.loads(cleaned)


def _collect_asked_questions(session: Session) -> list[str]:
    return [t["content"] for t in session.turns if t["role"] == "assistant"]


def _build_fallback_summary(session: Session, fallback_text: str) -> str:
    meaningful = session.meaningful_user_text()
    if len(meaningful) >= 10:
        return meaningful[:200]
    return fallback_text[:140] or "Caso sem detalhes — revisar conversa"


async def _call_forced_decide(session: Session, kb_context: str) -> dict:
    prompt = FORCED_DECIDE_PROMPT.format(
        history=session.history_as_text(),
        kb_context=kb_context,
    )
    try:
        raw = await _call_llm(prompt, "Responda em JSON.", max_tokens=600)
        parsed = _parse_llm_json(raw)
        if parsed.get("decision") not in ("explain", "escalate"):
            parsed["decision"] = "escalate"
        return parsed
    except Exception as exc:
        logger.warning("Forced-decide parse failed: %s", exc)
        return {
            "decision": "explain",
            "explanation": (
                "Nao consegui determinar com precisao o seu caso. "
                "Pode descrever com mais detalhes? Se for um erro do sistema, "
                "entre em contato com o suporte pelo canal de atendimento."
            ),
            "urgency": "normal",
            "reason": "forced decide fallback — preferindo explicar",
        }


# -- Phase 3: Gibberish detection --
_ERROR_CODE_PATTERN = re.compile(
    r"(#ERR-|#ERR|ERR-\d{2,}|HTTP\s?\d{3}|API\s?(KEY|ERROR|CALL)|\b\d{3}\b)",
    re.IGNORECASE,
)


def _is_gibberish(text: str) -> bool:
    """Return True if text looks like random keystrokes, not a real message."""
    stripped = text.strip()
    if not stripped:
        return False
    if _ERROR_CODE_PATTERN.search(stripped):
        return False
    alpha_count = sum(1 for c in stripped if c.isalpha())
    total = len(stripped)
    if total == 0:
        return False
    if alpha_count / total < 0.4:
        return True
    words = [w for w in stripped.split() if len(w) >= 3 and any(c.isalpha() for c in w)]
    if not words:
        return True
    return False


# -- Phase 7: Language detection --
_ENGLISH_WORDS = frozenset(
    {
        "how",
        "what",
        "where",
        "when",
        "why",
        "who",
        "can",
        "help",
        "need",
        "create",
        "project",
        "workspace",
        "team",
        "invite",
        "members",
        "please",
        "hello",
        "hi",
        "thanks",
        "thank",
        "you",
        "the",
        "and",
        "for",
        "with",
        "this",
        "that",
        "from",
        "not",
        "does",
        "work",
        "use",
        "using",
        "trying",
        "error",
        "bug",
        "issue",
        "problem",
        "configure",
        "setup",
        "set",
        "get",
        "access",
        "upload",
        "document",
        "file",
        "new",
        "make",
        "want",
        "like",
        "know",
        "would",
        "could",
        "should",
        "about",
        "into",
        "account",
        "login",
        "integration",
        "system",
        "platform",
        "feature",
        "function",
        "method",
    }
)


def _detect_language(text: str) -> str:
    """Return 'en' if text appears to be English, else 'pt'."""
    words = re.findall(r"[a-zA-Z]{3,}", text.lower())
    if not words:
        return "pt"
    en_count = sum(1 for w in words if w in _ENGLISH_WORDS)
    if en_count / len(words) >= 0.5:
        return "en"
    return "pt"


async def process_turn(session: Session, user_message: str) -> TriageStep:
    """Advance the triage state machine by one user message."""
    session.add_user(user_message)

    # 0) MAX_TURNS guard — prevent infinite follow-up loops.
    if len(session.turns) > MAX_TURNS:
        msg = (
            "Atingimos o limite de mensagens para esta conversa. "
            "Se ainda precisar de ajuda, clique em 'Nova conversa' para recomecar."
        )
        session.closed = True
        session.add_bot(msg)
        return TriageStep(
            decision="escalate",
            message=msg,
            reason="limite de turnos atingido",
            sources=[],
        )

    # 1) Greeting short-circuit — do not consume a question, do not call LLM.
    is_only_greeting = _is_greeting(user_message) and all(
        _is_greeting(t["content"]) for t in session.turns if t["role"] == "user"
    )
    if is_only_greeting:
        session.add_bot(WELCOME_MESSAGE)
        session.last_bot_question = WELCOME_MESSAGE
        return TriageStep(
            decision="ask",
            message=WELCOME_MESSAGE,
            reason="saudacao inicial — aguardando descricao do caso",
            sources=[],
        )

    # 2) Gibberish filter — ask for clarification instead of escalating.
    if _is_gibberish(user_message):
        msg = (
            "Nao entendi sua mensagem. "
            "Pode descrever com mais detalhes o que voce precisa?"
        )
        session.add_bot(msg)
        return TriageStep(
            decision="ask",
            message=msg,
            reason="input detectado como invalido — pedido de esclarecimento",
            sources=[],
        )

    # 3) Language detection.
    lang = _detect_language(user_message)
    language_instruction = (
        "Responda em INGLES. The user writes in English, reply in English."
        if lang == "en"
        else ""
    )

    kb = get_knowledge_base()
    query = session.meaningful_user_text() or user_message
    kb_context = kb.format_context(query, max_results=5) or "(sem trechos relevantes)"
    search = kb.search(query, max_results=5)
    sources = list(dict.fromkeys(s["source"] for s in search))

    at_cap = session.questions_asked >= MAX_QUESTIONS

    # 2) If already at cap, go straight to forced-decide mode.
    if at_cap:
        parsed = await _call_forced_decide(session, kb_context)
    else:
        asked_qs = _collect_asked_questions(session)
        asked_list = (
            "\n".join(f"- {q}" for q in asked_qs) if asked_qs else "(nenhuma ainda)"
        )
        system_prompt = TRIAGE_SYSTEM_PROMPT.format(
            max_questions=MAX_QUESTIONS,
            questions_asked=session.questions_asked,
            questions_remaining=MAX_QUESTIONS - session.questions_asked,
            asked_questions=asked_list,
            history=session.history_as_text(),
            kb_context=kb_context,
            language_instruction=language_instruction,
        )
        try:
            raw = await _call_llm(system_prompt, "Responda em JSON.", max_tokens=800)
            parsed = _parse_llm_json(raw)
        except Exception as exc:
            logger.warning("Triage LLM parse failed: %s", exc)
            parsed = {
                "decision": "explain",
                "explanation": (
                    "Com base na documentacao disponivel, este parece ser um ajuste de uso. "
                    "Verifique os passos no material de referencia ou tente descrever "
                    "com mais detalhes para que eu possa te ajudar melhor."
                ),
                "urgency": "baixa",
                "reason": "fallback por erro de parsing do LLM — preferindo explicar",
            }

    decision: Decision = parsed.get("decision", "ask")

    # 3) Duplicate-question guard: if LLM wants to ask the same thing again,
    # force a decision instead.
    if decision == "ask":
        new_q = (parsed.get("question") or "").strip()
        if session.last_bot_question and _similar_question(
            new_q, session.last_bot_question
        ):
            logger.info("Duplicate question detected — forcing decision")
            parsed = await _call_forced_decide(session, kb_context)
            decision = parsed.get("decision", "explain")

    # 4) Final safety: never return ask if we would exceed the cap after this turn.
    if decision == "ask" and session.questions_asked + 1 > MAX_QUESTIONS:
        parsed = await _call_forced_decide(session, kb_context)
        decision = parsed.get("decision", "explain")

    if decision == "ask":
        question = (parsed.get("question") or "").strip() or (
            "Voce pode detalhar o que estava tentando fazer quando isso aconteceu?"
        )
        session.questions_asked += 1
        session.add_bot(question)
        session.last_bot_question = question
        return TriageStep(
            decision="ask",
            message=question,
            reason=parsed.get("reason") or "",
            sources=[],
        )

    if decision == "explain":
        explanation = (parsed.get("explanation") or "").strip()
        if not explanation:
            explanation = (
                "Com base na documentacao, este parece ser um ajuste de uso. "
                "Verifique os passos no material de referencia abaixo."
            )
        session.questions_asked = 0
        session.in_follow_up = True
        session.add_bot(explanation)
        return TriageStep(
            decision="explain",
            message=explanation,
            reason=parsed.get("reason") or "",
            sources=sources,
        )

    # escalate
    error_summary = (parsed.get("error_summary") or "").strip()
    if len(error_summary) < 10:
        error_summary = _build_fallback_summary(session, user_message)
    urgency = (parsed.get("urgency") or "urgente").strip().lower() or "urgente"
    session.closed = True
    session.add_bot(f"[ESCALACAO] {error_summary}")
    return TriageStep(
        decision="escalate",
        message=error_summary,
        reason=parsed.get("reason") or "",
        sources=sources,
        urgency=urgency,
        error_summary=error_summary,
    )
