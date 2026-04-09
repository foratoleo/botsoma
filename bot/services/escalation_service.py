import logging
import time

import httpx

from bot.config import (
    MICROSOFT_APP_ID,
    MICROSOFT_APP_PASSWORD,
    MICROSOFT_APP_TENANT_ID,
    TOKEN_EXPIRY_BUFFER_S,
)

logger = logging.getLogger(__name__)

_cached_token: str | None = None
_token_expiry: float = 0.0


async def _get_access_token() -> str:
    global _cached_token, _token_expiry

    if _cached_token and time.time() < _token_expiry:
        return _cached_token

    url = (
        f"https://login.microsoftonline.com/{MICROSOFT_APP_TENANT_ID}/oauth2/v2.0/token"
    )
    data = {
        "client_id": MICROSOFT_APP_ID,
        "client_secret": MICROSOFT_APP_PASSWORD,
        "scope": "https://api.botframework.com/.default",
        "grant_type": "client_credentials",
    }

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(url, data=data)

    if resp.status_code != 200:
        raise Exception(f"Token request failed {resp.status_code}: {resp.text[:200]}")

    body = resp.json()
    _cached_token = body["access_token"]
    _token_expiry = time.time() + (body.get("expires_in", 3600) - TOKEN_EXPIRY_BUFFER_S)

    logger.info("Access token acquired, expires in %ds", body.get("expires_in", 3600))
    return _cached_token


async def send_proactive_message(
    service_url: str,
    conversation_id: str,
    text: str,
) -> bool:
    token = await _get_access_token()

    url = f"{service_url}/v3/conversations/{conversation_id}/activities"

    payload = {
        "type": "message",
        "from": {"id": MICROSOFT_APP_ID, "name": "Suporte IA"},
        "text": text,
    }

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            url,
            json=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )

    if not resp.is_success:
        logger.error(
            "Proactive message failed %s: %s", resp.status_code, resp.text[:300]
        )
        return False

    logger.info("Proactive message sent to conversation %s", conversation_id[:20])
    return True


async def create_or_continue_conversation(
    service_url: str,
    user_id: str,
    text: str,
    tenant_id: str | None = None,
) -> bool:
    token = await _get_access_token()

    url = f"{service_url}/v3/conversations"

    payload = {
        "bot": {"id": MICROSOFT_APP_ID},
        "members": [{"id": user_id}],
        "tenantId": tenant_id or MICROSOFT_APP_TENANT_ID,
    }

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            url,
            json=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )

    if not resp.is_success:
        logger.error(
            "Create conversation failed %s: %s", resp.status_code, resp.text[:300]
        )
        return False

    body = resp.json()
    conversation_id = body.get("id")
    if not conversation_id:
        logger.error("No conversation ID in response")
        return False

    return await send_proactive_message(service_url, conversation_id, text)
