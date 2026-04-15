"""
Channel router — translates TriageStep into channel-specific message formats.

Teams: Adaptive Cards with Action.Execute buttons
WhatsApp: Kapso interactive reply buttons (max 3)
"""

from __future__ import annotations

from typing import Any

import structlog

from bot.services.triage_flow import TriageStep
from bot.adapters.whatsapp_adapter import (
    send_text,
    send_interactive_buttons,
    WhatsAppButton,
)

logger = structlog.get_logger(__name__)


def step_to_teams_card(step: TriageStep, session_id: str = "") -> dict[str, Any]:
    """Convert a TriageStep to a Teams Adaptive Card dict."""
    from bot.services.cards import (
        _card_envelope,
        _text_block,
        _action_execute,
    )

    if step.decision == "classify":
        body = [
            _text_block(
                "Classificacao", size="Medium", weight="Bolder", color="Accent"
            ),
            _text_block(step.message, spacing="Small"),
        ]
        actions = [
            _action_execute(
                "Sim, esta correto", "confirm_classification", {"answer": "sim"}
            ),
            _action_execute(
                "Nao, classificar novamente",
                "confirm_classification",
                {"answer": "nao"},
            ),
        ]
        return _card_envelope(body, actions, fallback_text=step.message)

    if step.decision == "confirm_ticket":
        body = [
            _text_block(
                "Problema detectado", size="Medium", weight="Bolder", color="Attention"
            ),
            _text_block(step.message, spacing="Small"),
        ]
        actions = [
            _action_execute(
                "Sim, abrir chamado", "create_jira_ticket", {"session_id": session_id}
            ),
            _action_execute(
                "Nao, obrigado", "decline_jira_ticket", {"session_id": session_id}
            ),
        ]
        return _card_envelope(body, actions, fallback_text=step.message)

    return {}


async def step_to_whatsapp(step: TriageStep, wa_id: str) -> bool:
    """Send a TriageStep as a WhatsApp message via Kapso."""
    if step.decision == "ask":
        return await send_text(wa_id, step.message)

    if step.decision == "explain":
        msg = step.message
        if step.sources:
            msg += f"\n\nFonte: {', '.join(step.sources)}"
        return await send_text(wa_id, msg)

    if step.decision == "classify":
        return await send_interactive_buttons(
            wa_id,
            body_text=step.message,
            header_text="Classificacao",
            buttons=[
                WhatsAppButton(id="confirm_sim", title="Sim"),
                WhatsAppButton(id="confirm_nao", title="Nao"),
            ],
        )

    if step.decision == "confirm_ticket":
        return await send_interactive_buttons(
            wa_id,
            body_text=step.message,
            header_text="Problema detectado",
            buttons=[
                WhatsAppButton(id="ticket_sim", title="Abrir chamado"),
                WhatsAppButton(id="ticket_nao", title="Nao"),
            ],
        )

    if step.decision == "escalate":
        return await send_text(wa_id, step.message)

    return await send_text(wa_id, step.message)
