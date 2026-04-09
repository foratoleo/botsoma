import asyncio
import logging
from datetime import datetime, timezone

from botbuilder.core import (
    BotFrameworkAdapter,
    BotFrameworkAdapterSettings,
    TurnContext,
    ActivityHandler,
)
from botbuilder.schema import Activity, ActivityTypes
from aiohttp import web

from bot.config import (
    MICROSOFT_APP_ID,
    MICROSOFT_APP_PASSWORD,
    MICROSOFT_APP_TENANT_ID,
    BOT_PORT,
    SUPPORT_USER_IDS,
)
from bot.services.knowledge_base import get_knowledge_base
from bot.services.triage_flow import (
    process_turn,
    get_or_create_session,
    reset_session,
    TriageStep,
)
from bot.services.escalation_service import send_proactive_message

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

settings = BotFrameworkAdapterSettings(
    MICROSOFT_APP_ID,
    MICROSOFT_APP_PASSWORD,
    channel_auth_tenant=MICROSOFT_APP_TENANT_ID or None,
)
adapter = BotFrameworkAdapter(settings)


async def on_error(context: TurnContext, error: Exception):
    logger.error("Bot error: %s", error, exc_info=True)
    await context.send_activity(
        "Desculpe, ocorreu um erro ao processar sua mensagem. "
        "Se o problema persistir, entre em contato com o suporte."
    )


adapter.on_turn_error = on_error

WELCOME_MESSAGE = (
    "Ola! Sou o **Workforce Help**.\n\n"
    "Descreva o que aconteceu ou o que voce precisa. "
    "Vou tentar resolver pela documentacao ou, se for um erro, "
    "encaminhar para o time de suporte."
)

ESCALATION_USER_MESSAGE = (
    "Parece que voce esta enfrentando um problema tecnico. "
    "Vou encaminhar para o time de suporte."
)

NO_SUPPORT_CONFIGURED = (
    "Nao consegui resolver pela documentacao e parece ser um problema tecnico. "
    "Por favor, entre em contato com o suporte pelo canal de atendimento."
)


class TriageBot(ActivityHandler):
    async def on_message_activity(self, turn_context: TurnContext):
        user_text = (turn_context.activity.text or "").strip()
        if not user_text:
            return

        user_name = turn_context.activity.from_property.name or "Usuario"
        conversation_id = turn_context.activity.conversation.id
        activity = turn_context.activity
        service_url = activity.service_url
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        logger.info(
            "Message from %s (%s): %s",
            user_name,
            conversation_id[:20],
            user_text[:100],
        )

        try:
            session = get_or_create_session(conversation_id)

            if session.closed:
                reset_session(conversation_id)
                session = get_or_create_session(conversation_id)

            step: TriageStep = await process_turn(session, user_text)

            logger.info(
                "Triage: decision=%s reason=%s",
                step.decision,
                step.reason[:80],
            )

            if step.decision == "ask":
                await turn_context.send_activity(step.message)

            elif step.decision == "explain":
                reply = step.message
                if step.sources:
                    sources_line = ", ".join(step.sources)
                    reply += f"\n\n_Fonte: {sources_line}_"
                await turn_context.send_activity(reply)

            elif step.decision == "escalate":
                await turn_context.send_activity(ESCALATION_USER_MESSAGE)

                if SUPPORT_USER_IDS:
                    escalation_text = (
                        f"🔔 **Nova Escalacao de Suporte**\n\n"
                        f"**Usuario:** {user_name}\n"
                        f"**Horario:** {timestamp}\n"
                        f"**Conversa:** `{conversation_id}`\n"
                        f"**Urgencia:** {step.urgency or 'normal'}\n\n"
                        f"**Resumo:** {step.error_summary or step.reason}\n\n"
                        f"**Historico:**\n> {session.user_text_joined()[:500]}"
                    )
                    for support_user_id in SUPPORT_USER_IDS:
                        try:
                            sent = await send_proactive_message(
                                service_url,
                                conversation_id,
                                escalation_text,
                            )
                            if sent:
                                logger.info(
                                    "Escalation sent to support user %s",
                                    support_user_id[:20],
                                )
                        except Exception as exc:
                            logger.error(
                                "Escalation error for %s: %s",
                                support_user_id[:20],
                                exc,
                            )
                else:
                    logger.warning("No SUPPORT_USER_IDS configured")
                    await turn_context.send_activity(NO_SUPPORT_CONFIGURED)

        except Exception as exc:
            logger.error("Triage error: %s", exc, exc_info=True)
            await turn_context.send_activity(
                "Nao consegui processar sua mensagem no momento. "
                "Por favor, tente novamente ou entre em contato com o suporte."
            )

    async def on_members_added_activity(self, members_added, turn_context: TurnContext):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity(WELCOME_MESSAGE)


bot = TriageBot()


async def messages(req):
    if "application/json" in req.headers.get("Content-Type", ""):
        body = await req.json()
    else:
        return web.Response(status=415)

    activity = Activity().deserialize(body)
    auth_header = req.headers.get("Authorization", "")

    async def call_bot(turn_context):
        if turn_context.activity.type in (
            ActivityTypes.message,
            ActivityTypes.conversation_update,
        ):
            await bot.on_turn(turn_context)

    try:
        await adapter.process_activity(activity, auth_header, call_bot)
        return web.Response(status=201)
    except Exception as exc:
        logger.error("Adapter error: %s", exc, exc_info=True)
        return web.Response(status=500)


app = web.Application()
app.router.add_post("/api/messages", messages)

if __name__ == "__main__":
    kb = get_knowledge_base()
    logger.info("Bot starting — knowledge base: %d sections loaded", kb.section_count)
    logger.info("Bot running on http://localhost:%d/api/messages", BOT_PORT)
    web.run_app(app, port=BOT_PORT)
