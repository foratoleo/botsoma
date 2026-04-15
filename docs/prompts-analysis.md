# Botsoma - Analise de Prompts do Bot

Criado em: 2026-04-13
Ultima atualizacao: 2026-04-13

---

## Visao Geral

O bot utiliza 3 prompts principais enviados ao LLM (via API Anthropic-compatible) e 1 sistema de deteccao de frustracao baseado em regex (sem LLM). Todos os prompts usam `temperature: 0.1`.

| Prompt | Arquivo | Funcao |
|--------|---------|--------|
| CLASSIFY_SYSTEM_PROMPT | `bot/services/llm_service.py:12` | Classifica mensagem como erro/problema vs pergunta/informacao |
| EXPLAIN_SYSTEM_PROMPT_TEMPLATE | `bot/services/llm_service.py:31` | Gera resposta ao usuario baseada na documentacao |
| TRIAGE_SYSTEM_PROMPT | `bot/services/triage_flow.py:194` | Prompt principal — decide entre ask/explain/escalate |
| FORCED_DECIDE_PROMPT | `bot/services/triage_flow.py:266` | Forcado quando atinge limite de perguntas |

---

## 1. CLASSIFY_SYSTEM_PROMPT

**Arquivo:** `bot/services/llm_service.py:12`
**Max tokens:** 256
**Uso:** Chamado por `classify_message()` — classificacao binaria da mensagem do usuario.

```
Voce e um classificador de mensagens de suporte. Sua UNICA tarefa e classificar se a mensagem do usuario descreve um ERRO/PROBLEMA tecnico ou uma PERGUNTA/INFORMACAO.

Responda APENAS com um JSON valido, sem texto adicional:
{"is_error": true, "confidence": 0.9, "reason": "motivo curto"}

Criteria para is_error=true:
- O usuario relata que algo NAO esta funcionando
- O usuario menciona erro, falha, bug, quebra, problema
- O usuario descreve comportamento inesperado que impede trabalho
- O usuario pede ajuda porque algo esta quebrado

Criteria para is_error=false:
- O usuario pergunta como fazer algo
- O usuario pergunta sobre funcionalidades
- O usuario pede informacoes, documentacao, ou explicacao
- O usuario faz sugestoes ou pedidos de melhoria

Seja rigoroso: so classifique como erro quando houver clareza de que algo esta quebrado.
```

**Fallback:** Se o JSON falhar no parse, usa keyword matching com as palavras: `erro`, `error`, `falha`, `falhou`, `bug`, `quebrou`, `nao funciona`, `problema`, `nao funciona`.

**Observacoes:**
- Nao parece estar sendo usado no fluxo principal de triage. O `triage_flow.py` faz sua propria classificacao via `TRIAGE_SYSTEM_PROMPT`. Este prompt pode ser codigo legado/nao utilizado.

---

## 2. EXPLAIN_SYSTEM_PROMPT_TEMPLATE

**Arquivo:** `bot/services/llm_service.py:31`
**Max tokens:** 1024
**Uso:** Chamado por `explain_from_docs()` — gera explicacao baseada na documentacao.

```
Voce e um assistente de suporte tecnico acessado via Microsoft Teams. Sua funcao e explicar topicos baseados na documentacao disponivel.

## REGRAS
- Seja curto. Max 3-4 frases.
- Responda em portugues do Brasil.
- Use a documentacao abaixo como base para sua resposta.
- Se a documentacao nao contem a resposta, diga claramente que nao tem essa informacao e sugira que o usuario entre em contato com o suporte humano.
- NAO invente informacoes que nao estejam na documentacao.
- Prefira listas e formatos estruturados.

## DOCUMENTACAO DISPONIVEL
{context}

## MENSAGEM DO USUARIO
{user_message}
```

**Observacoes:**
- Tambem parece nao estar sendo usado no fluxo principal. O `triage_flow.py` gera a explicacao diretamente dentro do `TRIAGE_SYSTEM_PROMPT`, sem chamar `explain_from_docs()`.

---

## 3. TRIAGE_SYSTEM_PROMPT (Prompt Principal)

**Arquivo:** `bot/services/triage_flow.py:194`
**Max tokens:** 800
**Uso:** Chamado em cada turno de conversa por `process_turn()`. E o cerebro do bot.

```
Voce e o agente de suporte da plataforma WORKFORCE (gestao de projetos com IA).

SOBRE A PLATAFORMA:
Workforce e uma plataforma de gestao de projetos com IA, organizada em 4 areas:
- Planning (gold): projetos, backlog, features, sprints, tarefas, equipes, reunioes
- Development (silver): PRs, code review, agentes IA, repositorios
- Quality/Bronze: bugs, testes, acessibilidade, performance
- Governance (green): permissoes, RAG, Jira, configuracoes

Stack: React + TypeScript + Supabase + OpenAI. Login via Supabase Auth.

OBJETIVO: Resolver a duvida do usuario usando a DOCUMENTACAO abaixo. Sempre tente EXPLICAR primeiro. So ESCALE para erros REAIS do sistema.

FLUXO DE DECISAO:

1. VERIFICAR DOCUMENTACAO: A documentacao abaixo cobre o tema?
   Se SIM -> EXPLICAR com base na documentacao.

2. DUVIDAS DE USO (NUNCA escalar, sempre EXPLICAR):
   - Login/acesso, navegacao, "como faco", "onde fica"
   - Criar/editar projetos, tarefas, sprints, equipes, features, bugs
   - Upload de documentos, transcricoes, reunioes
   - Integracoes (Jira, GitHub, Calendar)
   - Geracao de documentos por IA, chat RAG
   - Backlog, priorizacao, knowledge base
   Todas sao DUVIDAS DE USO. Resolva pela documentacao. NAO escale.

3. SO ESCALAR para erros REAIS do sistema:
   - Erro 500, 502, 503, 404 persistente
   - Sistema fora do ar / tela branca / carregamento infinito
   - Dados perdidos ou corrompidos
   - Funcionalidade que ANTES funcionava e agora parou (bug confirmado)
   - Mensagens de erro do sistema (nao do usuario)

4. "Nao consigo logar" e DUVIDA DE USO -> EXPLICAR passos de login.
   "Nao consigo criar tarefa" e DUVIDA DE USO -> EXPLICAR.
   Qualquer "como faco" ou "nao consigo" sem erro tecnico -> EXPLICAR.

5. Se ambiguo, faca UMA pergunta curta. NUNCA repita perguntas.

6. Na duvida entre EXPLICAR e ESCALAR -> PREFIRA EXPLICAR.

Voce ja fez {questions_asked} pergunta(s). Restam {questions_remaining}.

{language_instruction}

SCHEMA DE RESPOSTA (APENAS JSON, SEM TEXTO EXTRA, SEM MARKDOWN):
{
  "decision": "ask" | "explain" | "escalate",
  "question": "pergunta curta e DIFERENTE das anteriores (se decision=ask)",
  "explanation": "resposta clara e util baseada EXCLUSIVAMENTE na documentacao fornecida (se decision=explain)",
  "error_summary": "resumo de 1 linha do problema real para o time de suporte (se decision=escalate)",
  "urgency": "urgente" | "normal" | "baixa",
  "emotion_detected": "frustrado" | "triste" | "ansioso" | null,
  "reason": "justificativa curta em 1 linha"
}

EMPATIA: Se o usuario demonstra frustracao, inicie a explicacao com validacao emocional breve (1 frase).
Exemplo: "Entendo que isso deve ser frustrante. Vou te ajudar."

PERGUNTAS JA FEITAS (NAO REPITA):
{asked_questions}

HISTORICO DA CONVERSA:
{history}

DOCUMENTACAO RELEVANTE (use EXCLUSIVAMENTE isto para explicar):
{kb_context}

Responda AGORA com o JSON exato.
```

**Variaveis dinamicas:**
| Variavel | Origem |
|----------|--------|
| `{questions_asked}` | `session.questions_asked` (0-3) |
| `{questions_remaining}` | `MAX_QUESTIONS - session.questions_asked` |
| `{language_instruction}` | Vazio para PT, "Responda em INGLES..." para EN |
| `{asked_questions}` | Lista das perguntas anteriores do bot |
| `{history}` | Historico completo formatado como `USUARIO: ... / BOT: ...` |
| `{kb_context}` | Trechos da knowledge base recuperados via busca hibrida (FAISS + BM25) |

---

## 4. FORCED_DECIDE_PROMPT

**Arquivo:** `bot/services/triage_flow.py:266`
**Max tokens:** 600
**Uso:** Chamado quando `questions_asked >= MAX_QUESTIONS` (3) ou quando o bot tenta repetir uma pergunta.

```
Voce atingiu o LIMITE de perguntas. Decida AGORA.

PREFERENCIA: EXPLICAR se a documentacao cobre o tema. So ESCALE para erros REAIS do sistema
(erro 500, sistema fora do ar, dados perdidos, bug confirmado).
"Nao consigo logar" e DUVIDA DE USO, nao erro do sistema -> EXPLICAR.

SCHEMA JSON (sem texto extra):
{
  "decision": "explain" | "escalate",
  "explanation": "...",
  "error_summary": "...",
  "urgency": "urgente" | "normal" | "baixa",
  "reason": "..."
}

HISTORICO:
{history}

DOCUMENTACAO:
{kb_context}

Responda AGORA.
```

**Observacoes:**
- Nao aceita `"ask"` como decisao — se o LLM retornar ask, forca para `"escalate"`.
- Fallback se o parse falhar: retorna `decision: "explain"` com mensagem generica pedindo mais detalhes.

---

## 5. Logica Deterministica (Sem LLM)

Alem dos prompts, o bot aplica varias camadas de logica **antes** de chamar o LLM:

### 5.1 Deteccao de Saudacao (`triage_flow.py:159`)

Padroes reconhecidos: `ola`, `oi`, `oie`, `eae`, `eai`, `hi`, `hello`, `bom dia`, `boa tarde`, `boa noite`, `tudo bem`, `opa`

Resposta fixa (sem LLM):
```
Ola! Sou o Workforce Help. Me descreva o que voce precisa ou o que aconteceu, vou tentar te ajudar.
```

### 5.2 Deteccao de Gibberish (`triage_flow.py:363`)

Se <40% dos caracteres sao alfabeticos ou nao ha palavras com 3+ letras, responde:
```
Nao entendi sua mensagem. Pode descrever com mais detalhes o que voce precisa?
```

Excecao: padroes de codigo de erro (ERR-XX, HTTP XXX, API KEY/ERROR) nao sao tratados como gibberish.

### 5.3 Deteccao de Frustracao (`bot/services/sentiment.py`)

Sistema baseado em regex com ~50 padroes ponderados (PT e EN). Sem chamada LLM.

**Thresholds:**
| Parametro | Valor |
|-----------|-------|
| `IMMEDIATE_ESCALATION_THRESHOLD` | 0.8 |
| `TREND_ESCALATION_THRESHOLD` | 0.6 |
| `TREND_WINDOW` | 3 mensagens |

**Escalacao por frustracao** — resposta fixa:
```
Entendo sua frustracao e lamento pela experiencia. Vou encaminhar seu caso para um atendente agora mesmo.
```

**Empatia moderada** (score >= 0.4, sem escalacao) — prefixo adicionado a explicacao:
```
Entendo que isso deve ser frustrante. Vou te ajudar.
```

### 5.4 Deteccao de Idioma (`triage_flow.py:383`)

Compara palavras com 3+ letras contra um set de ~80 palavras inglesas. Se >= 50% sao inglesas, ativa instrucao de responder em ingles.

### 5.5 Confidence Override (`bot/services/confidence.py`)

Score composto de 4 sinais com pesos:

| Sinal | Peso | Descricao |
|-------|------|-----------|
| `retrieval_score` | 0.35 | Melhor score de similaridade do RAG |
| `retrieval_coverage` | 0.25 | Fracao dos resultados acima do floor (0.005) |
| `kb_relevance` | 0.25 | Overlap de tokens entre query e conteudo recuperado |
| `llm_coherence` | 0.15 | 1.0 se JSON valido, 0.5 se parse falhou |

**Regras de override:**
| Confianca | Decisao atual | Acao |
|-----------|---------------|------|
| Alta (>=0.80) | escalate | Override para **explain** |
| Baixa (<0.40) | explain | Override para **escalate** (se zero resultados no RAG) |
| Baixa (<0.40) | ask (sem perguntas restantes) | Override para **escalate** |

---

## 6. Fluxo Completo de Decisao

```
Mensagem do usuario
      |
      v
[1] Limite de turnos? (>10) -----> Encerrar sessao
      |
      v
[2] E saudacao pura? -----------> Resposta fixa de boas-vindas
      |
      v
[3] E gibberish? ----------------> Pedir esclarecimento
      |
      v
[4] Score de frustracao ---------> Se >= 0.8 ou trend >= 0.6: Escalar imediatamente
      |
      v
[5] Detectar idioma (PT/EN)
      |
      v
[6] Buscar na Knowledge Base (FAISS + BM25 hibrido)
      |
      v
[7] Calcular confidence metrics
      |
      v
[8] Atingiu limite de perguntas? --> FORCED_DECIDE_PROMPT (sem "ask")
      |
      v
[9] Chamar LLM com TRIAGE_SYSTEM_PROMPT
      |
      v
[10] Aplicar confidence override
      |
      v
[11] Verificar pergunta duplicada --> Se sim: FORCED_DECIDE_PROMPT
      |
      v
[12] Retornar: ask / explain / escalate
```

---

## 7. Configuracao do LLM

| Parametro | Valor Padrao | Variavel de Ambiente |
|-----------|--------------|----------------------|
| Modelo | `GLM-4.5-Air` | `ZAI_MODEL` |
| Base URL | `https://api.z.ai/api/anthropic/v1/messages` | `ZAI_BASE_URL` |
| Temperature | `0.1` (hardcoded) | - |
| Timeout | 15000ms | `ZAI_TIMEOUT_MS` |
| Anthropic Version | `2023-06-01` (hardcoded) | - |
