"""
WhatsApp channel adapter via Kapso HTTP proxy.

Sends text messages and interactive reply buttons through the Kapso-managed
WhatsApp Business API. Does NOT use any WhatsApp SDK — pure HTTP calls to
the Kapso proxy endpoint.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx
import structlog

from bot.config import (
    KAPSO_API_BASE_URL,
    KAPSO_API_KEY,
    KAPSO_PHONE_NUMBER_ID,
    KAPSO_META_GRAPH_VERSION,
)

logger = structlog.get_logger(__name__)


@dataclass
class WhatsAppButton:
    id: str
    title: str


def _build_send_url() -> str:
    return (
        f"{KAPSO_API_BASE_URL}/meta/whatsapp/"
        f"{KAPSO_META_GRAPH_VERSION}/{KAPSO_PHONE_NUMBER_ID}/messages"
    )


def _build_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {KAPSO_API_KEY}",
        "Content-Type": "application/json",
    }


async def send_text(to: str, text: str) -> bool:
    """Send a plain text message via Kapso proxy."""
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text[:4096]},
    }
    return await _post(payload)


async def send_interactive_buttons(
    to: str,
    body_text: str,
    buttons: list[WhatsAppButton],
    header_text: str | None = None,
) -> bool:
    """Send an interactive message with up to 3 reply buttons."""
    if len(buttons) > 3:
        buttons = buttons[:3]
    if len(buttons) == 0:
        return await send_text(to, body_text)

    action = {
        "buttons": [
            {
                "type": "reply",
                "reply": {"id": btn.id, "title": btn.title[:20]},
            }
            for btn in buttons
        ]
    }

    interactive: dict[str, Any] = {
        "type": "button",
        "body": {"text": body_text[:1024]},
        "action": action,
    }
    if header_text:
        interactive["header"] = {"type": "text", "text": header_text[:60]}

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": interactive,
    }
    return await _post(payload)


async def send_interactive_list(
    to: str,
    body_text: str,
    button_title: str,
    sections: list[dict[str, Any]],
    header_text: str | None = None,
) -> bool:
    """Send an interactive list message (for >3 options)."""
    interactive: dict[str, Any] = {
        "type": "list",
        "body": {"text": body_text[:1024]},
        "action": {
            "button": button_title[:20],
            "sections": sections,
        },
    }
    if header_text:
        interactive["header"] = {"type": "text", "text": header_text[:60]}

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": interactive,
    }
    return await _post(payload)


async def _post(payload: dict[str, Any]) -> bool:
    if not KAPSO_API_BASE_URL or not KAPSO_API_KEY or not KAPSO_PHONE_NUMBER_ID:
        logger.error("kapso_not_configured")
        return False

    url = _build_send_url()
    headers = _build_headers()

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, json=payload, headers=headers)

        if not resp.is_success:
            logger.error(
                "whatsapp_send_failed",
                status=resp.status_code,
                body=resp.text[:300],
            )
            return False

        logger.info("whatsapp_message_sent", to=payload.get("to", ""))
        return True
    except Exception as exc:
        logger.error("whatsapp_send_error", error=str(exc))
        return False
