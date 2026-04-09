# Arquitetura de Producao

**Data de criacao:** 2026-04-08
**Ultima atualizacao:** 2026-04-08

---

## Arquitetura Recomendada

```
                        +-------------------+
                        |  Azure Bot        |
                        |  Service (S1)     |
                        +--------+----------+
                                 |
                                 v
                     +-----------+-----------+
                     |   Bot App (Python)    |
                     |   botbuilder-core     |
                     |   Port 3978           |
                     +-----+-------+--------+
                           |       |        |
              +------------+  +----+---+  +-+----------+
              |               | Redis  |  | Embeddings |
              v               | Store  |  | (FAISS)    |
        +-----+-----+        +--------+  +------------+
        | LLM API   |
        | (z.ai)    |
        +-----------+
```

### Componentes

| Componente | Tecnologia | Funcao |
|-----------|-----------|--------|
| Bot Runtime | Python + botbuilder-core + aiohttp | Recebe mensagens do Teams |
| Session Store | Redis | Sessoes, ConversationReferences, rate limiting |
| Embedding Store | FAISS (CPU) | Busca semantica na base de conhecimento |
| LLM | z.ai (Anthropic-compatible) | Classificacao, explicacao, resumo |
| Logging | structlog | Logs estruturados para observabilidade |
| Metrics | Prometheus | Latencia, throughput, decisoes |
| Deploy | Docker + Azure Container Apps / AKS | Infraestrutura |

## Logging Estruturado

```python
import structlog

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.BoundLogger,
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger()

# Uso no triage:
logger.info(
    "triage_decision",
    session_id=session.id,
    decision=step.decision,
    confidence=confidence.overall_confidence,
    questions_asked=session.questions_asked,
    turn_count=len(session.turns),
    source_count=len(step.sources),
)
```

## Metricas Prometheus

```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from aiohttp import web

# Metricas
TRIAGE_DECISIONS = Counter(
    "bot_triage_decisions_total",
    "Total triage decisions",
    ["decision"]  # ask, explain, escalate
)

TRIAGE_LATENCY = Histogram(
    "bot_triage_latency_seconds",
    "Time to process a triage turn",
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

ACTIVE_SESSIONS = Gauge(
    "bot_active_sessions",
    "Currently active sessions"
)

LLM_CALLS = Counter(
    "bot_llm_calls_total",
    "Total LLM API calls",
    ["status"]  # success, error, timeout
)

RAG_RETRIEVAL_SCORE = Histogram(
    "bot_rag_retrieval_score",
    "Top-1 retrieval score distribution",
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

# Middleware para instrumentacao
@TRIAGE_LATENCY.time()
async def process_turn_instrumented(session, user_message):
    step = await process_turn(session, user_message)
    TRIAGE_DECISIONS.labels(decision=step.decision).inc()
    return step

# Endpoint de metricas
async def metrics_endpoint(request):
    return web.Response(
        text=generate_latest().decode(),
        content_type="text/plain"
    )
```

## OpenTelemetry (Tracing Distribuido)

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

# Setup
provider = TracerProvider()
provider.add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint="http://otel-collector:4317"))
)
trace.set_tracer_provider(provider)

tracer = trace.get_tracer("botsoma")

# Uso
async def process_turn(session, user_message):
    with tracer.start_as_current_span("triage.process_turn") as span:
        span.set_attribute("session.id", session.id)
        span.set_attribute("user.message_length", len(user_message))

        # RAG search
        with tracer.start_as_current_span("triage.rag_search"):
            results = retriever.search(user_message)
            span.set_attribute("rag.results_count", len(results))

        # LLM call
        with tracer.start_as_current_span("triage.llm_call"):
            raw = await _call_llm(system_prompt, "Responda em JSON.")
            span.set_attribute("llm.response_length", len(raw))

        return step
```

## Dockerfile Atualizado

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Instalar dependencias do sistema para FAISS e torch CPU
RUN apt-get update && \
    apt-get install -y --no-install-recommends libgomp1 && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir \
    torch==2.5.1 --index-url https://download.pytorch.org/whl/cpu

COPY bot/ bot/
COPY docs/ docs/

# Download do modelo de embeddings no build
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

EXPOSE 3978

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:3978/health')"

CMD ["python", "-m", "bot.app"]
```

## Azure Container Apps Deployment

```yaml
# azure-containerapp.yaml
apiVersion: 2023-05-01
location: brazilsouth
properties:
  template:
    containers:
      - name: botsoma
        image: registry.azurecr.io/botsoma:latest
        env:
          - name: MICROSOFT_APP_ID
            secretRef: ms-app-id
          - name: MICROSOFT_APP_PASSWORD
            secretRef: ms-app-password
          - name: ZAI_API_KEY
            secretRef: zai-api-key
          - name: REDIS_URL
            secretRef: redis-url
        resources:
          cpu: 1.0
          memory: 2.0Gi
        probes:
          - type: liveness
            httpGet:
              path: /health
              port: 3978
    scale:
      minReplicas: 1
      maxReplicas: 3
  configuration:
    ingress:
      external: true
      targetPort: 3978
```

## Redis para Producao

### Configuracao Recomendada

```
# redis.conf (Azure Cache for Redis)
maxmemory-policy allkeys-lru
maxmemory 256mb
save ""  # Desabilitar RDB para performance (dados sao efemeros)
```

### Estrutura de Chaves

| Prefixo | TTL | Conteudo |
|---------|-----|----------|
| `session:{id}` | 7 dias | Sessao do triage flow |
| `conv_ref:{conv_id}` | 30 dias | ConversationReference |
| `bot_state:{key}` | 1 dia | Bot Framework state |
| `rate_limit:{conv_id}` | 1 minuto | Rate limiting counter |

## Dependencias Completas

```
# requirements.txt - versao final:
fastapi==0.115.6
uvicorn==0.34.0
aiohttp==3.11.11
botbuilder-core==4.15.0
python-dotenv==1.0.1
httpx==0.28.1
redis==5.2.1
sentence-transformers==3.3.1
faiss-cpu==1.9.0.post1
structlog==24.4.0
prometheus-client==0.21.0
opentelemetry-api==1.28.2
opentelemetry-sdk==1.28.2
opentelemetry-exporter-otlp-proto-grpc==1.28.2
azure-identity==1.19.0
msgraph-sdk==1.14.0
```

## Checklist de Producao

- [ ] Redis configurado e testado
- [ ] Embeddings construidos e FAISS index carregado
- [ ] Logging estruturado com structlog
- [ ] Metricas Prometheus expostas
- [ ] Health check endpoint funcional
- [ ] Rate limiting por conversa
- [ ] Graceful shutdown (fechar Redis, flush metricas)
- [ ] Variaveis de ambiente sem hardcoded values
- [ ] Docker build testado localmente
- [ ] Manifest do Teams atualizado (permissions)
- [ ] Monitoramento de latencia do LLM
- [ ] Alertas para taxa de erro > 5%
- [ ] Backup/restore da base de conhecimento
