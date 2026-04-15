"""
Adaptive Cards service for interactive UX in Microsoft Teams.

Builds card JSON payloads following the Adaptive Cards schema v1.5 with
Universal Action Model (Action.Execute) for bot-initiated actions.

All cards include ``fallbackText`` so that clients without Adaptive Card
support still receive a meaningful plain-text message.

Card types:
  - welcome:              Greeting card with quick-action buttons
  - explanation:          RAG answer card with feedback buttons (Sim/Nao)
  - escalation:           Escalation confirmation card with context summary
  - feedback:             Thank-you card after user rates an answer
  - problem_form:         Task Module form for structured problem reporting
  - problem_confirmation: Confirmation card shown after problem submission
  - ask:                  Clarifying question card with suggested quick-reply buttons
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import structlog

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CARD_SCHEMA = "http://adaptivecards.io/schemas/adaptive-card.json"
CARD_VERSION = "1.5"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _card_envelope(
    body: list[dict], actions: list[dict] | None = None, fallback_text: str = ""
) -> dict[str, Any]:
    """Wrap body elements and actions into a complete Adaptive Card JSON."""
    card: dict[str, Any] = {
        "$schema": CARD_SCHEMA,
        "type": "AdaptiveCard",
        "version": CARD_VERSION,
        "body": body,
    }
    if actions:
        card["actions"] = actions
    if fallback_text:
        card["fallbackText"] = fallback_text
    return card


def _action_submit(title: str, verb: str, data: dict | None = None) -> dict[str, Any]:
    """Build an Action.Submit element.

    ``Action.Submit`` is used instead of ``Action.Execute`` because it works
    reliably in Teams personal scope without requiring Universal Action Model
    configuration in the app manifest.  The ``verb`` is embedded inside the
    ``data`` payload so that ``on_message_activity`` can route the submission.
    """
    action_data = data or {}
    action_data["verb"] = verb
    return {
        "type": "Action.Submit",
        "title": title,
        "data": action_data,
    }


def _text_block(text: str, **kwargs: Any) -> dict[str, Any]:
    """Build a TextBlock element with optional overrides."""
    block: dict[str, Any] = {
        "type": "TextBlock",
        "text": text,
        "wrap": True,
    }
    block.update(kwargs)
    return block


def card_to_attachment(card: dict[str, Any]) -> dict[str, Any]:
    """Wrap an Adaptive Card dict into a Bot Framework attachment object."""
    return {
        "contentType": "application/vnd.microsoft.card.adaptive",
        "content": card,
    }


def card_to_activity(card: dict[str, Any], fallback_text: str = "") -> dict[str, Any]:
    """Build a Bot Framework Activity dict containing an Adaptive Card attachment."""
    return {
        "type": "message",
        "attachments": [card_to_attachment(card)],
        "text": fallback_text or card.get("fallbackText", ""),
    }


# ---------------------------------------------------------------------------
# Welcome Card
# ---------------------------------------------------------------------------


def build_welcome_card() -> dict[str, Any]:
    """Build a welcome card shown when a user first interacts with the bot.

    Includes quick-action buttons for common support scenarios.
    """
    fallback = (
        "Ola! Sou o Workforce Help. "
        "Me descreva o que voce precisa ou escolha uma das opcoes abaixo."
    )

    body = [
        _text_block(
            "Workforce Help",
            size="Large",
            weight="Bolder",
            color="Accent",
        ),
        _text_block(
            "Ola! Sou o assistente de suporte da plataforma DR AI Workforce. "
            "Me descreva o que voce precisa ou escolha uma das opcoes rapidas abaixo.",
            spacing="Small",
        ),
        {
            "type": "ColumnSet",
            "spacing": "Medium",
            "columns": [
                {
                    "type": "Column",
                    "width": "stretch",
                    "items": [
                        _text_block(
                            "Como posso ajudar?",
                            weight="Bolder",
                            spacing="Small",
                        ),
                    ],
                },
            ],
        },
    ]

    actions = [
        _action_submit(
            "Problema de login",
            "login_issue",
            {"category": "login"},
        ),
        _action_submit(
            "Duvida sobre funcionalidade",
            "feature_question",
            {"category": "feature"},
        ),
        _action_submit(
            "Erro no sistema",
            "system_error",
            {"category": "error"},
        ),
        _action_submit(
            "Reportar problema",
            "report_problem",
            {"category": "report"},
        ),
    ]

    return _card_envelope(body, actions, fallback_text=fallback)


# ---------------------------------------------------------------------------
# Explanation Card (with feedback buttons)
# ---------------------------------------------------------------------------


def build_explanation_card(
    explanation: str,
    sources: list[str] | None = None,
    session_id: str = "",
) -> dict[str, Any]:
    """Build a card displaying a RAG-based explanation with feedback buttons.

    Parameters
    ----------
    explanation:
        The answer text generated from the knowledge base.
    sources:
        List of document source names used for the answer.
    session_id:
        Current session identifier for tracking feedback.
    """
    fallback = f"{explanation}\n\nEssa resposta ajudou? Responda Sim ou Nao."

    body: list[dict[str, Any]] = [
        _text_block(
            "Resposta",
            size="Medium",
            weight="Bolder",
            color="Accent",
        ),
        _text_block(explanation, spacing="Small"),
    ]

    if sources:
        sources_text = ", ".join(sources)
        body.append(
            _text_block(
                f"Fonte: {sources_text}",
                size="Small",
                isSubtle=True,
                spacing="Small",
            )
        )

    body.append(
        _text_block(
            "Essa resposta ajudou?",
            weight="Bolder",
            spacing="Medium",
        )
    )

    actions = [
        _action_submit(
            "Sim, ajudou!",
            "feedback_yes",
            {"session_id": session_id, "helpful": True},
        ),
        _action_submit(
            "Nao, preciso de mais ajuda",
            "feedback_no",
            {"session_id": session_id, "helpful": False},
        ),
    ]

    return _card_envelope(body, actions, fallback_text=fallback)


# ---------------------------------------------------------------------------
# Escalation Card
# ---------------------------------------------------------------------------


def build_escalation_card(
    error_summary: str,
    urgency: str = "normal",
    session_id: str = "",
) -> dict[str, Any]:
    """Build a card confirming escalation to a human support agent.

    Parameters
    ----------
    error_summary:
        Short description of the issue being escalated.
    urgency:
        Urgency level: ``urgente``, ``normal``, or ``baixa``.
    session_id:
        Current session identifier.
    """
    urgency_colors = {
        "urgente": "Attention",
        "normal": "Warning",
        "baixa": "Good",
    }
    urgency_color = urgency_colors.get(urgency, "Default")

    fallback = (
        f"Seu caso foi encaminhado para o time de suporte. "
        f"Resumo: {error_summary} | Urgencia: {urgency}"
    )

    body: list[dict[str, Any]] = [
        _text_block(
            "Escalacao para Suporte",
            size="Medium",
            weight="Bolder",
            color="Accent",
        ),
        _text_block(
            "Seu caso foi encaminhado para o time de suporte humano. "
            "Um membro da equipe vai entrar em contato em breve.",
            spacing="Small",
        ),
        {
            "type": "FactSet",
            "spacing": "Medium",
            "facts": [
                {"title": "Resumo", "value": error_summary[:200]},
                {"title": "Urgencia", "value": urgency.capitalize()},
            ],
        },
        _text_block(
            f"Prioridade: {urgency.upper()}",
            size="Small",
            weight="Bolder",
            color=urgency_color,
            spacing="Small",
        ),
    ]

    actions = [
        _action_submit(
            "Voltar ao menu",
            "back_to_menu",
            {"session_id": session_id},
        ),
    ]

    return _card_envelope(body, actions, fallback_text=fallback)


# ---------------------------------------------------------------------------
# Feedback Card (thank-you after rating)
# ---------------------------------------------------------------------------


def build_feedback_card(helpful: bool, session_id: str = "") -> dict[str, Any]:
    """Build a thank-you card after the user provides feedback.

    Parameters
    ----------
    helpful:
        Whether the user indicated the answer was helpful.
    session_id:
        Current session identifier.
    """
    if helpful:
        title = "Obrigado pelo feedback!"
        message = (
            "Fico feliz que a resposta tenha ajudado. "
            "Se precisar de mais alguma coisa, e so me chamar!"
        )
        fallback = "Obrigado! Se precisar de mais ajuda, e so me chamar."
    else:
        title = "Vamos resolver isso"
        message = (
            "Sinto que a resposta nao foi suficiente. "
            "Voce pode descrever melhor o problema ou eu posso "
            "encaminhar para o time de suporte."
        )
        fallback = (
            "Sinto que a resposta nao foi suficiente. "
            "Descreva melhor ou posso escalar para o suporte."
        )

    body = [
        _text_block(title, size="Medium", weight="Bolder", color="Accent"),
        _text_block(message, spacing="Small"),
    ]

    actions: list[dict[str, Any]] = []
    if not helpful:
        actions = [
            _action_submit(
                "Falar com suporte",
                "escalate",
                {"session_id": session_id, "reason": "feedback_negative"},
            ),
            _action_submit(
                "Tentar novamente",
                "back_to_menu",
                {"session_id": session_id},
            ),
        ]
    else:
        actions = [
            _action_submit(
                "Nova consulta",
                "back_to_menu",
                {"session_id": session_id},
            ),
        ]

    return _card_envelope(body, actions, fallback_text=fallback)


# ---------------------------------------------------------------------------
# Ask Card (clarifying question with quick-reply suggestions)
# ---------------------------------------------------------------------------


def build_ask_card(
    question: str,
    suggested_replies: list[str] | None = None,
    session_id: str = "",
) -> dict[str, Any]:
    """Build a card for a clarifying question with optional quick-reply buttons.

    Parameters
    ----------
    question:
        The clarifying question text.
    suggested_replies:
        Optional list of quick-reply button labels. Each reply is sent as
        user text when clicked.
    session_id:
        Current session identifier.
    """
    fallback = question

    body = [
        _text_block(
            "Preciso de mais informacoes",
            size="Medium",
            weight="Bolder",
            color="Accent",
        ),
        _text_block(question, spacing="Small"),
    ]

    actions: list[dict[str, Any]] = []
    if suggested_replies:
        for reply_text in suggested_replies[:4]:  # Limit to 4 quick-reply buttons
            actions.append(
                _action_submit(
                    reply_text,
                    "quick_reply",
                    {"session_id": session_id, "reply_text": reply_text},
                )
            )

    return _card_envelope(body, actions, fallback_text=fallback)


# ---------------------------------------------------------------------------
# Problem Form Card (Task Module)
# ---------------------------------------------------------------------------

# Valid category values accepted by the problem form.
PROBLEM_CATEGORIES: dict[str, str] = {
    "login": "Problema de login / acesso",
    "system_error": "Erro no sistema",
    "feature_broken": "Funcionalidade nao funciona",
    "usage_question": "Duvida de uso",
    "performance": "Lentidao / performance",
    "other": "Outro",
}

# Valid urgency levels.
URGENCY_LEVELS: dict[str, str] = {
    "baixa": "Baixa - Nao impede meu trabalho",
    "normal": "Normal - Atrapalha mas consigo continuar",
    "urgente": "Urgente - Estou parado, nao consigo trabalhar",
}


def build_problem_form_card() -> dict[str, Any]:
    """Build a structured problem report form for use in a Task Module.

    The form collects:
      - Problem category (Input.ChoiceSet -- compact dropdown)
      - Description (Input.Text multiline, required, max 2000 chars)
      - Urgency level (Input.ChoiceSet -- expanded radio buttons)
      - Steps to reproduce (Input.Text multiline, optional, max 1500 chars)
      - Contact info (Input.Text, optional -- for follow-up outside Teams)

    The ``Action.Execute`` verb is ``submit_problem`` with an ``action``
    marker so the ``on_invoke_activity`` handler in ``bot/app.py`` can
    distinguish this form from other card submissions.

    Task Module wiring (handled by task 2.2 in ``bot/app.py``):
      - ``task/fetch`` with ``commandId == "report_problem"`` should return
        ``build_task_module_response(build_problem_form_card(), title=...)``.
      - ``task/submit`` should call ``process_problem_submission(data)`` to
        parse and validate the payload, then route through ``triage_flow``
        and return ``build_task_module_submit_response(...)`` or
        ``build_problem_confirmation_card(...)`` wrapped in
        ``build_task_module_response(...)`` for a second step.
    """
    fallback = (
        "Para reportar um problema, descreva: "
        "1) Categoria (login, funcionalidade, erro, outro) "
        "2) Descricao detalhada "
        "3) Urgencia (baixa, normal, urgente)"
    )

    body: list[dict[str, Any]] = [
        _text_block(
            "Reportar Problema",
            size="Medium",
            weight="Bolder",
            color="Accent",
        ),
        _text_block(
            "Preencha os campos abaixo para que possamos entender "
            "e resolver seu problema mais rapidamente.",
            spacing="Small",
            isSubtle=True,
        ),
        # Category selector
        {
            "type": "Input.ChoiceSet",
            "id": "category",
            "label": "Categoria",
            "style": "compact",
            "isRequired": True,
            "errorMessage": "Selecione uma categoria",
            "placeholder": "Selecione a categoria do problema",
            "choices": [
                {"title": title, "value": value}
                for value, title in PROBLEM_CATEGORIES.items()
            ],
        },
        # Description
        {
            "type": "Input.Text",
            "id": "description",
            "label": "Descricao do problema",
            "isMultiline": True,
            "isRequired": True,
            "errorMessage": "Descreva o problema",
            "placeholder": "Descreva o que aconteceu com o maximo de detalhes possivel...",
            "maxLength": 2000,
        },
        # Urgency
        {
            "type": "Input.ChoiceSet",
            "id": "urgency",
            "label": "Urgencia",
            "style": "expanded",
            "isRequired": True,
            "errorMessage": "Selecione a urgencia",
            "value": "normal",
            "choices": [
                {"title": title, "value": value}
                for value, title in URGENCY_LEVELS.items()
            ],
        },
        # Steps to reproduce (optional)
        {
            "type": "Input.Text",
            "id": "steps_to_reproduce",
            "label": "Passos para reproduzir (opcional)",
            "isMultiline": True,
            "isRequired": False,
            "placeholder": (
                "1. Acessei a pagina X\n2. Cliquei no botao Y\n3. Apareceu o erro Z"
            ),
            "maxLength": 1500,
        },
        # Contact info (optional) -- for follow-up outside Teams
        {
            "type": "Input.Text",
            "id": "contact_info",
            "label": "Contato para retorno (opcional)",
            "isMultiline": False,
            "isRequired": False,
            "placeholder": "E-mail ou ramal para retorno",
            "maxLength": 200,
        },
    ]

    actions = [
        _action_submit(
            "Enviar problema",
            "submit_problem",
            {"action": "submit_problem"},
        ),
    ]

    return _card_envelope(body, actions, fallback_text=fallback)


# ---------------------------------------------------------------------------
# Problem submission processing
# ---------------------------------------------------------------------------


@dataclass
class ProblemSubmission:
    """Validated problem submission data from the Task Module form.

    Attributes
    ----------
    category:
        One of the keys in ``PROBLEM_CATEGORIES``.
    category_label:
        Human-readable label for the selected category.
    description:
        User-provided problem description (stripped, max 2000 chars).
    urgency:
        One of ``baixa``, ``normal``, ``urgente``.
    urgency_label:
        Human-readable label for the selected urgency.
    steps_to_reproduce:
        Optional reproduction steps.
    contact_info:
        Optional contact info for follow-up.
    validation_errors:
        List of validation error messages (empty when valid).
    """

    category: str = ""
    category_label: str = ""
    description: str = ""
    urgency: str = "normal"
    urgency_label: str = ""
    steps_to_reproduce: str = ""
    contact_info: str = ""
    validation_errors: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Return True when the submission passes all validations."""
        return len(self.validation_errors) == 0

    def to_triage_text(self) -> str:
        """Format the submission as plain text for ``process_turn()``.

        This produces a structured message that the triage flow can process
        as if the user had typed a detailed problem description.
        """
        parts = [
            f"[Categoria: {self.category_label}]",
            f"[Urgencia: {self.urgency_label}]",
            self.description,
        ]
        if self.steps_to_reproduce:
            parts.append(f"Passos para reproduzir: {self.steps_to_reproduce}")
        return "\n".join(parts)


def process_problem_submission(data: dict[str, Any]) -> ProblemSubmission:
    """Parse and validate a ``task/submit`` payload from the problem form.

    Parameters
    ----------
    data:
        The raw ``turn_context.activity.value`` dict submitted by the
        Adaptive Card. Expected keys: ``category``, ``description``,
        ``urgency``, ``steps_to_reproduce`` (optional),
        ``contact_info`` (optional).

    Returns
    -------
    ProblemSubmission:
        Validated dataclass. Check ``is_valid`` before processing further.
        If invalid, ``validation_errors`` contains human-readable messages.

    Usage in ``bot/app.py`` (task 2.2)::

        from bot.services.cards import (
            process_problem_submission,
            build_problem_confirmation_card,
            build_task_module_submit_response,
        )

        # Inside on_invoke_activity, when handling task/submit:
        submission = process_problem_submission(activity.value)
        if not submission.is_valid:
            # Re-show form with error message
            ...
        else:
            # Route through triage
            triage_text = submission.to_triage_text()
            # ... process_turn(session, triage_text) ...
            confirmation_card = build_problem_confirmation_card(submission)
            return build_task_module_submit_response(
                "Problema registrado com sucesso!"
            )
    """
    errors: list[str] = []

    category = str(data.get("category", "")).strip()
    if not category:
        errors.append("Categoria e obrigatoria.")
    elif category not in PROBLEM_CATEGORIES:
        errors.append(f"Categoria invalida: {category}")

    description = str(data.get("description", "")).strip()
    if not description:
        errors.append("Descricao e obrigatoria.")
    elif len(description) > 2000:
        description = description[:2000]

    urgency = str(data.get("urgency", "normal")).strip()
    if urgency not in URGENCY_LEVELS:
        urgency = "normal"

    steps = str(data.get("steps_to_reproduce", "")).strip()
    if len(steps) > 1500:
        steps = steps[:1500]

    contact = str(data.get("contact_info", "")).strip()
    if len(contact) > 200:
        contact = contact[:200]

    submission = ProblemSubmission(
        category=category,
        category_label=PROBLEM_CATEGORIES.get(category, category),
        description=description,
        urgency=urgency,
        urgency_label=URGENCY_LEVELS.get(urgency, urgency),
        steps_to_reproduce=steps,
        contact_info=contact,
        validation_errors=errors,
    )

    if submission.is_valid:
        logger.info(
            "problem_submission_valid",
            category=category,
            urgency=urgency,
            has_steps=bool(steps),
            has_contact=bool(contact),
        )
    else:
        logger.warning(
            "problem_submission_invalid",
            errors=errors,
        )

    return submission


# ---------------------------------------------------------------------------
# Problem Confirmation Card (shown after successful submission)
# ---------------------------------------------------------------------------


def build_problem_confirmation_card(
    submission: ProblemSubmission,
    ticket_id: str = "",
) -> dict[str, Any]:
    """Build a confirmation card displayed after a successful problem report.

    Parameters
    ----------
    submission:
        The validated ``ProblemSubmission`` dataclass.
    ticket_id:
        Optional ticket/tracking ID assigned to this report.
    """
    urgency_colors = {
        "urgente": "Attention",
        "normal": "Warning",
        "baixa": "Good",
    }
    urgency_color = urgency_colors.get(submission.urgency, "Default")

    fallback = (
        f"Problema registrado! "
        f"Categoria: {submission.category_label} | "
        f"Urgencia: {submission.urgency_label}"
    )

    facts: list[dict[str, str]] = [
        {"title": "Categoria", "value": submission.category_label},
        {"title": "Urgencia", "value": submission.urgency_label},
    ]
    if ticket_id:
        facts.insert(0, {"title": "Protocolo", "value": ticket_id})
    if submission.contact_info:
        facts.append({"title": "Contato", "value": submission.contact_info})

    body: list[dict[str, Any]] = [
        _text_block(
            "Problema Registrado",
            size="Medium",
            weight="Bolder",
            color="Good",
        ),
        _text_block(
            "Seu problema foi registrado com sucesso. "
            "Nossa equipe vai analisar e retornar o mais breve possivel.",
            spacing="Small",
        ),
        {
            "type": "FactSet",
            "spacing": "Medium",
            "facts": facts,
        },
        _text_block(
            f"Prioridade: {submission.urgency.upper()}",
            size="Small",
            weight="Bolder",
            color=urgency_color,
            spacing="Small",
        ),
        _text_block(
            submission.description[:300]
            + ("..." if len(submission.description) > 300 else ""),
            size="Small",
            isSubtle=True,
            spacing="Small",
        ),
    ]

    actions = [
        _action_submit(
            "Voltar ao menu",
            "back_to_menu",
            {},
        ),
    ]

    return _card_envelope(body, actions, fallback_text=fallback)


# ---------------------------------------------------------------------------
# Escalation notification card (sent to support team)
# ---------------------------------------------------------------------------


def build_escalation_notification_card(
    user_name: str,
    timestamp: str,
    conversation_id: str,
    urgency: str,
    error_summary: str,
    conversation_history: str,
) -> dict[str, Any]:
    """Build a rich escalation notification card sent to support team members.

    Parameters
    ----------
    user_name:
        Name of the user who needs support.
    timestamp:
        ISO timestamp of when the escalation occurred.
    conversation_id:
        Teams conversation identifier.
    urgency:
        Urgency level (urgente, normal, baixa).
    error_summary:
        Short description of the user's issue.
    conversation_history:
        Summarized conversation text.
    """
    urgency_colors = {
        "urgente": "Attention",
        "normal": "Warning",
        "baixa": "Good",
    }
    urgency_color = urgency_colors.get(urgency, "Default")

    fallback = (
        f"Nova escalacao de suporte - Usuario: {user_name} | "
        f"Urgencia: {urgency} | Resumo: {error_summary}"
    )

    body: list[dict[str, Any]] = [
        {
            "type": "ColumnSet",
            "columns": [
                {
                    "type": "Column",
                    "width": "auto",
                    "items": [
                        _text_block(
                            "Nova Escalacao",
                            size="Medium",
                            weight="Bolder",
                            color="Accent",
                        ),
                    ],
                },
                {
                    "type": "Column",
                    "width": "stretch",
                    "items": [
                        _text_block(
                            urgency.upper(),
                            size="Small",
                            weight="Bolder",
                            color=urgency_color,
                            horizontalAlignment="Right",
                        ),
                    ],
                },
            ],
        },
        {
            "type": "FactSet",
            "spacing": "Medium",
            "facts": [
                {"title": "Usuario", "value": user_name},
                {"title": "Horario", "value": timestamp},
                {"title": "Conversa", "value": conversation_id[:30]},
                {"title": "Urgencia", "value": urgency.capitalize()},
            ],
        },
        _text_block("Resumo", weight="Bolder", spacing="Medium"),
        _text_block(error_summary[:300], spacing="Small"),
        _text_block("Historico", weight="Bolder", spacing="Medium"),
        _text_block(
            conversation_history[:500],
            size="Small",
            isSubtle=True,
            spacing="Small",
        ),
    ]

    return _card_envelope(body, fallback_text=fallback)


# ---------------------------------------------------------------------------
# Classification Confirmation Card
# ---------------------------------------------------------------------------


def build_classify_card(
    message: str,
    classification_label: str = "",
    session_id: str = "",
) -> dict[str, Any]:
    fallback = f"{message} Responda Sim ou Nao."

    body: list[dict[str, Any]] = [
        _text_block(
            "Classificacao",
            size="Medium",
            weight="Bolder",
            color="Accent",
        ),
        _text_block(message, spacing="Small"),
    ]

    actions = [
        _action_submit(
            "Sim, esta correto",
            "confirm_classification",
            {"session_id": session_id, "answer": "sim", "label": classification_label},
        ),
        _action_submit(
            "Nao, classificar novamente",
            "confirm_classification",
            {"session_id": session_id, "answer": "nao"},
        ),
    ]

    return _card_envelope(body, actions, fallback_text=fallback)


# ---------------------------------------------------------------------------
# Confirm Ticket Card (Jira)
# ---------------------------------------------------------------------------


def build_confirm_ticket_card(
    error_summary: str,
    urgency: str = "normal",
    session_id: str = "",
) -> dict[str, Any]:
    urgency_colors = {
        "urgente": "Attention",
        "normal": "Warning",
        "baixa": "Good",
    }
    urgency_color = urgency_colors.get(urgency, "Default")

    fallback = (
        f"Problema detectado: {error_summary} | "
        f"Deseja abrir chamado? Responda Sim ou Nao."
    )

    body: list[dict[str, Any]] = [
        _text_block(
            "Problema detectado",
            size="Medium",
            weight="Bolder",
            color="Attention",
        ),
        _text_block(
            f"Parece que voce esta enfrentando um problema tecnico:",
            spacing="Small",
        ),
        _text_block(
            error_summary[:300],
            spacing="Small",
            isSubtle=True,
        ),
        _text_block(
            f"Urgencia: {urgency.upper()}",
            size="Small",
            weight="Bolder",
            color=urgency_color,
            spacing="Medium",
        ),
        _text_block(
            "Deseja abrir um chamado para o time de suporte?",
            weight="Bolder",
            spacing="Medium",
        ),
    ]

    actions = [
        _action_submit(
            "Sim, abrir chamado",
            "create_jira_ticket",
            {
                "session_id": session_id,
                "error_summary": error_summary,
                "urgency": urgency,
            },
        ),
        _action_submit(
            "Nao, obrigado",
            "decline_jira_ticket",
            {"session_id": session_id},
        ),
    ]

    return _card_envelope(body, actions, fallback_text=fallback)


# ---------------------------------------------------------------------------
# Ticket Created Card
# ---------------------------------------------------------------------------


def build_ticket_created_card(
    ticket_key: str,
    ticket_url: str,
    session_id: str = "",
) -> dict[str, Any]:
    fallback = f"Chamado criado: {ticket_key} - {ticket_url}"

    body: list[dict[str, Any]] = [
        _text_block(
            "Chamado Criado",
            size="Medium",
            weight="Bolder",
            color="Good",
        ),
        _text_block(
            "Seu chamado foi registrado com sucesso!",
            spacing="Small",
        ),
        {
            "type": "FactSet",
            "spacing": "Medium",
            "facts": [
                {"title": "Protocolo", "value": ticket_key},
                {"title": "Link", "value": f"[Acompanhar]({ticket_url})"},
            ],
        },
    ]

    actions = [
        _action_submit(
            "Voltar ao menu",
            "back_to_menu",
            {"session_id": session_id},
        ),
    ]

    return _card_envelope(body, actions, fallback_text=fallback)


# ---------------------------------------------------------------------------
# Task Module response helpers
# ---------------------------------------------------------------------------


def build_task_module_response(
    card: dict[str, Any],
    title: str = "Workforce Help",
    width: str = "medium",
    height: str = "medium",
) -> dict[str, Any]:
    """Wrap a card in a Task Module (task/fetch) response envelope.

    Parameters
    ----------
    card:
        The Adaptive Card dict to display in the Task Module.
    title:
        Title shown in the Task Module dialog header.
    width:
        Dialog width: ``small``, ``medium``, or ``large``.
    height:
        Dialog height: ``small``, ``medium``, or ``large``.
    """
    return {
        "task": {
            "type": "continue",
            "value": {
                "title": title,
                "width": width,
                "height": height,
                "card": card_to_attachment(card),
            },
        },
    }


def build_task_module_submit_response(message: str = "") -> dict[str, Any]:
    """Build a Task Module (task/submit) completion response.

    Parameters
    ----------
    message:
        Optional message to show after the Task Module closes.
        If empty, the Task Module simply closes.
    """
    if message:
        return {
            "task": {
                "type": "message",
                "value": message,
            },
        }
    return {"task": {"type": "message", "value": "Problema registrado com sucesso!"}}
