# Bot Framework Avancado - Proactive Messaging e State Management

**Data de criacao:** 2026-04-08
**Ultima atualizacao:** 2026-04-08

---

## Estado Atual vs Estado Desejado

### Atual (app.py + triage_flow.py)
- Sessoes em memoria (`_sessions: dict[str, Session]`)
- Nao sobrevive a restarts do bot
- Proactive messaging basica via escalation_service.py
- ConversationReference nao persistida

### Desejado
- Sessoes persistidas em Redis
- ConversationReference armazenada para proactive messaging
- ConversationState/UserState do Bot Framework
- Health checks e monitoramento

---

## Proactive Messaging

### Padrao continue_conversation

```python
from botbuilder.core import BotFrameworkAdapter, TurnContext
from botbuilder.schema import ConversationReference

class ProactiveMessenger:
    def __init__(self, adapter: BotFrameworkAdapter):
        self.adapter = adapter
        self._references: dict[str, ConversationReference] = {}

    async def store_reference(self, conversation_id: str, reference: ConversationReference):
        """Armazena referencia para uso futuro."""
        self._references[conversation_id] = reference

    async def send_proactive(
        self,
        conversation_id: str,
        message: str,
        card: dict | None = None
    ) -> bool:
        """Envia mensagem proativa para uma conversa existente."""
        reference = self._references.get(conversation_id)
        if not reference:
            return False

        async def _send(turn_context: TurnContext):
            if card:
                activity = Activity(
                    type=ActivityTypes.message,
                    attachments=[Attachment(
                        content_type="application/vnd.microsoft.card.adaptive",
                        content=card
                    )]
                )
                await turn_context.send_activity(activity)
            else:
                await turn_context.send_activity(message)

        try:
            await self.adapter.continue_conversation(reference, _send, self.app_id)
            return True
        except Exception as exc:
            logger.error("Proactive message failed: %s", exc)
            return False
```

### Persistencia de ConversationReference

```python
import json
import redis

class RedisReferenceStore:
    """Persiste ConversationReferences no Redis."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.client = redis.from_url(redis_url, decode_responses=True)
        self.prefix = "conv_ref:"

    async def store(self, conversation_id: str, reference: ConversationReference):
        data = reference.serialize()
        self.client.setex(
            f"{self.prefix}{conversation_id}",
            86400 * 30,  # 30 dias TTL
            json.dumps(data)
        )

    async def get(self, conversation_id: str) -> ConversationReference | None:
        raw = self.client.get(f"{self.prefix}{conversation_id}")
        if not raw:
            return None
        return ConversationReference().deserialize(json.loads(raw))
```

## State Management com Redis

### Substituindo o _sessions dict

```python
import redis
import json

class RedisSessionStore:
    """Substitui o _sessions dict por Redis."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.client = redis.from_url(redis_url, decode_responses=True)
        self.prefix = "session:"
        self.ttl = 86400 * 7  # 7 dias

    def get_or_create(self, session_id: str) -> dict:
        key = f"{self.prefix}{session_id}"
        raw = self.client.get(key)
        if raw:
            return json.loads(raw)
        return {
            "id": session_id,
            "turns": [],
            "questions_asked": 0,
            "closed": False,
            "last_bot_question": "",
            "in_follow_up": False,
        }

    def save(self, session: dict):
        key = f"{self.prefix}{session['id']}"
        self.client.setex(key, self.ttl, json.dumps(session, ensure_ascii=False))

    def delete(self, session_id: str):
        self.client.delete(f"{self.prefix}{session_id}")
```

### Integracao com Bot Framework ConversationState

```python
from botbuilder.core import ConversationState, UserState, MemoryStorage
from botbuilder.azure import CosmosDbStorage

# Para producao, usar CosmosDb ou Redis:
# storage = CosmosDbPartitionedStorage(
#     settings=CosmosDbPartitionedStorageOptions(
#         auth_key="...",
#         container_id="bot-state",
#         database_id="botsoma",
#         cosmos_db_endpoint="https://..."
#     )
# )

# Para inicio, Redis como storage customizado:
class RedisBotStorage:
    """Storage compativel com Bot Framework State."""
    def __init__(self, redis_url: str):
        self.client = redis.from_url(redis_url)
        self.prefix = "bot_state:"

    async def read(self, keys: list[str]) -> dict:
        result = {}
        for key in keys:
            raw = self.client.get(f"{self.prefix}{key}")
            if raw:
                result[key] = json.loads(raw)
        return result

    async def write(self, changes: dict):
        for key, data in changes.items():
            self.client.setex(
                f"{self.prefix}{key}",
                86400,
                json.dumps(data, ensure_ascii=False)
            )

    async def delete(self, keys: list[str]):
        for key in keys:
            self.client.delete(f"{self.prefix}{key}")
```

### Configuracao no Bot

```python
from botbuilder.core import BotFrameworkAdapter, ConversationState, UserState
from botbuilder.core.integration import aiohttp_error_middleware

def create_bot(redis_url: str | None = None):
    # Storage
    if redis_url:
        storage = RedisBotStorage(redis_url)
    else:
        storage = MemoryStorage()

    conversation_state = ConversationState(storage)
    user_state = UserState(storage)

    adapter = BotFrameworkAdapter(settings)

    # Error handler
    async def on_error(turn_context, error):
        logger.error("Unhandled error: %s", error)
        await turn_context.send_activity("Desculpe, ocorreu um erro interno.")

    adapter.on_turn_error = on_error

    bot = TriageBot(conversation_state, user_state)
    return adapter, bot
```

## Handler on_members_added Melhorado

```python
async def on_members_added_activity(self, members_added, turn_context):
    """Envia welcome com card interativa."""
    for member in members_added:
        if member.id != turn_context.activity.recipient.id:
            # Armazenar conversation reference
            reference = TurnContext.get_conversation_reference(turn_context.activity)
            await self.reference_store.store(
                turn_context.activity.conversation.id,
                reference
            )

            # Enviar welcome card
            welcome_card = self._build_welcome_card()
            await turn_context.send_activity(
                Activity(
                    type=ActivityTypes.message,
                    attachments=[welcome_card],
                    summary="Bem-vindo ao Workforce Help"
                )
            )
```

## Health Check Endpoint

```python
from aiohttp import web

async def health_check(request):
    """Endpoint para verificacao de saude do bot."""
    checks = {
        "status": "healthy",
        "redis": False,
        "knowledge_base": False,
    }

    # Verificar Redis
    try:
        if redis_client:
            redis_client.ping()
            checks["redis"] = True
    except Exception:
        checks["status"] = "degraded"

    # Verificar KB
    try:
        kb = get_knowledge_base()
        if kb.chunks:
            checks["knowledge_base"] = True
    except Exception:
        checks["status"] = "degraded"

    status_code = 200 if checks["status"] == "healthy" else 503
    return web.json_response(checks, status=status_code)
```

## Rate Limiting

```python
import time
from collections import defaultdict

class RateLimiter:
    """Rate limiting simples por conversation_id."""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, conversation_id: str) -> bool:
        now = time.time()
        requests = self._requests[conversation_id]

        # Limpar requests antigos
        requests[:] = [t for t in requests if now - t < self.window]

        if len(requests) >= self.max_requests:
            return False

        requests.append(now)
        return True
```

## Estrutura de Arquivos Recomendada

```
bot/
  app.py                    # Entry point com aiohttp
  config.py                 # Configuracoes
  services/
    triage_flow.py           # State machine (com Redis sessions)
    knowledge_base.py        # RAG com embeddings
    llm_service.py           # Chamadas LLM
    escalation_service.py    # Proactive messaging
    redis_store.py           # Redis session/reference storage
    rate_limiter.py          # Rate limiting
```

## Dependencias Adicionais

```
# requirements.txt - adicionar:
redis==5.2.1
```
