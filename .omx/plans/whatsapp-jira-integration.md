# Plano: Integração WhatsApp (Kapso) + Jira + Botões Interativos

## Requirements Summary

Adicionar WhatsApp como canal do bot Botsoma usando Kapso como provedor, com:
1. **Botões interativos** na primeira interação para classificar intenção (Dúvida / Erro / Outro)
2. **LLM pré-classifica** e sugere, usuário confirma/corrige via botão
3. **Integração Jira** para abertura de chamados quando for "Erro" — funciona em **AMBOS os canais** (Teams + WhatsApp)
4. Manter funcionamento do canal Teams existente, agora com criação de tickets Jira também

### Fluxo Detalhado

```
User manda msg (texto, "oi", ou descrição do problema)
        │
        ▼
┌─────────────────────────────────┐
│  LLM classifica rapidamente     │
│  (dúvida / erro / outro / vaga) │
└─────────────────────────────────┘
        │
   ┌────┼──────────────┐
   ▼    ▼              ▼
 Mensagem     Mensagem      Vaga ("oi")
 com conteúdo  com conteúdo
   │    │              │
   ▼    ▼              ▼
 LLM sugere   LLM sugere    Bot pergunta
 classificação classificação "Como posso ajudar?"
   │           │              │
   ▼           ▼              ▼
 Botões:      Botões:       Botões:
 "É isso?"    "É isso?"    [Dúvida] [Erro] [Outro]
 [Sim-Dúvida] [Sim-Erro]    
 [É Erro]     [É Dúvida]   
 [Outro]      [Outro]      
   │           │              │
   ▼           ▼              ▼
 Confirmação  Confirmação    User clica
   │           │              │
   ▼           ▼              ▼
  ┌────┐     ┌──────────┐  ┌────────┐
  │ KB │     │Confirmar │  │ LLM    │
  │ask │     │abertura? │  │re-tria │
  └────┘     │[Abrir]   │  └────────┘
    │        │[Não]     │       │
    ▼        └────┬─────┘       ▼
  Explica      ┌───┴───┐    Reclassifica
  ao user     │       │
             ▼       ▼
          [Abrir]  [Não]
             │       │
             ▼       ▼
       Cria ticket   "Ok, se
       no Jira       precisar..."
             │
             ▼
       "Seu chamado #SCRUM-5
        foi aberto!
        Acompanhe:
        botdr.atlassian.net/..."
```

**Funciona em AMBOS os canais** — Teams (Adaptive Card com botão) e WhatsApp (interactive button message).
Quando usuário confirma "Erro" → pergunta "Quer abrir um chamado?" → confirmação → cria ticket Jira → retorna número e link.

## Acceptance Criteria

1. **AC1**: Bot recebe mensagens WhatsApp via webhook Kapso e processa via triage_flow existente
2. **AC2**: Na primeira interação, bot envia mensagem com 3 botões interativos ([Dúvida] [Erro] [Outro]) — funciona em WhatsApp E Teams
3. **AC3**: Se usuário já descreveu problema, LLM pré-classifica e pergunta "É isso mesmo?" com botão de confirmação
4. **AC4**: Se usuário clica [Erro] ou confirma erro → bot pergunta "Quer abrir um chamado?" com botões [Abrir chamado] [Não] — funciona em ambos canais
5. **AC5**: Se usuário clica [Abrir chamado] → cria ticket no Jira (projeto SCRUM, botdr.atlassian.net) → retorna número e link
6. **AC6**: Se usuário clica [Dúvida] ou confirma dúvida → fluxo de explain via KB existente
7. **AC7**: Se usuário clica [Não, obrigado] → encerra com "Se precisar, estou aqui"
8. **AC8**: Se usuário clica [Outro] → LLM tenta classificar ou pede descrição livre
9. **AC9**: Chamado Jira inclui: mensagem do usuário, classificação, histórico da conversa, urgência, canal de origem
10. **AC10**: Bot retorna número do chamado ao usuário ("Seu chamado #SCRUM-5 foi aberto! Acompanhe: botdr.atlassian.net/browse/SCRUM-5")
11. **AC11**: Canal Teams existente continua funcionando — agora com botões Adaptive Card + Jira integration
12. **AC12**: Sessões são isoladas por canal (WhatsApp phone number vs Teams user ID)
13. **AC13**: Teams: quando identifica erro, pergunta se quer abrir chamado via Adaptive Card com Action.Submit

## Implementation Steps

### Wave 1: Infraestrutura WhatsApp (paralelo com Wave 2)

#### Task 1.1: WhatsApp Adapter + Webhook Handler
**Category**: unspecified-high
**Skills**: integrate-whatsapp
**Files to create**: `bot/adapters/whatsapp_adapter.py`
**Files to modify**: `bot/app.py` (adicionar rotas webhook)

Criar adapter para comunicação com WhatsApp via Kapso proxy:
- `WhatsAppAdapter` class com métodos `send_text()`, `send_interactive_buttons()`, `send_template()`
- Todas as chamadas via HTTP para Kapso proxy (`POST /meta/whatsapp/v24.0/{phone_number_id}/messages`)
- Header `X-API-Key` com `KAPSO_API_KEY`
- Webhook verification (GET challenge) e message reception (POST)
- Parsing do payload Kapso para extrair: sender phone, message text, interactive button response
- Session ID derivation: `whatsapp:+5511999999999`

**Condição de sucesso**: `curl POST /api/whatsapp/webhook` com payload simulado retorna 200; adapter consegue enviar mensagem via Kapso proxy.

#### Task 1.2: Config para WhatsApp + Jira
**Category**: quick
**Skills**: []
**Files to modify**: `bot/config.py`

Adicionar variáveis de ambiente:
```python
# WhatsApp via Kapso
KAPSO_API_KEY: str
KAPSO_API_BASE_URL: str = "https://api.kapso.ai"
KAPSO_PHONE_NUMBER_ID: str
KAPSO_META_GRAPH_VERSION: str = "v24.0"

# Jira
JIRA_EMAIL: str
JIRA_API_TOKEN: str
JIRA_BASE_URL: str
JIRA_PROJECT_KEY: str
JIRA_COMPONENT: str = "Support"
```

**Condição de sucesso**: Config carrega sem erros, todas as vars são acessíveis.

### Wave 2: Lógica de Negócio (paralelo com Wave 1)

#### Task 2.1: Modificar TriageFlow para suportar classificação por botão
**Category**: deep
**Skills**: []
**Files to modify**: `bot/services/triage_flow.py`

Mudanças no state machine:

1. **Novo estado inicial**: `CLASSIFY` — antes de entrar no fluxo ask/explain/escalate
   - Adicionar `pending_classification` field no Session (str | None)
   - Se `pending_classification` é None → entrar modo classificação
   
2. **Nova função**: `classify_with_buttons(session, user_message)` → retorna `TriageStep` com:
   - `decision = "classify"` (novo tipo)
   - `message` = "Pelo que entendi, parece ser uma **dúvida** sobre X. É isso?"
   - `buttons` = `[("sim_duvida", "✅ Sim, é uma dúvida"), ("nao_erro", "❌ É um erro"), ("outro", "📝 Outro assunto")]`
   - Se mensagem for vaga ("oi"), buttons diretos sem sugestão

3. **Nova função**: `handle_button_response(session, button_id)` → retorna `TriageStep`:
   - Se `sim_duvida` → `decision="explain"`, entra fluxo KB
   - Se `nao_erro` → `decision="escalate"`, entra fluxo Jira
   - Se `outro` → pede descrição livre
   - Se `sim_erro` (LLM sugeriu erro e user confirmou) → fluxo Jira direto
   - Se `nao_duvida` (LLM sugeriu erro mas user diz que é dúvida) → fluxo KB

4. **Modificar `TriageStep`** (linhas 290-301):
   - Adicionar `buttons: list[dict] | None = None` (campo novo)
   - Adicionar `classification_suggestion: str | None = None`
   - Adicionar `jira_ticket_key: str | None = None`
   - Adicionar `jira_ticket_url: str | None = None`

5. **Modificar `process_turn()`** (linhas 464-701):
   - No início, verificar se é resposta de botão interativo (button_id)
   - Se sim → chamar `handle_button_response()`
   - Se não e session.pending_classification é None → chamar `classify_with_buttons()`
   - Se não e pending_classification já existe → fluxo normal atual

**Linhas afetadas**:
- 77-86: Session dataclass (adicionar fields)
- 48-49: MAX_QUESTIONS (manter)
- 290-301: TriageStep (adicionar campos)
- 464-701: process_turn (adicionar branching)
- 194-263: TRIAGE_SYSTEM_PROMPT (adicionar instrução de classificação)
- 681-701: escalation path (chamar Jira service)

**Condição de sucesso**: `process_turn()` retorna `TriageStep` com `decision="classify"` e `buttons` populados quando apropriado.

#### Task 2.2: Jira Integration Service
**Category**: unspecified-high
**Skills**: []
**Files to create**: `bot/services/jira_service.py`
**Files to modify**: `bot/config.py` (já coberto em 1.2), `requirements.txt`

Criar `JiraService`:
- `__init__`: inicializa `jira-python` client com email + API token
- `create_support_ticket(user_message, classification, history, urgency)`:
  - Cria issue no projeto configurado
  - Issue type: "Bug" se erro, "Support Request" se outro
  - Priority: mapear urgency → Jira priority
  - Description: inclui mensagem do usuário + classificação LLM + histórico da conversa
  - Labels: ["whatsapp", "bot-automation"]
  - Retorna `{"key": "PROJ-123", "url": "https://..."}`
- `create_issue_with_retry()`: retry com backoff em rate limit (429)
- Error handling: se Jira falhar, retornar erro gracefully (não bloquear o bot)
- Adicionar `jira` ao `requirements.txt`

**Condição de sucesso**: Dado um payload de teste, `JiraService.create_support_ticket()` cria issue e retorna key.

### Wave 3: Integração + Renderização (depende de Wave 1 e 2)

#### Task 3.1: Channel Router + WhatsApp Message Renderer
**Category**: unspecified-high
**Skills**: integrate-whatsapp
**Files to create**: `bot/adapters/channel_router.py`
**Files to modify**: `bot/adapters/whatsapp_adapter.py` (render methods)

Criar `ChannelRouter` que:
1. Recebe `TriageStep` do triage_flow
2. Detecta o canal (Teams ou WhatsApp)
3. Renderiza a resposta no formato do canal:

**Para WhatsApp**:
- Se `TriageStep.buttons` existe → enviar como interactive button message via Kapso
  - WhatsApp suporta até 3 reply buttons
  - Formato: `{"type": "interactive", "interactive": {"type": "button", "body": {"text": "..."}, "action": {"buttons": [...]}}}`
- Se `TriageStep.jira_ticket_key` existe → incluir no texto ("Seu chamado #PROJ-123 foi aberto: https://...")
- Se texto normal → enviar como text message

**Para Teams**:
- Manter comportamento atual (Adaptive Cards)
- Se tem buttons → renderizar como Adaptive Card com Action.Submit

**Condição de sucesso**: Mensagem com botões é enviada via WhatsApp e aparece no app com 3 opções clicáveis.

#### Task 3.2: Webhook Handler Completo
**Category**: unspecified-high
**Skills**: integrate-whatsapp
**Files to modify**: `bot/app.py`

Adicionar ao servidor aiohttp existente:
- `GET /api/whatsapp/webhook` → Meta verification challenge
- `POST /api/whatsapp/webhook` → receber mensagens WhatsApp via Kapso
  - Validar webhook signature
  - Extrair: sender, message text, interactive response (button_id)
  - Obter/criar sessão (Redis, prefixo "whatsapp:")
  - Chamar `process_turn()` ou `handle_button_response()` conforme tipo
  - Passar resultado para ChannelRouter → WhatsAppAdapter → enviar resposta

**Condição de sucesso**: Fluxo completo funciona: user manda msg → webhook recebe → triage processa → resposta com botões chega no WhatsApp.

### Wave 4: Testes + Verificação

#### Task 4.1: Testes Manuais End-to-End
**Category**: unspecified-low
**Skills**: []

Cenários de teste:
1. User manda "oi" → bot responde com botões [Dúvida] [Erro] [Outro]
2. User clica [Dúvida] → bot entra modo de pergunta sobre a dúvida
3. User descreve erro completo → LLM sugere "É um erro?" → botões [Sim] [Não, é dúvida] [Outro]
4. User confirma [Sim, é erro] → bot abre chamado Jira → retorna número
5. User clica [Outro] → bot pede descrição livre
6. Sessão WhatsApp não interfere com sessão Teams
7. Jira falha → bot não crasha, informa user que vai registrar

## Risks and Mitigations

| Risco | Impacto | Mitigação |
|---|---|---|
| Templates WhatsApp não aprovados a tempo | Bloqueia notificações fora de 24h | No MVP, operar só dentro da janela de 24h; usar mensagem genérica aprovada |
| SDK Kapso é Node.js, Botsoma é Python | Não usar SDK, usar HTTP direto | Chamar Kapso proxy via aiohttp/httpx |
| Jira API token expira | Chamados param de ser criados | Monitorar, alertar, fallback graceful |
| Rate limit Jira (100 req/s) | Improvável para volume de suporte | Retry com backoff implementado |
| WhatsApp 24h window | Bot não consegue responder depois | Trackear timestamp, usar template se necessário |
| Adicionar campo `buttons` ao TriageStep quebra Teams | Teams não usa esse campo | `buttons = None` por default, Teams ignora |

## Verification Steps

1. **Unit**: `JiraService.create_support_ticket()` com mock → retorna key
2. **Unit**: `WhatsAppAdapter.send_interactive_buttons()` com mock HTTP → payload correto
3. **Integration**: `process_turn()` com primeira mensagem → retorna `decision="classify"` com buttons
4. **Integration**: Webhook POST com payload WhatsApp → resposta enviada
5. **E2E**: Mensagem real no WhatsApp → bot responde com botões → clicar botão → fluxo continua
6. **Regression**: Teams bot funciona normalmente após mudanças

## Estimated Effort

| Wave | Tasks | Tempo Estimado |
|---|---|---|
| Wave 1 (Infra) | 1.1, 1.2 | 2-3 dias |
| Wave 2 (Lógica) | 2.1, 2.2 | 3-4 dias |
| Wave 3 (Integração) | 3.1, 3.2 | 2-3 dias |
| Wave 4 (Testes) | 4.1 | 1-2 dias |
| **Total** | | **8-12 dias** |

## Prerequisites (antes de implementar)

- [ ] Kapso CLI instalado e autenticado (`kapso login`)
- [ ] Número WhatsApp Business conectado (`kapso setup`)
- [ ] Webhook URL configurado (ngrok ou domínio)
- [ ] Jira Cloud account + API token gerado
- [ ] Projeto Jira criado com key configurada
- [ ] `jira` adicionado ao requirements.txt
