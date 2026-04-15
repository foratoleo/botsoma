"""
Jira ticket creation service.

Creates support tickets on the configured Jira Cloud project (SCRUM) via the
jira-python REST client. Runs synchronous Jira calls in a thread executor
so the async event loop is never blocked.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import partial
from typing import Any

import structlog

from bot.config import (
    JIRA_URL,
    JIRA_EMAIL,
    JIRA_API_TOKEN,
    JIRA_PROJECT_KEY,
    JIRA_ISSUE_TYPE_NAME,
)

logger = structlog.get_logger(__name__)

_jira_client: Any = None


@dataclass
class TicketResult:
    key: str = ""
    url: str = ""
    success: bool = False
    error: str = ""


def _get_jira_client() -> Any:
    global _jira_client
    if _jira_client is not None:
        return _jira_client

    from jira import JIRA

    if not JIRA_EMAIL or not JIRA_API_TOKEN:
        raise RuntimeError("JIRA_EMAIL and JIRA_API_TOKEN must be configured")

    _jira_client = JIRA(
        server=JIRA_URL,
        basic_auth=(JIRA_EMAIL, JIRA_API_TOKEN),
        options={"server": JIRA_URL},
    )
    logger.info("jira_client_initialized", url=JIRA_URL, project=JIRA_PROJECT_KEY)
    return _jira_client


def _create_issue_sync(
    summary: str,
    description: str,
    urgency: str = "normal",
    channel: str = "unknown",
    user_name: str = "",
    conversation_id: str = "",
    classification_label: str = "",
) -> dict[str, Any]:
    """Synchronous Jira issue creation (runs in thread executor)."""
    jira = _get_jira_client()

    urgency_map = {
        "urgente": "Highest",
        "normal": "Medium",
        "baixa": "Low",
    }
    priority_name = urgency_map.get(urgency, "Medium")

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    adf_description = {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": description or "(sem descricao detalhada)",
                    }
                ],
            },
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "---"},
                ],
            },
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": f"Canal: {channel}",
                        "marks": [{"type": "strong"}],
                    },
                    {"type": "text", "text": " | "},
                    {
                        "type": "text",
                        "text": f"Usuario: {user_name or 'N/A'}",
                        "marks": [{"type": "strong"}],
                    },
                    {"type": "text", "text": " | "},
                    {
                        "type": "text",
                        "text": f"Urgencia: {urgency}",
                        "marks": [{"type": "strong"}],
                    },
                ],
            },
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": f"Classificacao bot: {classification_label or 'N/A'}",
                    },
                ],
            },
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": f"Criado em: {timestamp}"},
                ],
            },
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": f"Conversation ID: {conversation_id or 'N/A'}",
                    },
                ],
            },
        ],
    }

    fields = {
        "project": {"key": JIRA_PROJECT_KEY},
        "summary": summary[:255],
        "description": adf_description,
        "issuetype": {"name": JIRA_ISSUE_TYPE_NAME},
    }

    issue = jira.create_issue(fields=fields)

    try:
        priorities = jira.priorities()
        priority_id = next(
            (p.id for p in priorities if p.name == priority_name),
            None,
        )
        if priority_id:
            issue.update(fields={"priority": {"id": priority_id}})
    except Exception:
        logger.warning("jira_priority_set_failed", priority=priority_name)

    return {
        "key": issue.key,
        "url": issue.permalink(),
    }


async def create_ticket(
    summary: str,
    description: str,
    urgency: str = "normal",
    channel: str = "unknown",
    user_name: str = "",
    conversation_id: str = "",
    classification_label: str = "",
) -> TicketResult:
    """Create a Jira ticket without blocking the async event loop."""
    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            partial(
                _create_issue_sync,
                summary=summary,
                description=description,
                urgency=urgency,
                channel=channel,
                user_name=user_name,
                conversation_id=conversation_id,
                classification_label=classification_label,
            ),
        )
        logger.info(
            "jira_ticket_created",
            key=result["key"],
            url=result["url"],
            channel=channel,
        )
        return TicketResult(
            key=result["key"],
            url=result["url"],
            success=True,
        )
    except Exception as exc:
        logger.error("jira_ticket_failed", error=str(exc))
        return TicketResult(error=str(exc))
