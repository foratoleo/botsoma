# Deep Research: Agente de Atendimento Teams Moderno

**Data de criacao:** 2026-04-08
**Ultima atualizacao:** 2026-04-08

---

## Resumo Executivo

Esta pesquisa analisa melhores praticas e tecnologias modernas para transformar o bot Botsoma de um agente de suporte basico em um sistema de atendimento inteligente e interativo no Microsoft Teams. O escopo cobre quatro areas: UX Conversacional, RAG e Qualidade, Escalacao Inteligente, e Arquitetura de Producao.

### Principais Lacunas Identificadas no Estado Atual

| Area | Estado Atual | Estado Desejado |
|------|-------------|----------------|
| **UX** | Apenas texto plano | Adaptive Cards com menus e botoes interativos |
| **RAG** | Keyword search (regex) | Hybrid search (BM25 + dense) com reranking |
| **Escalacao** | Binaria (explain/escalate) | Confidence scoring + sentiment + warm handoff |
| **Sessoes** | Dict em memoria | Redis persistido |
| **Observabilidade** | logging basico | structlog + Prometheus + OpenTelemetry |

---

## 1. UX Conversacional no Teams

### 1.1 Adaptive Cards e Menus

O Teams nao suporta `suggestedActions` nativamente. A solucao e usar **Adaptive Cards com `Action.Execute`** (padrao moderno) para criar menus clicaveis.

**Recomendacoes principais:**
- Usar `Action.Execute` (novo) em vez de `Action.Submit` (legado) para manipulacao via `on_invoke_activity`
- Limitar a 3-5 botoes por card para nao sobrecarregar o usuario
- Implementar navegacao drill-down com breadcrumb para menus complexos
- Sempre incluir `fallbackText` para clientes que nao suportam cards

**Fluxo recomendado:**
```
Saudacao → Welcome Card (4 botoes)
    → Click "Nao consigo acessar" → Explanation Card + "Ajudou? Sim/Nao"
        → Sim → Feedback Card
        → Nao → Task Module com formulario detalhado
            → Formulario → RAG busca + Card de resolucao
                → Resolvido → Feedback final
                → Nao resolvido → Card de escalacao com resumo
```

### 1.2 Task Modules

Task Modules sao modais ideais para coleta de informacoes estruturadas (formularios multi-step). Manipulados via `task/fetch` (abertura) e `task/submit` (submissao) no `on_invoke_activity`.

**Casos de uso ideais:**
- Formulario de reportar problema (categoria + descricao + urgencia)
- Feedback de atendimento
- Formulario de detalhamento quando o bot nao entendeu

### 1.3 Messaging Extensions

Permitem interacoes na area de composicao de mensagens do Teams. Configurados no `manifest.json` via `composeExtensions`.

**Uso recomendado:**
- Busca rapida de documentos da base de conhecimento
- Compartilhamento de respostas prontas direto no compose area

**Detalhes completos:** [01-teams-interactive-ux--adaptive-cards-menus.md](./01-teams-interactive-ux--adaptive-cards-menus.md) e [01-teams-interactive-ux--task-modules-deep-features.md](./01-teams-interactive-ux--task-modules-deep-features.md)

---

## 2. RAG Moderno

### 2.1 Embeddings e Vector Search

**Modelo recomendado:** `sentence-transformers/all-MiniLM-L6-v2` (384 dimensoes, 80MB, bom para PT-BR em producao).

**Vector store recomendado:** FAISS com `IndexFlatIP` (inner product com vetores normalizados = cosine similarity).

**Estrategia de chunking:** Dividir documentos .md por headings `##`, com fallback para divisao por paragrafos quando secoes excedem 500 caracteres.

**Pipeline de indexacao:**
1. Carregar todos .md do diretorio de documentacao
2. Chunking semantico por headings
3. Gerar embeddings com sentence-transformers
4. Indexar no FAISS com cosine similarity
5. Re-indexar no startup do bot

### 2.2 Retrieval Quality e Reranking

**Arquitetura recomendada: Hybrid Search + Reranking**

```
Query → BM25 (sparse) + Dense (FAISS) → RRF merge → Cross-encoder rerank → Top-K
```

| Estagio | Latencia Estimada | Ganho |
|---------|-------------------|-------|
| Dense only (baseline) | ~50ms | +30% vs keyword |
| Dense + BM25 + RRF | ~70ms | +50% vs keyword |
| + Cross-encoder reranking | ~170ms | +70% vs keyword |

**Metricas de qualidade (RAGAS):**
- `faithfulness`: resposta fiel ao contexto? (> 0.7)
- `context_precision`: chunks retornados sao relevantes?
- `context_recall`: todos chunks necessarios foram encontrados?

**Estrategia de implementacao incremental:**
1. **Fase 1:** Substituir keyword search por FAISS + embeddings (maior ganho imediato)
2. **Fase 2:** Adicionar BM25 + RRF para hybrid search
3. **Fase 3:** Adicionar cross-encoder reranking para refino final
4. **Fase 4:** Criar dataset de teste e avaliar com metricas RAGAS

**Detalhes completos:** [02-modern-rag--embeddings-vector-search.md](./02-modern-rag--embeddings-vector-search.md) e [02-modern-rag--retrieval-quality-reranking.md](./02-modern-rag--retrieval-quality-reranking.md)

---

## 3. Escalacao Inteligente

### 3.1 Confidence Scoring

Score composto por 4 metricas ponderadas:
- **Retrieval score** (35%): score do top-1 chunk retornado
- **Retrieval coverage** (20%): quantos chunks relevantes foram encontrados
- **LLM decision entropy** (25%): incerteza na decisao do LLM
- **KB relevance** (20%): relevancia geral do KB para o topico

**Thresholds de acao:**

| Score | Acao |
|-------|------|
| >= 0.80 | Auto-explain |
| 0.60 - 0.79 | Clarify (+1 pergunta) |
| 0.40 - 0.59 | Explain com caveat + oferecer escalacao |
| < 0.40 | Auto-escalate |

### 3.2 Deteccao de Sentimento

**Abordagem dual:**
- **Simples (sem modelo):** Pattern matching com lista de keywords de frustracao. Score 0-1 baseado em matches.
- **Avancada (com modelo):** `nlptown/bert-base-multilingual-uncased-sentiment` para analise de sentimento multilingual.

**Triggers de escalacao por sentimento:**
- Frustracao > 0.7 na 1a mensagem → oferecer card "Quer falar com atendente?"
- Frustracao > 0.5 + 2+ perguntas → escalar com tag "frustrado"
- "Quero falar com alguem" → escalar imediatamente
- Sentimento piorando ao longo da conversa → escalar preventivamente

### 3.3 Warm Handoff

Transferencia de contexto completo para o atendente via `EscalationContext`:
- Resumo da conversa gerado por LLM
- Historico completo
- Scores de confianca e frustracao
- Topicos discutidos e documentos tentados
- Urgencia e idioma

### 3.4 Modo Co-Piloto

Apos escalacao, o bot continua auxiliando o atendente humano com sugestoes de resposta baseadas no RAG.

**Detalhes completos:** [03-intelligent-escalation.md](./03-intelligent-escalation.md)

---

## 4. Bot Framework Avancado

### 4.1 Proactive Messaging e State Management

**Proactive messaging:** Via `adapter.continue_conversation()` com ConversationReferences persistidas em Redis (TTL 30 dias).

**State management:** Substituir o `_sessions: dict` em memoria por Redis com TTL de 7 dias. Implementar `RedisBotStorage` compativel com `ConversationState`/`UserState` do Bot Framework.

**Rate limiting:** 10 requests por minuto por conversation_id para prevenir abuso.

### 4.2 Microsoft Graph API Integration

**Bibliotecas:** `azure-identity` + `msgraph-sdk`

**Casos de uso:**
- Enriquecimento de contexto do usuario (nome, departamento, cargo)
- Busca de atendente disponivel via presenca
- Criacao de chat 1:1 entre usuario e atendente
- Escalacao para canal de equipe

**Permissoes necessarias:** User.Read.All, Team.ReadBasic.All, Channel.ReadBasic.All, Chat.ReadWrite.All, Presence.Read.All

**Detalhes completos:** [04-bot-framework-advanced--proactive-messaging-state.md](./04-bot-framework-advanced--proactive-messaging-state.md) e [04-bot-framework-advanced--graph-api-integration.md](./04-bot-framework-advanced--graph-api-integration.md)

---

## 5. Arquitetura de Producao

### Stack Tecnologica

| Componente | Tecnologia |
|-----------|-----------|
| Runtime | Python 3.12 + aiohttp |
| Session Store | Redis |
| Vector Store | FAISS (CPU) |
| Logging | structlog (JSON) |
| Metricas | prometheus-client |
| Tracing | OpenTelemetry + OTLP |
| Deploy | Docker + Azure Container Apps / AKS |

### Metricas Recomendadas

| Metrica | Tipo | Alerta |
|---------|------|--------|
| `bot_triage_decisions_total` | Counter por decisao | Taxa de escalate > 30% |
| `bot_triage_latency_seconds` | Histogram | p99 > 10s |
| `bot_active_sessions` | Gauge | > 100 simultaneas |
| `bot_llm_calls_total` | Counter por status | Error rate > 5% |
| `bot_rag_retrieval_score` | Histogram | Media < 0.3 |

### Dependencias Adicionais

```
redis==5.2.1
sentence-transformers==3.3.1
faiss-cpu==1.9.0.post1
torch==2.5.1  # CPU only
structlog==24.4.0
prometheus-client==0.21.0
opentelemetry-api==1.28.2
opentelemetry-sdk==1.28.2
opentelemetry-exporter-otlp-proto-grpc==1.28.2
azure-identity==1.19.0
msgraph-sdk==1.14.0
```

**Detalhes completos:** [05-production-architecture.md](./05-production-architecture.md)

---

## Plano de Implementacao Recomendado

### Sprint 1 - Fundacao (1-2 semanas)
1. Substituir keyword search por FAISS + embeddings
2. Implementar Redis para persistencia de sessoes
3. Adicionar logging estruturado com structlog

### Sprint 2 - UX Interativa (1-2 semanas)
4. Implementar Adaptive Cards para menu principal e respostas
5. Adicionar Task Module para formulario de problemas
6. Integrar callbacks de cards no triage flow

### Sprint 3 - Escalacao Inteligente (1-2 semanas)
7. Implementar confidence scoring
8. Adicionar deteccao de frustracao
9. Criar EscalationContext e warm handoff
10. Integrar Graph API para enriquecimento de contexto

### Sprint 4 - Qualidade e Producao (1-2 semanas)
11. Adicionar hybrid search (BM25 + RRF)
12. Implementar cross-encoder reranking
13. Adicionar metricas Prometheus + health checks
14. Setup Dockerfile atualizado + deploy

---

## Fontes e Referencias

- Microsoft Bot Framework Python SDK (v4.15.0)
- Microsoft Adaptive Cards Schema v1.5
- sentence-transformers documentation
- FAISS documentation (Facebook Research)
- RAGAS: Evaluation framework for RAG
- Microsoft Graph API v1.0
- Bot Framework Proactive Messaging patterns
- Azure Bot Service best practices
