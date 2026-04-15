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
import re
import time
import unicodedata
import uuid
from dataclasses import dataclass, field
from typing import Literal

import structlog

from bot.services.confidence import (
    ConfidenceMetrics,
    compute_confidence,
    should_override_decision,
)
from bot.services.knowledge_base import get_knowledge_base
from bot.services.llm_service import _call_llm
from bot.services.redis_store import (
    dict_to_session,
    get_session_store,
    session_to_dict,
)
from bot.services.sentiment import FrustrationTracker, detect_frustration

logger = structlog.get_logger(__name__)

MAX_QUESTIONS = 3
MAX_TURNS = 30

Decision = Literal["ask", "explain", "escalate", "classify", "confirm_ticket"]

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
    frustration_tracker: FrustrationTracker = field(default_factory=FrustrationTracker)
    pending_classification: str = ""
    classification_confirmed: bool = False
    channel: str = "teams"

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


async def get_or_create_session(session_id: str | None) -> Session:
    """Retrieve an existing session from Redis (or fallback) or create a new one."""
    store = get_session_store()
    sid = session_id or str(uuid.uuid4())

    if session_id:
        data = await store.get(session_id)
        if data is not None:
            session = dict_to_session(data)
            return session  # type: ignore[return-value]

    session = Session(id=sid)
    await store.save(sid, session_to_dict(session))
    logger.info(
        "session_created",
        session_id=sid,
        store_mode="redis" if store.is_redis_connected else "memory",
    )
    return session


async def save_session(session: Session) -> None:
    """Persist the current session state to the store."""
    store = get_session_store()
    await store.save(session.id, session_to_dict(session))


async def reset_session(session_id: str) -> None:
    """Remove a session from the store."""
    store = get_session_store()
    await store.delete(session_id)


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


TRIAGE_SYSTEM_PROMPT = """Voce e o agente de suporte da plataforma WORKFORCE (gestao de projetos com IA).

SOBRE A PLATAFORMA:
Workforce e uma plataforma de gestao de projetos com IA, organizada em 4 areas:
- Planning (gold): projetos, backlog, features, sprints, tarefas, equipes, reunioes
- Development (silver): PRs, code review, agentes IA, repositorios
- Quality/Bronze: bugs, testes, acessibilidade, performance
- Governance (green): permissoes, RAG, Jira, configuracoes

Stack: React + TypeScript + Supabase + OpenAI. Login via Supabase Auth.

OBJETIVO: Resolver a duvida do usuario usando a DOCUMENTACAO abaixo. Sempre tente EXPLICAR primeiro. So ESCALE para erros REAIS do sistema.

FLUXO DE DECISAO:

1. VERIFICAR DOCUMENTACAO: A documentacao abaixo cobre o tema?
   Se SIM -> EXPLICAR com base na documentacao.

2. DUVIDAS DE USO (NUNCA escalar, sempre EXPLICAR):
   - Login/acesso, navegacao, "como faco", "onde fica"
   - Criar/editar projetos, tarefas, sprints, equipes, features, bugs
   - Upload de documentos, transcricoes, reunioes
   - Integracoes (Jira, GitHub, Calendar)
   - Geracao de documentos por IA, chat RAG
   - Backlog, priorizacao, knowledge base
   Todas sao DUVIDAS DE USO. Resolva pela documentacao. NAO escale.

3. SO ESCALAR para erros REAIS do sistema:
   - Erro 500, 502, 503, 404 persistente
   - Sistema fora do ar / tela branca / carregamento infinito
   - Dados perdidos ou corrompidos
   - Funcionalidade que ANTES funcionava e agora parou (bug confirmado)
   - Mensagens de erro do sistema (nao do usuario)

4. "Nao consigo logar" e DUVIDA DE USO -> EXPLICAR passos de login.
   "Nao consigo criar tarefa" e DUVIDA DE USO -> EXPLICAR.
   Qualquer "como faco" ou "nao consigo" sem erro tecnico -> EXPLICAR.

5. Se ambiguo, faca UMA pergunta curta. NUNCA repita perguntas.

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


CLASSIFY_SYSTEM_PROMPT = """Classifique a mensagem do usuario em UMA das categorias abaixo.

CATEGORIAS:
- "erro_sistema": O usuario relata um ERRO REAL do sistema (tela branca, erro 500, funcionalidade quebrada, dados corrompidos, sistema fora do ar)
- "duvida_uso": O usuario tem uma DUVIDA sobre como usar a plataforma (como faco, onde fica, nao consigo, como funciona)
- "solicitacao": O usuario faz uma SOLICITACAO (pede nova funcionalidade, melhoria, integracao, configuracao)

Responda APENAS com JSON:
{{"category": "erro_sistema" | "duvida_uso" | "solicitacao", "confidence": 0.0-1.0, "summary": "resumo de 1 linha"}}

MENSAGEM DO USUARIO:
{user_message}

HISTORICO:
{history}"""


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
    confidence: ConfidenceMetrics | None = None
    frustration_score: float = 0.0
    suggested_actions: list[str] | None = None
    classification_label: str = ""
    ticket_key: str = ""
    ticket_url: str = ""


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
        logger.warning("forced_decide_parse_failed", error=str(exc))
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


async def _classify_message(session: Session, user_message: str) -> dict:
    """Pre-classify the user message into a category for button confirmation."""
    prompt = CLASSIFY_SYSTEM_PROMPT.format(
        user_message=user_message,
        history=session.history_as_text()[:500],
    )
    try:
        raw = await _call_llm(prompt, "Responda em JSON.", max_tokens=300)
        return _parse_llm_json(raw)
    except Exception:
        return {
            "category": "duvida_uso",
            "confidence": 0.5,
            "summary": user_message[:100],
        }


CATEGORY_LABELS = {
    "erro_sistema": "Erro no sistema",
    "duvida_uso": "Duvida de uso",
    "solicitacao": "Solicitacao",
}

CATEGORY_BUTTON_IDS = {
    "erro_sistema": "confirm_erro_sistema",
    "duvida_uso": "confirm_duvida_uso",
    "solicitacao": "confirm_solicitacao",
}


async def process_turn(session: Session, user_message: str) -> TriageStep:
    """Advance the triage state machine by one user message."""
    session.add_user(user_message)

    # 0) MAX_TURNS guard — prevent infinite follow-up loops.
    if (
        len(session.turns) > MAX_TURNS
        and session.pending_classification != "awaiting_ticket_confirm"
    ):
        msg = (
            "Atingimos o limite de mensagens para esta conversa. "
            "Se ainda precisar de ajuda, clique em 'Nova conversa' para recomecar."
        )
        session.closed = True
        session.add_bot(msg)
        await save_session(session)
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
        await save_session(session)
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
        await save_session(session)
        return TriageStep(
            decision="ask",
            message=msg,
            reason="input detectado como invalido — pedido de esclarecimento",
            sources=[],
        )

    # 2.5) Handle classification confirmation from interactive buttons.
    if session.pending_classification == "awaiting_ticket_confirm":
        norm_msg = _normalize(user_message)
        if norm_msg in (
            "sim",
            "confirmar",
            "confirmo",
            "sim abrir",
            "yes",
            "abrir chamado",
            "abre um chamado",
            "abre chamado",
            "abre um",
        ):
            session.pending_classification = ""
            session.closed = True
            session.add_bot("[ESCALACAO] Criando chamado...")
            await save_session(session)

            from bot.services.jira_service import create_ticket

            error_summary = session.meaningful_user_text()[:200]
            ticket = await create_ticket(
                summary=error_summary,
                description=session.history_as_text(),
                urgency="urgente",
                channel=session.channel,
                conversation_id=session.id,
            )
            if ticket.success:
                msg = (
                    f"Chamado criado com sucesso!\n"
                    f"Protocolo: {ticket.key}\n"
                    f"Acompanhe em: {ticket.url}"
                )
            else:
                msg = (
                    f"Nao consegui criar o chamado: {ticket.error}\n"
                    f"Entre em contato com o suporte manualmente."
                )
            session.add_bot(msg)
            await save_session(session)
            return TriageStep(
                decision="escalate",
                message=msg,
                reason="chamado jira criado pelo usuario",
                sources=[],
                urgency="urgente",
                error_summary=error_summary,
                ticket_key=ticket.key if ticket.success else "",
                ticket_url=ticket.url if ticket.success else "",
            )
        else:
            session.pending_classification = ""
            session.classification_confirmed = True
            msg = "Entendi. Se precisar de mais alguma coisa, estou aqui."
            session.add_bot(msg)
            await save_session(session)
            return TriageStep(
                decision="explain",
                message=msg,
                reason="usuario recusou criacao de chamado",
                sources=[],
            )

    if session.pending_classification and not session.classification_confirmed:
        norm_msg = _normalize(user_message)
        classification = session.pending_classification
        if norm_msg in ("sim", "confirmar", "confirmo", "isso mesmo", "correto", "yes"):
            session.classification_confirmed = True
            session.pending_classification = ""
            session.add_bot(
                f"Categoria confirmada: {CATEGORY_LABELS.get(classification, classification)}"
            )
            await save_session(session)
        elif norm_msg.startswith("nao") or norm_msg in ("errado", "incorreto", "no"):
            session.classification_confirmed = False
            session.pending_classification = ""
            session.add_bot(
                "Entendi. Vou reavaliar. Pode descrever melhor o que precisa?"
            )
            await save_session(session)
            return TriageStep(
                decision="ask",
                message="Pode descrever melhor o que voce precisa?",
                reason="usuario corrigiu classificacao",
                sources=[],
            )
        elif any(
            user_message.strip().startswith(prefix) for prefix in ("confirm_", "cat_")
        ):
            button_id = user_message.strip()
            for cat_key, btn_id in CATEGORY_BUTTON_IDS.items():
                if button_id == btn_id or norm_msg == _normalize(btn_id):
                    session.classification_confirmed = True
                    session.pending_classification = ""
                    session.add_bot(f"Categoria confirmada: {CATEGORY_LABELS[cat_key]}")
                    await save_session(session)
                    break

    # 2.6) Pre-classification step: classify first real message with buttons.
    if not session.classification_confirmed and not session.pending_classification:
        classification_result = await _classify_message(session, user_message)
        category = classification_result.get("category", "duvida_uso")
        summary = classification_result.get("summary", user_message[:80])
        confidence = float(classification_result.get("confidence", 0.5))

        if confidence < 0.7:
            pass
        else:
            session.pending_classification = category
            label = CATEGORY_LABELS.get(category, category)
            msg = (
                f"Analisei sua mensagem e parece ser: *{label}*\n"
                f"Resumo: {summary}\n\n"
                f"Isso esta correto?"
            )
            session.add_bot(msg)
            await save_session(session)
            return TriageStep(
                decision="classify",
                message=msg,
                reason="pre-classificacao com botoes interativos",
                sources=[],
                classification_label=label,
            )

    # 3) Frustration detection — score the message and track the trend.
    frustration_score, frustration_escalate = detect_frustration(
        user_message, session.frustration_tracker
    )

    if frustration_escalate and not session.closed:
        empathy_prefix = (
            "Entendo sua frustracao e lamento pela experiencia. "
            "Vou encaminhar seu caso para um atendente agora mesmo."
        )
        error_summary = _build_fallback_summary(session, user_message)
        session.closed = True
        session.add_bot(f"[ESCALACAO POR FRUSTRACAO] {error_summary}")
        await save_session(session)
        logger.info(
            "frustration_escalation",
            session_id=session.id,
            frustration_score=frustration_score,
            trend_avg=session.frustration_tracker.trend_average,
            peak=session.frustration_tracker.peak_score,
        )
        return TriageStep(
            decision="escalate",
            message=f"{empathy_prefix}\n\n{error_summary}",
            reason="escalacao automatica por frustracao elevada",
            sources=[],
            urgency="urgente",
            error_summary=error_summary,
            frustration_score=frustration_score,
        )

    # 4) Language detection.
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

    # Compute confidence metrics from RAG results.
    confidence = compute_confidence(
        search_results=search, query=query, llm_parse_ok=True
    )

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
            logger.warning("triage_llm_parse_failed", error=str(exc))
            confidence = compute_confidence(
                search_results=search, query=query, llm_parse_ok=False
            )
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

    # Apply confidence-based override.
    override = should_override_decision(
        current_decision=decision,
        metrics=confidence,
        questions_asked=session.questions_asked,
        max_questions=MAX_QUESTIONS,
    )
    if override is not None:
        decision = override

    logger.info(
        "triage_decision",
        session_id=session.id,
        decision=decision,
        frustration_score=frustration_score,
        frustration_trend=session.frustration_tracker.trend_average,
        **confidence.as_dict(),
    )

    # 3) Duplicate-question guard: if LLM wants to ask the same thing again,
    # force a decision instead.
    if decision == "ask":
        new_q = (parsed.get("question") or "").strip()
        if session.last_bot_question and _similar_question(
            new_q, session.last_bot_question
        ):
            logger.info("duplicate_question_detected", session_id=session.id)
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
        await save_session(session)
        return TriageStep(
            decision="ask",
            message=question,
            reason=parsed.get("reason") or "",
            sources=[],
            confidence=confidence,
            frustration_score=frustration_score,
        )

    if decision == "explain":
        explanation = (parsed.get("explanation") or "").strip()
        if not explanation:
            explanation = (
                "Com base na documentacao, este parece ser um ajuste de uso. "
                "Verifique os passos no material de referencia abaixo."
            )
        # Prepend empathy when moderate frustration is detected.
        if frustration_score >= 0.4:
            explanation = (
                f"Entendo que isso deve ser frustrante. Vou te ajudar.\n\n{explanation}"
            )
        session.questions_asked = 0
        session.in_follow_up = True
        session.add_bot(explanation)
        await save_session(session)
        return TriageStep(
            decision="explain",
            message=explanation,
            reason=parsed.get("reason") or "",
            sources=sources,
            confidence=confidence,
            frustration_score=frustration_score,
        )

    # escalate — offer Jira ticket creation
    error_summary = (parsed.get("error_summary") or "").strip()
    if len(error_summary) < 10:
        error_summary = _build_fallback_summary(session, user_message)
    urgency = (parsed.get("urgency") or "urgente").strip().lower() or "urgente"
    if frustration_score >= 0.6:
        urgency = "urgente"

    session.pending_classification = "awaiting_ticket_confirm"
    confirm_msg = (
        f"Parece que voce esta enfrentando um problema tecnico: {error_summary}\n\n"
        f"Deseja abrir um chamado para o time de suporte?"
    )
    session.add_bot(confirm_msg)
    await save_session(session)
    return TriageStep(
        decision="confirm_ticket",
        message=confirm_msg,
        reason="solicitando confirmacao para criar ticket jira",
        sources=sources,
        urgency=urgency,
        error_summary=error_summary,
        confidence=confidence,
        frustration_score=frustration_score,
    )
