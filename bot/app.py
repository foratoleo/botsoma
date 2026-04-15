import asyncio
import time
from datetime import datetime, timezone

import structlog
from botbuilder.core import (
    BotFrameworkAdapter,
    BotFrameworkAdapterSettings,
    InvokeResponse,
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
    REDIS_URL,
    SUPPORT_USER_IDS,
    KAPSO_WEBHOOK_VERIFY_TOKEN,
)
from bot.logging_config import setup_logging
from bot.services.knowledge_base import get_knowledge_base
from bot.services.redis_store import init_session_store
from bot.services.triage_flow import (
    process_turn,
    get_or_create_session,
    reset_session,
    TriageStep,
)
from bot.services.cards import (
    build_ask_card,
    build_escalation_card,
    build_escalation_notification_card,
    build_explanation_card,
    build_feedback_card,
    build_problem_form_card,
    build_task_module_response,
    build_task_module_submit_response,
    build_welcome_card,
    build_classify_card,
    build_confirm_ticket_card,
    build_ticket_created_card,
    card_to_activity,
    card_to_attachment,
)
from bot.services.escalation_service import send_proactive_message
from bot.services.metrics import (
    health_handler,
    metrics_handler,
    record_escalation,
    record_triage_decision,
    session_closed,
    session_opened,
    track_triage_latency,
)
from bot.services.rate_limiter import (
    get_rate_limiter,
    init_rate_limiter,
    RATE_LIMIT_MESSAGE,
)
from bot.adapters.channel_router import step_to_whatsapp

setup_logging()
logger = structlog.get_logger(__name__)

settings = BotFrameworkAdapterSettings(
    MICROSOFT_APP_ID,
    MICROSOFT_APP_PASSWORD,
    channel_auth_tenant=MICROSOFT_APP_TENANT_ID or None,
)
adapter = BotFrameworkAdapter(settings)


async def on_error(context: TurnContext, error: Exception):
    logger.error("bot_error", error=str(error), exc_info=True)
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
        # Action.Submit from Adaptive Cards arrives as a message with value payload.
        action_data = turn_context.activity.value
        if isinstance(action_data, dict) and "verb" in action_data:
            await self._handle_card_submit(turn_context, action_data)
            return

        user_text = (turn_context.activity.text or "").strip()
        if not user_text:
            return

        user_name = turn_context.activity.from_property.name or "Usuario"
        conversation_id = turn_context.activity.conversation.id
        activity = turn_context.activity
        service_url = activity.service_url
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        log = logger.bind(
            conversation_id=conversation_id[:20],
            user_name=user_name,
        )
        log.info("message_received", text_preview=user_text[:100])

        try:
            # Rate-limit check before any processing.
            limiter = get_rate_limiter()
            rate_result = await limiter.check(conversation_id)
            if not rate_result.allowed:
                log.warning(
                    "rate_limited",
                    current_count=rate_result.current_count,
                    limit=rate_result.limit,
                    retry_after=rate_result.retry_after_seconds,
                )
                await turn_context.send_activity(RATE_LIMIT_MESSAGE)
                return

            session = await get_or_create_session(conversation_id)

            if session.closed:
                await reset_session(conversation_id)
                session = await get_or_create_session(conversation_id)
                session_opened()
                log.info("session_created", session_id=session.id)

            async with track_triage_latency():
                t0 = time.monotonic()
                step: TriageStep = await process_turn(session, user_text)
                latency_ms = round((time.monotonic() - t0) * 1000, 1)

            record_triage_decision(step.decision, step.urgency)

            log.info(
                "triage_decision",
                session_id=session.id,
                decision=step.decision,
                reason=step.reason[:80],
                urgency=step.urgency,
                latency_ms=latency_ms,
            )

            if step.decision == "ask":
                card = build_ask_card(
                    question=step.message,
                    suggested_replies=step.suggested_actions,
                    session_id=session.id,
                )
                reply = Activity(
                    type=ActivityTypes.message,
                    attachments=[card_to_attachment(card)],
                    text=step.message,
                )
                await turn_context.send_activity(reply)

            elif step.decision == "classify":
                card = build_classify_card(
                    message=step.message,
                    classification_label=step.classification_label,
                    session_id=session.id,
                )
                reply = Activity(
                    type=ActivityTypes.message,
                    attachments=[card_to_attachment(card)],
                    text=step.message,
                )
                await turn_context.send_activity(reply)

            elif step.decision == "confirm_ticket":
                card = build_confirm_ticket_card(
                    error_summary=step.error_summary or step.message,
                    urgency=step.urgency or "normal",
                    session_id=session.id,
                )
                reply = Activity(
                    type=ActivityTypes.message,
                    attachments=[card_to_attachment(card)],
                    text=step.message,
                )
                await turn_context.send_activity(reply)

            elif step.decision == "explain":
                card = build_explanation_card(
                    explanation=step.message,
                    sources=step.sources or None,
                    session_id=session.id,
                )
                reply = Activity(
                    type=ActivityTypes.message,
                    attachments=[card_to_attachment(card)],
                    text=step.message,
                )
                await turn_context.send_activity(reply)

            elif step.decision == "escalate":
                if step.ticket_key:
                    card = build_ticket_created_card(
                        ticket_key=step.ticket_key,
                        ticket_url=step.ticket_url,
                        session_id=session.id,
                    )
                    reply = Activity(
                        type=ActivityTypes.message,
                        attachments=[card_to_attachment(card)],
                        text=f"Chamado criado: {step.ticket_key}",
                    )
                    await turn_context.send_activity(reply)
                else:
                    session_closed()
                    card = build_escalation_card(
                        error_summary=step.error_summary or step.reason,
                        urgency=step.urgency or "normal",
                        session_id=session.id,
                    )
                    reply = Activity(
                        type=ActivityTypes.message,
                        attachments=[card_to_attachment(card)],
                        text=f"Problema detectado: {step.error_summary or step.reason}",
                    )
                    await turn_context.send_activity(reply)

                await self._send_escalation_notifications(
                    turn_context,
                    user_name,
                    timestamp,
                    conversation_id,
                    step.urgency or "normal",
                    step.error_summary or step.reason,
                    session,
                    service_url,
                    log,
                )

        except Exception as exc:
            log.error("triage_error", error=str(exc), exc_info=True)
            await turn_context.send_activity(
                "Nao consegui processar sua mensagem no momento. "
                "Por favor, tente novamente ou entre em contato com o suporte."
            )

    async def on_invoke_activity(self, turn_context: TurnContext) -> InvokeResponse:
        """Handle invoke activities from Adaptive Card actions and Task Modules.

        Supported invoke types:
          - adaptiveCard/action: Action.Execute verbs from card buttons
          - task/fetch:  Opens a Task Module dialog
          - task/submit: Processes Task Module form submissions
        """
        activity = turn_context.activity
        invoke_name = activity.name or ""
        conversation_id = activity.conversation.id
        user_name = activity.from_property.name or "Usuario"
        service_url = activity.service_url
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        log = logger.bind(
            conversation_id=conversation_id[:20],
            user_name=user_name,
            invoke_name=invoke_name,
        )
        log.info("invoke_received")

        try:
            # -- adaptiveCard/action (Universal Action Model) --
            if invoke_name == "adaptiveCard/action":
                value = activity.value or {}
                action_data = value.get("action", {})
                verb = action_data.get("verb", "")
                data = action_data.get("data", {})

                log.info("card_action", verb=verb)

                return await self._handle_card_action(
                    turn_context,
                    verb,
                    data,
                    conversation_id,
                    user_name,
                    service_url,
                    timestamp,
                    log,
                )

            # -- task/fetch: Open a Task Module dialog --
            if invoke_name == "task/fetch":
                log.info("task_fetch")
                form_card = build_problem_form_card()
                response_body = build_task_module_response(
                    form_card,
                    title="Reportar Problema",
                    width="medium",
                    height="large",
                )
                return self._invoke_ok(response_body)

            # -- task/submit: Process Task Module form data --
            if invoke_name == "task/submit":
                form_data = activity.value.get("data", {}) if activity.value else {}
                log.info("task_submit", form_data=form_data)
                return await self._handle_task_submit(
                    turn_context,
                    form_data,
                    conversation_id,
                    user_name,
                    service_url,
                    timestamp,
                    log,
                )

            # Unrecognized invoke — return OK to avoid errors in Teams.
            log.warning("unrecognized_invoke", invoke_name=invoke_name)
            return self._invoke_ok()

        except Exception as exc:
            log.error("invoke_error", error=str(exc), exc_info=True)
            return self._invoke_error(str(exc))

    # -- Invoke helpers --

    @staticmethod
    def _invoke_ok(body: dict | None = None) -> InvokeResponse:
        """Return a successful (200) InvokeResponse."""
        return InvokeResponse(
            status=200,
            body=body,
        )

    @staticmethod
    def _invoke_card(card: dict) -> InvokeResponse:
        """Return an adaptiveCard/action response with a card refresh."""
        return InvokeResponse(
            status=200,
            body={
                "statusCode": 200,
                "type": "application/vnd.microsoft.card.adaptive",
                "value": card,
            },
        )

    @staticmethod
    def _invoke_error(message: str = "Internal error") -> InvokeResponse:
        """Return a 500 InvokeResponse with an error message."""
        return InvokeResponse(
            status=500,
            body={"error": message},
        )

    async def _handle_card_action(
        self,
        turn_context: TurnContext,
        verb: str,
        data: dict,
        conversation_id: str,
        user_name: str,
        service_url: str,
        timestamp: str,
        log,
    ) -> InvokeResponse:
        """Route adaptiveCard/action verbs to appropriate handlers."""
        session_id = data.get("session_id", "")

        # -- Category quick-start buttons (welcome card) --
        if verb in ("login_issue", "feature_question", "system_error"):
            category_messages = {
                "login_issue": "Estou com problema de login / acesso",
                "feature_question": "Tenho uma duvida sobre funcionalidade",
                "system_error": "Estou vendo um erro no sistema",
            }
            synthetic_message = category_messages[verb]
            session = await get_or_create_session(conversation_id)

            if session.closed:
                await reset_session(conversation_id)
                session = await get_or_create_session(conversation_id)
                session_opened()

            async with track_triage_latency():
                t0 = time.monotonic()
                step: TriageStep = await process_turn(session, synthetic_message)
                latency_ms = round((time.monotonic() - t0) * 1000, 1)

            record_triage_decision(step.decision, step.urgency)
            log.info(
                "triage_decision",
                session_id=session.id,
                decision=step.decision,
                latency_ms=latency_ms,
                source="card_action",
                verb=verb,
            )

            card = self._step_to_card(step, session.id)
            return self._invoke_card(card)

        # -- Escalate from card --
        if verb == "escalate":
            session = await get_or_create_session(conversation_id)
            session.closed = True
            from bot.services.triage_flow import save_session

            error_summary = data.get("reason", "Escalacao solicitada pelo usuario")
            session.add_bot(f"[ESCALACAO] {error_summary}")
            await save_session(session)

            session_closed()
            record_triage_decision("escalate", "normal")

            await self._send_escalation_notifications(
                turn_context,
                user_name,
                timestamp,
                conversation_id,
                "normal",
                error_summary,
                session,
                service_url,
                log,
            )

            card = build_escalation_card(
                error_summary=error_summary,
                urgency="normal",
                session_id=session.id,
            )
            return self._invoke_card(card)

        # -- Back to menu --
        if verb == "back_to_menu":
            await reset_session(conversation_id)
            card = build_welcome_card()
            return self._invoke_card(card)

        # -- Feedback buttons --
        if verb in ("feedback_yes", "feedback_no"):
            helpful = verb == "feedback_yes"
            log.info("feedback_received", helpful=helpful, session_id=session_id)
            card = build_feedback_card(helpful=helpful, session_id=session_id)
            return self._invoke_card(card)

        # -- Quick reply from ask card --
        if verb == "quick_reply":
            reply_text = data.get("reply_text", "")
            if not reply_text:
                return self._invoke_ok()

            session = await get_or_create_session(conversation_id)
            if session.closed:
                await reset_session(conversation_id)
                session = await get_or_create_session(conversation_id)
                session_opened()

            async with track_triage_latency():
                t0 = time.monotonic()
                step = await process_turn(session, reply_text)
                latency_ms = round((time.monotonic() - t0) * 1000, 1)

            record_triage_decision(step.decision, step.urgency)
            log.info(
                "triage_decision",
                session_id=session.id,
                decision=step.decision,
                latency_ms=latency_ms,
                source="quick_reply",
            )

            card = self._step_to_card(step, session.id)
            return self._invoke_card(card)

        # -- Report problem (opens task module) --
        if verb == "report_problem":
            form_card = build_problem_form_card()
            response_body = build_task_module_response(
                form_card,
                title="Reportar Problema",
                width="medium",
                height="large",
            )
            return self._invoke_ok(response_body)

        # -- Classification confirmation (classify card buttons) --
        if verb == "confirm_classification":
            answer = data.get("answer", "sim")
            session = await get_or_create_session(conversation_id)

            if session.closed:
                await reset_session(conversation_id)
                session = await get_or_create_session(conversation_id)
                session_opened()

            if answer == "sim":
                session.classification_confirmed = True
                session.pending_classification = ""
                from bot.services.triage_flow import save_session

                await save_session(session)

                last_user_text = ""
                for t in reversed(session.turns):
                    if t.get("role") == "user" and t.get("content", "").strip():
                        last_user_text = t["content"].strip()
                        break

                if last_user_text:
                    async with track_triage_latency():
                        t0 = time.monotonic()
                        step = await process_turn(session, last_user_text)
                        latency_ms = round((time.monotonic() - t0) * 1000, 1)

                    record_triage_decision(step.decision, step.urgency)
                    log.info(
                        "triage_decision",
                        session_id=session.id,
                        decision=step.decision,
                        latency_ms=latency_ms,
                        source="classification_confirmed",
                    )
                    card = self._step_to_card(step, session.id)
                    return self._invoke_card(card)
                else:
                    synthetic = data.get("label", "duvida_uso")
                    log.info("classification_confirmed_no_text", label=synthetic)
            else:
                session.classification_confirmed = False
                session.pending_classification = ""
                from bot.services.triage_flow import save_session

                await save_session(session)

            card = build_welcome_card()
            return self._invoke_card(card)

        # -- Create Jira ticket (confirm_ticket card button) --
        if verb == "create_jira_ticket":
            session = await get_or_create_session(conversation_id)
            error_summary = data.get("error_summary", "Problema reportado pelo usuario")
            urgency = data.get("urgency", "normal")

            from bot.services.jira_service import create_ticket
            from bot.services.triage_flow import save_session

            ticket = await create_ticket(
                summary=error_summary[:255],
                description=session.history_as_text()
                if hasattr(session, "history_as_text")
                else error_summary,
                urgency=urgency,
                channel="teams",
                conversation_id=conversation_id,
            )

            session.closed = True
            session.add_bot(f"[ESCALACAO] Ticket {ticket.key} criado")
            await save_session(session)

            session_closed()
            record_triage_decision("escalate", urgency)

            if ticket.success:
                card = build_ticket_created_card(
                    ticket_key=ticket.key,
                    ticket_url=ticket.url,
                    session_id=session.id,
                )
            else:
                card = build_escalation_card(
                    error_summary=f"Nao consegui criar o chamado: {ticket.error}",
                    urgency=urgency,
                    session_id=session.id,
                )
            return self._invoke_card(card)

        # -- Decline Jira ticket --
        if verb == "decline_jira_ticket":
            session = await get_or_create_session(conversation_id)
            if session.pending_classification == "awaiting_ticket_confirm":
                session.pending_classification = ""
                session.classification_confirmed = True
                from bot.services.triage_flow import save_session

                await save_session(session)

            card = build_welcome_card()
            return self._invoke_card(card)

        log.warning("unrecognized_verb", verb=verb)
        return self._invoke_ok()

    async def _handle_task_submit(
        self,
        turn_context: TurnContext,
        form_data: dict,
        conversation_id: str,
        user_name: str,
        service_url: str,
        timestamp: str,
        log,
    ) -> InvokeResponse:
        """Process a Task Module form submission through the triage flow."""
        category = form_data.get("category", "other")
        description = form_data.get("description", "")
        urgency = form_data.get("urgency", "normal")
        steps = form_data.get("steps_to_reproduce", "")

        synthetic_message = f"[{category}] {description}"
        if steps:
            synthetic_message += f"\nPassos: {steps}"

        session = await get_or_create_session(conversation_id)
        if session.closed:
            await reset_session(conversation_id)
            session = await get_or_create_session(conversation_id)
            session_opened()

        async with track_triage_latency():
            t0 = time.monotonic()
            step: TriageStep = await process_turn(session, synthetic_message)
            latency_ms = round((time.monotonic() - t0) * 1000, 1)

        record_triage_decision(step.decision, step.urgency or urgency)
        log.info(
            "triage_decision",
            session_id=session.id,
            decision=step.decision,
            latency_ms=latency_ms,
            source="task_submit",
            category=category,
            urgency=urgency,
        )

        if step.decision == "escalate":
            session_closed()
            await self._send_escalation_notifications(
                turn_context,
                user_name,
                timestamp,
                conversation_id,
                urgency,
                step.error_summary or description,
                session,
                service_url,
                log,
            )

        response_body = build_task_module_submit_response(
            "Problema registrado com sucesso! Estamos analisando seu caso."
        )
        return self._invoke_ok(response_body)

    def _step_to_card(self, step: TriageStep, session_id: str) -> dict:
        """Convert a TriageStep into the appropriate Adaptive Card dict."""
        if step.decision == "classify":
            return build_classify_card(
                message=step.message,
                classification_label=step.classification_label,
                session_id=session_id,
            )

        if step.decision == "confirm_ticket":
            return build_confirm_ticket_card(
                error_summary=step.error_summary or step.message,
                urgency=step.urgency or "normal",
                session_id=session_id,
            )

        if step.decision == "ask":
            return build_ask_card(
                question=step.message,
                suggested_replies=step.suggested_actions,
                session_id=session_id,
            )

        if step.decision == "explain":
            return build_explanation_card(
                explanation=step.message,
                sources=step.sources or None,
                session_id=session_id,
            )

        if step.decision == "escalate" and step.ticket_key:
            return build_ticket_created_card(
                ticket_key=step.ticket_key,
                ticket_url=step.ticket_url,
                session_id=session_id,
            )

        # escalate
        return build_escalation_card(
            error_summary=step.error_summary or step.message,
            urgency=step.urgency or "normal",
            session_id=session_id,
        )

    async def _handle_card_submit(
        self,
        turn_context: TurnContext,
        action_data: dict,
    ) -> None:
        """Route an Action.Submit payload through the same card-action handler.

        Reuses ``_handle_card_action`` for business logic, then extracts the
        resulting card from the InvokeResponse and sends it as a regular
        message activity (since Action.Submit doesn't support in-place refresh).
        """
        conversation_id = turn_context.activity.conversation.id
        user_name = turn_context.activity.from_property.name or "Usuario"
        service_url = turn_context.activity.service_url
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        log = logger.bind(
            conversation_id=conversation_id[:20],
            user_name=user_name,
            verb=action_data.get("verb"),
        )
        log.info("card_submit_received")

        verb = action_data.get("verb", "")
        result = await self._handle_card_action(
            turn_context,
            verb,
            action_data,
            conversation_id,
            user_name,
            service_url,
            timestamp,
            log,
        )

        if result and result.body and isinstance(result.body, dict):
            card = result.body.get("value")
            if card and isinstance(card, dict):
                await turn_context.send_activity(
                    Activity(
                        type=ActivityTypes.message,
                        attachments=[card_to_attachment(card)],
                        text=card.get("fallbackText", ""),
                    )
                )

    async def _send_escalation_notifications(
        self,
        turn_context: TurnContext,
        user_name: str,
        timestamp: str,
        conversation_id: str,
        urgency: str,
        error_summary: str,
        session,
        service_url: str,
        log,
    ) -> None:
        """Send escalation notifications to configured support users."""
        if not SUPPORT_USER_IDS:
            log.warning("no_support_users_configured")
            await turn_context.send_activity(NO_SUPPORT_CONFIGURED)
            return

        escalation_text = (
            f"Nova Escalacao de Suporte\n\n"
            f"Usuario: {user_name}\n"
            f"Horario: {timestamp}\n"
            f"Conversa: {conversation_id}\n"
            f"Urgencia: {urgency or 'normal'}\n\n"
            f"Resumo: {error_summary}\n\n"
            f"Historico:\n> {session.user_text_joined()[:500]}"
        )
        for support_user_id in SUPPORT_USER_IDS:
            try:
                sent = await send_proactive_message(
                    service_url,
                    conversation_id,
                    escalation_text,
                )
                if sent:
                    record_escalation("success")
                    log.info(
                        "escalation_sent",
                        session_id=session.id,
                        support_user_id=support_user_id[:20],
                    )
            except Exception as exc:
                record_escalation("error")
                log.error(
                    "escalation_error",
                    session_id=session.id,
                    support_user_id=support_user_id[:20],
                    error=str(exc),
                )

    async def on_members_added_activity(self, members_added, turn_context: TurnContext):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                welcome_card = build_welcome_card()
                welcome_activity = Activity(
                    type=ActivityTypes.message,
                    attachments=[card_to_attachment(welcome_card)],
                    text=WELCOME_MESSAGE,
                )
                await turn_context.send_activity(welcome_activity)


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
            ActivityTypes.invoke,
        ):
            await bot.on_turn(turn_context)

    try:
        await adapter.process_activity(activity, auth_header, call_bot)
        return web.Response(status=201)
    except Exception as exc:
        logger.error("adapter_error", error=str(exc), exc_info=True)
        return web.Response(status=500)


app = web.Application()
app.router.add_post("/api/messages", messages)
app.router.add_get("/metrics", metrics_handler)
app.router.add_get("/health", health_handler)


async def whatsapp_webhook_verify(req):
    """WhatsApp webhook verification (GET). Meta sends hub.challenge."""
    mode = req.query.get("hub.mode", "")
    token = req.query.get("hub.verify_token", "")
    challenge = req.query.get("hub.challenge", "")

    if mode == "subscribe" and token == KAPSO_WEBHOOK_VERIFY_TOKEN:
        logger.info("whatsapp_webhook_verified")
        return web.Response(text=challenge, status=200)

    logger.warning("whatsapp_webhook_verify_failed", mode=mode)
    return web.Response(status=403)


async def whatsapp_webhook_receive(req):
    """WhatsApp webhook receiver (POST). Processes incoming messages from Kapso."""
    try:
        body = await req.json()
    except Exception:
        return web.Response(status=400)

    logger.info(
        "whatsapp_webhook_received",
        body_keys=list(body.keys()) if isinstance(body, dict) else "non-dict",
    )

    try:
        entry = body.get("entry", [])
        for e in entry:
            changes = e.get("changes", [])
            for change in changes:
                value = change.get("value", {})
                messages = value.get("messages", [])
                for msg in messages:
                    await _process_whatsapp_message(msg)
    except Exception as exc:
        logger.error("whatsapp_webhook_error", error=str(exc))

    return web.Response(status=200)


async def _process_whatsapp_message(msg: dict):
    """Process a single WhatsApp inbound message through the triage flow."""
    wa_id = msg.get("from", "")
    msg_type = msg.get("type", "text")
    msg_id = msg.get("id", "")

    if not wa_id:
        return

    if msg_type == "text":
        user_text = msg.get("text", {}).get("body", "").strip()
    elif msg_type == "interactive":
        interactive = msg.get("interactive", {})
        button_reply = interactive.get("button_reply", {})
        user_text = button_reply.get("id", "") or button_reply.get("title", "")
        if not user_text:
            list_reply = interactive.get("list_reply", {})
            user_text = list_reply.get("id", "") or list_reply.get("title", "")
    elif msg_type == "button":
        user_text = msg.get("button", {}).get("text", "")
    else:
        user_text = ""

    if not user_text:
        return

    BUTTON_ID_MAP = {
        "confirm_sim": "sim",
        "confirm_nao": "nao",
        "ticket_sim": "sim",
        "ticket_nao": "nao",
    }
    user_text = BUTTON_ID_MAP.get(user_text, user_text)

    log = logger.bind(wa_id=wa_id, msg_id=msg_id)
    log.info("whatsapp_message_processing", text_preview=user_text[:80])

    session = await get_or_create_session(f"wa:{wa_id}")
    session.channel = "whatsapp"

    if session.closed:
        await reset_session(f"wa:{wa_id}")
        session = await get_or_create_session(f"wa:{wa_id}")
        session.channel = "whatsapp"

    try:
        step: TriageStep = await process_turn(session, user_text)
        log.info("whatsapp_triage_decision", decision=step.decision)
        await step_to_whatsapp(step, wa_id)
    except Exception as exc:
        log.error("whatsapp_triage_error", error=str(exc))
        from bot.adapters.whatsapp_adapter import send_text as wa_send_text

        await wa_send_text(
            wa_id, "Nao consegui processar sua mensagem. Por favor, tente novamente."
        )


app.router.add_get("/api/whatsapp/webhook", whatsapp_webhook_verify)
app.router.add_post("/api/whatsapp/webhook", whatsapp_webhook_receive)


async def on_startup(_app: web.Application) -> None:
    """Initialize async resources at server startup."""
    store = await init_session_store(redis_url=REDIS_URL or None)
    logger.info("session_store_initialized")

    # Initialize rate limiter, sharing the Redis connection when available.
    redis_client = store._redis if store.is_redis_connected else None
    init_rate_limiter(redis_client=redis_client)
    logger.info("rate_limiter_initialized")


async def on_cleanup(_app: web.Application) -> None:
    """Clean up async resources at server shutdown."""
    from bot.services.redis_store import get_session_store

    store = get_session_store()
    await store.close()


app.on_startup.append(on_startup)
app.on_cleanup.append(on_cleanup)

if __name__ == "__main__":
    kb = get_knowledge_base()
    logger.info("bot_starting", kb_sections=kb.section_count)
    logger.info("bot_ready", url=f"http://localhost:{BOT_PORT}/api/messages")
    web.run_app(app, port=BOT_PORT)
