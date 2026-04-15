"""
Warm handoff escalation context for intelligent support escalation.

Builds a rich ``EscalationContext`` containing full conversation metadata,
generates an LLM-powered conversation summary, and produces an Adaptive Card
for the support team with all relevant context for a seamless handoff.

This module is designed to be called from ``bot/app.py`` or
``bot/services/triage_flow.py`` when an escalation decision is reached.
It does **not** modify those files directly — it exports pure functions.

Usage::

    from bot.services.escalation_context import (
        build_escalation_context,
        build_warm_handoff_card,
        generate_conversation_summary,
    )

    ctx = await build_escalation_context(session, user_name, ...)
    card = build_warm_handoff_card(ctx)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import structlog

from bot.services.cards import (
    CARD_SCHEMA,
    CARD_VERSION,
    _action_submit,
    _text_block,
    card_to_attachment,
)
from bot.services.llm_service import _call_llm

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_SUMMARY_TOKENS = 400

SUMMARY_SYSTEM_PROMPT = """Voce e um assistente que resume conversas de suporte tecnico para handoff a um atendente humano.

REGRAS:
- Resuma a conversa em NO MAXIMO 3-4 frases objetivas.
- Inclua: o que o usuario tentou fazer, qual o problema, e o que o bot ja tentou responder.
- Se o usuario demonstrou frustracao, mencione isso brevemente.
- Use linguagem profissional e direta.
- Responda SOMENTE com o resumo, sem formatacao extra.
- Responda no mesmo idioma predominante da conversa (portugues ou ingles)."""


# ---------------------------------------------------------------------------
# EscalationContext dataclass
# ---------------------------------------------------------------------------


@dataclass
class EscalationContext:
    """Full metadata for a warm handoff escalation.

    Attributes
    ----------
    session_id:
        Unique session identifier.
    user_name:
        Display name of the user requesting support.
    user_id:
        Platform-specific user identifier (e.g. Teams AAD object ID).
    conversation_id:
        Teams conversation identifier.
    service_url:
        Bot Framework service URL for proactive messages.
    timestamp:
        ISO 8601 timestamp of the escalation event.
    urgency:
        Urgency level: ``urgente``, ``normal``, or ``baixa``.
    error_summary:
        Short (1-2 sentence) summary of the reported issue.
    conversation_summary:
        LLM-generated summary of the full conversation.
    conversation_history:
        Raw conversation turns as list of ``{role, content}`` dicts.
    sources_consulted:
        Knowledge base sources that were searched during triage.
    frustration_score:
        Frustration detection score (0.0 - 1.0).
    confidence_score:
        Overall confidence score from the triage process (0.0 - 1.0).
    escalation_reason:
        Why the bot decided to escalate (e.g. "erro real do sistema",
        "frustracao elevada", "confianca baixa").
    questions_asked:
        Number of clarifying questions the bot asked before escalating.
    category:
        Problem category if identified (e.g. "login", "system_error").
    tenant_id:
        Microsoft tenant ID for the user's organization.
    """

    session_id: str
    user_name: str
    user_id: str = ""
    conversation_id: str = ""
    service_url: str = ""
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    urgency: str = "normal"
    error_summary: str = ""
    conversation_summary: str = ""
    conversation_history: list[dict[str, str]] = field(default_factory=list)
    sources_consulted: list[str] = field(default_factory=list)
    frustration_score: float = 0.0
    confidence_score: float = 0.0
    escalation_reason: str = ""
    questions_asked: int = 0
    category: str = ""
    tenant_id: str = ""

    @property
    def history_as_text(self) -> str:
        """Format conversation history as readable text."""
        parts: list[str] = []
        for turn in self.conversation_history:
            role = "USUARIO" if turn.get("role") == "user" else "BOT"
            parts.append(f"{role}: {turn.get('content', '')}")
        return "\n".join(parts)

    @property
    def urgency_label(self) -> str:
        """Human-readable urgency label."""
        labels = {
            "urgente": "Urgente",
            "normal": "Normal",
            "baixa": "Baixa",
        }
        return labels.get(self.urgency, self.urgency.capitalize())

    @property
    def urgency_color(self) -> str:
        """Adaptive Card color token for the urgency level."""
        colors = {
            "urgente": "Attention",
            "normal": "Warning",
            "baixa": "Good",
        }
        return colors.get(self.urgency, "Default")

    def to_dict(self) -> dict[str, Any]:
        """Serialize context for logging or storage."""
        return {
            "session_id": self.session_id,
            "user_name": self.user_name,
            "user_id": self.user_id,
            "conversation_id": self.conversation_id,
            "timestamp": self.timestamp,
            "urgency": self.urgency,
            "error_summary": self.error_summary,
            "conversation_summary": self.conversation_summary,
            "sources_consulted": self.sources_consulted,
            "frustration_score": self.frustration_score,
            "confidence_score": self.confidence_score,
            "escalation_reason": self.escalation_reason,
            "questions_asked": self.questions_asked,
            "category": self.category,
        }


# ---------------------------------------------------------------------------
# LLM conversation summary
# ---------------------------------------------------------------------------


async def generate_conversation_summary(
    conversation_history: list[dict[str, str]],
    error_summary: str = "",
) -> str:
    """Generate a concise conversation summary via LLM.

    Parameters
    ----------
    conversation_history:
        List of ``{role, content}`` dicts from the session.
    error_summary:
        Optional short error summary to provide additional context.

    Returns
    -------
    str
        A 3-4 sentence summary of the conversation, or a fallback
        if the LLM call fails.
    """
    if not conversation_history:
        return error_summary or "Sem historico de conversa disponivel."

    history_text_parts: list[str] = []
    for turn in conversation_history:
        role = "USUARIO" if turn.get("role") == "user" else "BOT"
        content = turn.get("content", "").strip()
        if content:
            history_text_parts.append(f"{role}: {content}")
    history_text = "\n".join(history_text_parts)

    user_message = f"Resuma esta conversa de suporte:\n\n{history_text}"
    if error_summary:
        user_message += f"\n\nResumo do erro reportado: {error_summary}"

    t0 = time.monotonic()
    try:
        summary = await _call_llm(
            SUMMARY_SYSTEM_PROMPT,
            user_message,
            max_tokens=MAX_SUMMARY_TOKENS,
        )
        summary = summary.strip()
        latency_ms = round((time.monotonic() - t0) * 1000, 1)

        logger.info(
            "escalation_summary_generated",
            latency_ms=latency_ms,
            summary_length=len(summary),
        )

        return (
            summary
            if summary
            else _fallback_summary(conversation_history, error_summary)
        )

    except Exception as exc:
        latency_ms = round((time.monotonic() - t0) * 1000, 1)
        logger.warning(
            "escalation_summary_failed",
            error=str(exc),
            latency_ms=latency_ms,
            fallback="extractive",
        )
        return _fallback_summary(conversation_history, error_summary)


def _fallback_summary(
    conversation_history: list[dict[str, str]],
    error_summary: str = "",
) -> str:
    """Build a simple extractive summary when the LLM is unavailable.

    Concatenates the user turns to provide the support agent with raw context.
    """
    user_messages = [
        turn.get("content", "").strip()
        for turn in conversation_history
        if turn.get("role") == "user" and turn.get("content", "").strip()
    ]

    if not user_messages and error_summary:
        return error_summary

    combined = " | ".join(user_messages)
    if error_summary:
        combined = f"{error_summary} -- Mensagens do usuario: {combined}"

    return combined[:500] if combined else "Sem detalhes disponiveis para resumo."


# ---------------------------------------------------------------------------
# Build EscalationContext
# ---------------------------------------------------------------------------


async def build_escalation_context(
    session_id: str,
    user_name: str,
    conversation_history: list[dict[str, str]],
    error_summary: str = "",
    urgency: str = "normal",
    sources: list[str] | None = None,
    frustration_score: float = 0.0,
    confidence_score: float = 0.0,
    escalation_reason: str = "",
    questions_asked: int = 0,
    category: str = "",
    user_id: str = "",
    conversation_id: str = "",
    service_url: str = "",
    tenant_id: str = "",
) -> EscalationContext:
    """Build a complete EscalationContext with LLM-generated summary.

    This is the main entry point for creating an escalation context.
    It generates the conversation summary via LLM and assembles all
    metadata into a single dataclass.

    Parameters
    ----------
    session_id:
        Unique session identifier from triage flow.
    user_name:
        Display name of the user.
    conversation_history:
        Full list of ``{role, content}`` turns from the session.
    error_summary:
        Short description of the reported issue.
    urgency:
        Urgency level string.
    sources:
        Knowledge base sources consulted during triage.
    frustration_score:
        Frustration detection score (0.0 - 1.0).
    confidence_score:
        Confidence score from the triage process (0.0 - 1.0).
    escalation_reason:
        Human-readable reason for the escalation.
    questions_asked:
        Number of clarifying questions asked before escalation.
    category:
        Problem category if identified.
    user_id:
        Platform user identifier.
    conversation_id:
        Teams conversation identifier.
    service_url:
        Bot Framework service URL.
    tenant_id:
        Microsoft tenant ID.

    Returns
    -------
    EscalationContext
        Fully populated context ready for card building or logging.
    """
    conversation_summary = await generate_conversation_summary(
        conversation_history=conversation_history,
        error_summary=error_summary,
    )

    ctx = EscalationContext(
        session_id=session_id,
        user_name=user_name,
        user_id=user_id,
        conversation_id=conversation_id,
        service_url=service_url,
        urgency=urgency,
        error_summary=error_summary,
        conversation_summary=conversation_summary,
        conversation_history=conversation_history,
        sources_consulted=sources or [],
        frustration_score=frustration_score,
        confidence_score=confidence_score,
        escalation_reason=escalation_reason,
        questions_asked=questions_asked,
        category=category,
        tenant_id=tenant_id,
    )

    logger.info(
        "escalation_context_built",
        session_id=session_id,
        user_name=user_name,
        urgency=urgency,
        frustration_score=frustration_score,
        confidence_score=confidence_score,
        escalation_reason=escalation_reason,
        summary_length=len(conversation_summary),
    )

    return ctx


# ---------------------------------------------------------------------------
# Warm handoff Adaptive Card
# ---------------------------------------------------------------------------


def build_warm_handoff_card(ctx: EscalationContext) -> dict[str, Any]:
    """Build a rich Adaptive Card for the support team with full escalation context.

    The card includes:
      - Header with urgency badge
      - User information (name, session, timestamp)
      - Escalation reason and category
      - LLM-generated conversation summary
      - Confidence and frustration metrics
      - Sources consulted from the knowledge base
      - Truncated conversation history
      - Action buttons for the support agent

    Parameters
    ----------
    ctx:
        Fully populated EscalationContext.

    Returns
    -------
    dict
        Adaptive Card JSON payload ready for ``card_to_attachment()``.
    """
    fallback_text = (
        f"Nova escalacao de suporte - Usuario: {ctx.user_name} | "
        f"Urgencia: {ctx.urgency_label} | Resumo: {ctx.error_summary}"
    )

    # -- Header with urgency badge --
    header: list[dict[str, Any]] = [
        {
            "type": "ColumnSet",
            "columns": [
                {
                    "type": "Column",
                    "width": "stretch",
                    "items": [
                        _text_block(
                            "Escalacao - Handoff de Suporte",
                            size="Medium",
                            weight="Bolder",
                            color="Accent",
                        ),
                    ],
                },
                {
                    "type": "Column",
                    "width": "auto",
                    "items": [
                        _text_block(
                            ctx.urgency_label.upper(),
                            size="Small",
                            weight="Bolder",
                            color=ctx.urgency_color,
                            horizontalAlignment="Right",
                        ),
                    ],
                },
            ],
        },
    ]

    # -- User and session info --
    facts: list[dict[str, str]] = [
        {"title": "Usuario", "value": ctx.user_name},
        {"title": "Sessao", "value": ctx.session_id[:30]},
        {"title": "Horario", "value": _format_timestamp(ctx.timestamp)},
        {"title": "Urgencia", "value": ctx.urgency_label},
    ]
    if ctx.category:
        facts.append({"title": "Categoria", "value": ctx.category})
    if ctx.questions_asked > 0:
        facts.append({"title": "Perguntas feitas", "value": str(ctx.questions_asked)})

    info_section: list[dict[str, Any]] = [
        {
            "type": "FactSet",
            "spacing": "Medium",
            "facts": facts,
        },
    ]

    # -- Escalation reason --
    reason_section: list[dict[str, Any]] = []
    if ctx.escalation_reason:
        reason_section = [
            _text_block("Motivo da Escalacao", weight="Bolder", spacing="Medium"),
            _text_block(ctx.escalation_reason[:300], spacing="Small"),
        ]

    # -- Error summary --
    summary_section: list[dict[str, Any]] = []
    if ctx.error_summary:
        summary_section = [
            _text_block("Problema Reportado", weight="Bolder", spacing="Medium"),
            _text_block(ctx.error_summary[:400], spacing="Small"),
        ]

    # -- LLM conversation summary --
    llm_summary_section: list[dict[str, Any]] = []
    if ctx.conversation_summary:
        llm_summary_section = [
            _text_block(
                "Resumo da Conversa (IA)",
                weight="Bolder",
                spacing="Medium",
            ),
            _text_block(ctx.conversation_summary[:600], spacing="Small"),
        ]

    # -- Metrics (confidence + frustration) --
    metrics_section: list[dict[str, Any]] = []
    if ctx.confidence_score > 0 or ctx.frustration_score > 0:
        metrics_facts: list[dict[str, str]] = []
        if ctx.confidence_score > 0:
            confidence_pct = f"{ctx.confidence_score * 100:.0f}%"
            metrics_facts.append({"title": "Confianca do bot", "value": confidence_pct})
        if ctx.frustration_score > 0:
            frustration_pct = f"{ctx.frustration_score * 100:.0f}%"
            metrics_facts.append(
                {"title": "Frustracao detectada", "value": frustration_pct}
            )
        if metrics_facts:
            metrics_section = [
                _text_block("Metricas", weight="Bolder", spacing="Medium"),
                {
                    "type": "FactSet",
                    "spacing": "Small",
                    "facts": metrics_facts,
                },
            ]

    # -- Sources consulted --
    sources_section: list[dict[str, Any]] = []
    if ctx.sources_consulted:
        sources_text = ", ".join(ctx.sources_consulted[:5])
        sources_section = [
            _text_block("Fontes Consultadas", weight="Bolder", spacing="Medium"),
            _text_block(
                sources_text,
                size="Small",
                isSubtle=True,
                spacing="Small",
            ),
        ]

    # -- Conversation history (truncated) --
    history_section: list[dict[str, Any]] = []
    if ctx.conversation_history:
        history_text = ctx.history_as_text
        # Truncate to keep the card readable
        if len(history_text) > 800:
            history_text = history_text[:800] + "\n... (truncado)"
        history_section = [
            _text_block("Historico da Conversa", weight="Bolder", spacing="Medium"),
            _text_block(
                history_text,
                size="Small",
                isSubtle=True,
                spacing="Small",
            ),
        ]

    # -- Assemble body --
    body: list[dict[str, Any]] = (
        header
        + info_section
        + reason_section
        + summary_section
        + llm_summary_section
        + metrics_section
        + sources_section
        + history_section
    )

    # -- Actions for support agent --
    actions: list[dict[str, Any]] = [
        _action_submit(
            "Assumir atendimento",
            "claim_escalation",
            {"session_id": ctx.session_id, "user_id": ctx.user_id},
        ),
        _action_submit(
            "Solicitar mais informacoes",
            "request_more_info",
            {"session_id": ctx.session_id, "user_id": ctx.user_id},
        ),
    ]

    card: dict[str, Any] = {
        "$schema": CARD_SCHEMA,
        "type": "AdaptiveCard",
        "version": CARD_VERSION,
        "body": body,
        "actions": actions,
        "fallbackText": fallback_text,
    }

    return card


def build_user_escalation_confirmation_card(
    ctx: EscalationContext,
) -> dict[str, Any]:
    """Build a confirmation card shown to the user when their case is escalated.

    This is a simpler card for the end user (not the support team),
    confirming the handoff and providing a summary.

    Parameters
    ----------
    ctx:
        Fully populated EscalationContext.

    Returns
    -------
    dict
        Adaptive Card JSON payload.
    """
    fallback_text = (
        f"Seu caso foi encaminhado para o time de suporte. "
        f"Resumo: {ctx.error_summary} | Urgencia: {ctx.urgency_label}"
    )

    body: list[dict[str, Any]] = [
        _text_block(
            "Seu caso foi encaminhado",
            size="Medium",
            weight="Bolder",
            color="Accent",
        ),
        _text_block(
            "Um membro do time de suporte vai analisar seu caso e entrar "
            "em contato em breve. Voce nao precisa repetir as informacoes, "
            "o atendente tera acesso ao historico completo.",
            spacing="Small",
        ),
        {
            "type": "FactSet",
            "spacing": "Medium",
            "facts": [
                {"title": "Protocolo", "value": ctx.session_id[:12]},
                {"title": "Urgencia", "value": ctx.urgency_label},
                {"title": "Resumo", "value": (ctx.error_summary or "Em analise")[:200]},
            ],
        },
        _text_block(
            f"Prioridade: {ctx.urgency_label.upper()}",
            size="Small",
            weight="Bolder",
            color=ctx.urgency_color,
            spacing="Small",
        ),
    ]

    actions: list[dict[str, Any]] = [
        _action_submit(
            "Voltar ao menu",
            "back_to_menu",
            {"session_id": ctx.session_id},
        ),
    ]

    card: dict[str, Any] = {
        "$schema": CARD_SCHEMA,
        "type": "AdaptiveCard",
        "version": CARD_VERSION,
        "body": body,
        "actions": actions,
        "fallbackText": fallback_text,
    }

    return card


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def escalation_card_to_attachment(card: dict[str, Any]) -> dict[str, Any]:
    """Convenience wrapper — delegates to ``cards.card_to_attachment``."""
    return card_to_attachment(card)


def _format_timestamp(iso_timestamp: str) -> str:
    """Format an ISO timestamp to a human-readable string."""
    try:
        dt = datetime.fromisoformat(iso_timestamp)
        return dt.strftime("%d/%m/%Y %H:%M")
    except (ValueError, TypeError):
        return iso_timestamp
