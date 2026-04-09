# Plano de Melhorias - Botsoma Triagem Deterministica

**Data**: 2026-04-07
**Baseado em**: 15 testes com 15 agentes especialistas
**Revisao**: v2 (pos-Critic RALPLAN-DR)

---

## Requisitos

### R1 - Manter contexto da conversa (BLOQUEADOR)
Apos uma EXPLICACAO, o bot deve continuar disponivel para follow-ups no mesmo topico. Hoje `session.closed = True` (`triage_flow.py:351,365`) encerra toda conversa, e `server.py:81-84` cria sessao nova.

### R2 - Detectar idioma do usuario
Usuario em ingles (teste 6) recebeu resposta em portugues. O bot nao detecta idioma.

### R3 - Empatia nas respostas
Usuario emocional (teste 9) recebeu resposta tecnica sem acolhimento. O prompt nao instrui empatia.

### R4 - Filtrar conteudo tecnico do RAG
Respostas mencionam tabelas de BD (`llm_service.py:30-44` EXPLAIN_SYSTEM_PROMPT_TEMPLATE nao filtra docs tecnicos).

### R5 - Tratar inputs invalidos sem escalar
Gibberish (teste 7) escalou para humano. Deveria pedir esclarecimento.

### R6 - Diversificar agentes de escalacao
`server.py:28-32` tem agente unico hardcoded (Joana Martins).

### R7 - Niveis de urgencia
Todas escalacoes sao URGENTE (`triage_flow.py:364`). Deveria ter niveis.

---

## RALPLAN-DR Summary

### Principles
1. **Continuidade**: Sessao so reinicia quando usuario explicitamente pede ("Nova conversa") ou muda radicalmente de topico
2. **Empatia first**: Detectar emocao antes de triar tecnicamente
3. **Graduacao de resposta**: Nem tudo e urgente; nem tudo precisa de humano
4. **Filtragem de conteudo**: Separar docs tecnicos de docs de usuario no RAG
5. **Idioma adaptativo**: Responder no idioma do usuario

### Decision Drivers
1. Perda de contexto e o bloqueador #1 - invalida todas as outras melhorias
2. Escalacoes desnecessarias sobrecarregam o time humano
3. Falta de empatia gera experiencia negativa

### Viable Options

#### Option A: Evolucao Incremental (Recomendado)
Manter arquitetura atual, corrigir bugs e adicionar camadas.

**Pros**: Risco baixo, deploy incremental, sem refatorar
**Cons**: Divida tecnica acumula, limites da arquitetura deterministica permanecem

#### Option B: Refatoracao Multi-Agente
Separar em agentes especializados (explicador, diagnosticador, escalador).

**Pros**: Arquitetura escalavel, especializacao por agente
**Cons**: Risco alto, muito tempo, complexidade operacional

**Invalidacao de Option B**: Os problemas identificados (contexto, empatia, idioma) sao corrigiveis na arquitetura atual sem refatoracao profunda. Os 15 testes mostram que a logica de decisao (ask/explain/escalate) funciona em 87% dos casos; o problema esta nos detalhes (contexto, urgencia, idioma), nao na arquitetura. Refatorar para multi-agente introduziria novos pontos de falha (coordenacao entre agentes, roteamento, estado compartilhado) sem resolver os problemas identificados. A refaturacao multi-agente e prematura ate que os limites da arquitetura deterministica sejam atingidos na pratica.

---

## Implementation Steps

### Phase 1: BLOQUEADOR - Continuidade de Contexto

**Step 1.1**: Remover `session.closed = True` apos `explain` em `triage_flow.py:351`
- Manter closed=True apenas para `escalate` (erros reais devem sim encerrar)
- Apos explain, permitir follow-ups preservando historico

**Step 1.2**: Resetar estado de triagem apos explain
- Apos `explain`, resetar `session.questions_asked = 0` para permitir novas perguntas de triagem no follow-up
- Adicionar campo `in_follow_up: bool = False` ao Session dataclass (`triage_flow.py:51-56`)
- Setar `session.in_follow_up = True` apos explain
- No `process_turn()`, se `session.in_follow_up`, o prompt deve indicar contexto previo ao LLM

**Step 1.3**: Ajustar `server.py:81-84` - nao criar nova sessao apos explain
- Verificar se decisao anterior foi `explain` vs `escalate`
- Se explain: reabrir sessao mantendo historico (`session.closed = False`) - NAO chamar `reset_session()`
- Se escalate: manter comportamento atual (nova sessao via `reset_session()`)
- O `server.py` ja recebe `ChatResponse` com `closed: bool`, usar esse campo para decidir

**Step 1.4**: Implementar limite de turnos por sessao
- Adicionar `MAX_TURNS = 10` como constante em `triage_flow.py`
- No `process_turn()`, antes de chamar LLM: se `len(session.turns) >= MAX_TURNS`, retornar mensagem de encerramento
- Isso previne loops infinitos em follow-ups

**Step 1.5**: Ajustar frontend (`web/index.html`) - remover "Conversa finalizada" apos explain
- Texto so aparece apos escalate
- Apos explain, placeholder volta a "Digite sua mensagem..."

**Files**: `bot/services/triage_flow.py:344-358,51-56,258-276`, `web/server.py:81-84`, `web/index.html`

### Phase 2: Empatia e Detecao de Emocao

**Step 2.1**: Adicionar deteccao de sentimento no prompt do LLM
- Em `triage_flow.py:140` TRIAGE_SYSTEM_PROMPT, adicionar instrucao:
  "Se o usuario demonstra frustracao, tristeza ou ansiedade, INICIE sua resposta com validacao emocional (1 frase) antes de prosseguir."

**Step 2.2**: Adicionar campo `emotion_detected` no schema JSON de resposta
- O LLM retorna `{"emotion_detected": "frustrado", ...}` quando aplicavel
- Quando `emotion_detected` esta presente e o `decision` e `explain`, o LLM DEVE prefixar o campo `explanation` com a validacao emocional
- Exemplo: `"Entendo que voce esta frustrado. Vou te ajudar com isso. Para acessar as transcricoes..."`
- Isso garante que a empatia aparece na mensagem final do bot sem logica adicional no backend

**Files**: `bot/services/triage_flow.py:140-174`

### Phase 3: Filtro de Inputs Invalidos

**Step 3.1**: Adicionar validacao pre-triage em `triage_flow.py:process_turn`
- Antes de chamar LLM, detectar gibberish (>60% chars nao-alfabeticos, sem palavras validas com 3+ letras)
- bypass: inputs que contem padroes de erro (ex: `#ERR-`, `HTTP`, `API`, codigos alfanumericos com formato de erro) NAO devem ser filtrados
- Retornar mensagem de ajuda ao inves de escalar: "Nao entendi sua mensagem. Pode descrever com mais detalhes o que voce precisa?"

**Files**: `bot/services/triage_flow.py:258-276`

### Phase 4: Filtrar Conteudo Tecnico do RAG

**Step 4.1**: Excluir documentos tecnicos do contexto de explicacao
- Em `knowledge_base.py:_load_file()` (ou metodo equivalente), adicionar lista de exclusao:
  ```python
  EXCLUDED_DOCS = {"09-arquitetura-tecnica.md", "exemplo-documentacao.md"}
  if filepath.name in EXCLUDED_DOCS:
      return 0  # Skip file
  ```
- Filtrar no momento de carregamento (load time) para evitar consumo de memoria com docs que o usuario nunca vera
- Apenas usar docs de usuario (01-11, exceto 09)

**Files**: `bot/services/knowledge_base.py`, `bot/services/triage_flow.py:279-282`

### Phase 5: Niveis de Urgencia

**Step 5.1**: Atualizar schema JSON no prompt para suportar niveis de urgencia
- Em `triage_flow.py:155-163`, no JSON schema dentro de TRIAGE_SYSTEM_PROMPT:
  - Trocar `"urgency": "urgente"` (valor literal) por `"urgency": "urgente" | "normal" | "baixa"`
  - Adicionar instrucao: "Se o usuario esta bloqueado completamente -> urgente. Se e um bug nao-bloqueante -> normal. Se e uma duvida tecnica complexa -> baixa."

**Step 5.2**: Ajustar frontend para exibir urgencia com diferenciacao visual
- Em `web/index.html:284-298`:
  - Trocar label hardcoded `"ESCALACAO URGENTE"` por dinamico: `"ESCALACAO " + data.urgency.toUpperCase()`
  - Adicionar cores CSS por nivel: urgente=vermelho, normal=amarelo, baixa=azul
  - Manter fallback para `"urgente"` se campo vazio (compatibilidade retroativa)

**Files**: `bot/services/triage_flow.py:155-163,360-374`, `web/index.html`

### Phase 6: Pool de Agentes de Escalacao

**Step 6.1**: Transformar `SIMULATED_SUPPORT_AGENT` em lista/pool
- Em `server.py:28-32`, trocar string unica por lista de agentes:
  ```python
  SUPPORT_AGENTS = [
      {"name": "Joana Martins", "role": "Engenheira de Suporte", "specialty": "api"},
      {"name": "Carlos Silva", "role": "Analista de Suporte", "specialty": "documentos"},
      {"name": "Ana Costa", "role": "Tech Lead Suporte", "specialty": "autenticacao"},
  ]
  ```
- Usar round-robin simples (contador atomico, `agent_index = counter % len(SUPPORT_AGENTS)`) para distribuir escalacoes

**Files**: `web/server.py:28-32`

### Phase 7: Deteccao de Idioma

**Step 7.1**: Detectar idioma no inicio de `process_turn`
- Adicionar funcao `detect_language(text: str) -> str` em `triage_flow.py`:
  - Checar se >50% das palavras (3+ letras) estao em uma lista de palavras comuns em ingles
  - Retornar "en" ou "pt" (fallback para portugues)
- Se ingles: adicionar instrucao no prompt `"Responda em ingles."` ao TRIAGE_SYSTEM_PROMPT e ao EXPLAIN_SYSTEM_PROMPT_TEMPLATE
- Inputs mistos (< 50% ingles): tratar como portugues (idioma padrao do sistema)

**Files**: `bot/services/triage_flow.py:258-276,140-174`, `bot/services/llm_service.py:30-44`

---

## Acceptance Criteria

| ID | Criterio | Testavel |
|----|----------|----------|
| AC1 | Apos explain, follow-up permite novas perguntas de triagem (questions_asked reseta para 0), preservando historico da sessao | Teste: criar projeto -> adicionar membros -> configurar sprints (3 topicos seguidos) |
| AC2 | Apos escalate, nova sessao e criada (comportamento atual preservado) | Teste: reportar bug -> nova pergunta inicia fresh |
| AC3 | "Conversa finalizada" so aparece apos escalate, nao apos explain | Teste visual no browser |
| AC4 | Emocao detectada gera prefixo empatico na explicacao | Teste: "estou frustrada" + pergunta tecnica -> resposta comeca com validacao emocional |
| AC5 | Gibberish retorna pedido de esclarecimento, nao escalacao. Inputs com codigos de erro (#ERR-4029) NAO sao filtrados | Teste: "asdfghjkl" -> pedido de esclarecimento; "Erro #ERR-4029" -> triage normal |
| AC6 | Respostas nao mencionam tabelas de banco de dados | Teste: "como criar workspace" -> resposta sem "tabela 'projects'" |
| AC7 | Urgencia varia entre niveis conforme cenario | Teste: bug bloqueante="urgente", bug nao-bloqueante="normal", duvida tecnica="baixa" |
| AC8 | Agentes de escalacao rotacionam via round-robin | Teste: 2+ escalacoes vao para pessoas diferentes |
| AC9 | Pergunta em ingles gera resposta em ingles | Teste: "how do I create a project?" -> resposta em ingles |
| AC10 | Sessao encerra apos MAX_TURNS (10) follow-ups | Teste: enviar 11 mensagens seguidas -> mensagem de encerramento apos a 10a |

---

## Risks and Mitigations

| Risco | Probabilidade | Impacto | Mitigacao |
|-------|---------------|---------|-----------|
| Follow-ups geram loop infinito | Media | Alto | Limite de MAX_TURNS=10 implementado em process_turn() (Step 1.4) |
| Detecao de idioma falha | Baixa | Medio | Fallback para portugues |
| Empatia artificial soa falsa | Media | Medio | Frases curtas e naturais (1 frase de validacao), nao excessivas |
| Filtro de gibberish bloqueia mensagens validas | Baixa | Medio | Bypass para padroes de erro (#ERR-, HTTP, API) e threshold conservador (60%) |
| LLM ignora instrucao de urgencia | Media | Medio | Schema JSON explicita opcoes; fallback para "urgente" no frontend |
| LLM ignora instrucao de empatia | Media | Baixo | Validacao emocional e prefixo no campo explanation, nao campo separado |

---

## Verification Steps

1. Rodar os mesmos 15 testes originais e comparar resultados
2. Testar cenario de follow-up: criar projeto -> membros -> sprints (AC1 + AC10)
3. Verificar que "Conversa finalizada" so aparece apos escalate (AC3)
4. Enviar mensagem em ingles e verificar resposta em ingles (AC9)
5. Enviar gibberish e verificar que nao escala (AC5); enviar codigo de erro e verificar que passa (AC5)
6. Verificar que respostas nao vazam tabelas de BD (AC6)
7. Testar urgencia: bug bloqueante vs duvida tecnica vs bug nao-bloqueante (AC7)
8. Fazer 2+ escalacoes e verificar agentes diferentes (AC8)
9. Enviar 11 mensagens seguidas e verificar encerramento (AC10)

---

## ADR

**Decision**: Evolucao incremental (Option A)
**Drivers**: Perda de contexto e bloqueador critico; outras melhorias sao camadas aditivas; 87% de acerto na triagem valida a logica atual
**Alternatives considered**: Refaturacao multi-agente (Option B) - descartada porque os 15 testes mostram que a decisao ask/explain/escalate funciona; os problemas estao em detalhes (contexto, urgencia, idioma), nao na arquitetura
**Why chosen**: Todos os problemas identificados sao corrigiveis com mudancas pontuais nos arquivos existentes; refatorar introduziria novos pontos de falha
**Consequences**: Divida tecnica da arquitetura deterministica permanece, mas e aceitavel para o escopo atual; limite de escalabilidade sera atingido quando > 50 tipos de problema requererem roteamento diferente
**Follow-ups**: Apos estabilizar, avaliar evolucao para multi-agente em fase futura; monitorar metricas de satisfacao para validar decisao

---

## Improvement Changelog

**v2 - Pos-Critic RALPLAN-DR**:
- Added Step 1.2 (was Step 1.1b): Reset questions_asked=0 and add in_follow_up state to Session dataclass (Critic CRITICAL finding)
- Added Step 1.4: MAX_TURNS=10 limit to prevent infinite follow-up loops (Critic finding #8)
- Clarified Step 2.2: Emotion prefix goes into explanation field content, not separate logic (Critic finding #7)
- Clarified Step 4.1: Exact implementation with EXCLUDED_DOCS set at load time (Critic finding #3)
- Updated Step 5.1: Fix JSON schema from literal "urgente" to union type (Critic finding #5)
- Clarified Step 5.2: Specific frontend changes (dynamic label, CSS colors, fallback) (Critic finding #6)
- Clarified Step 3.1: Bypass for error code patterns (#ERR-, HTTP, API) (Critic finding #4)
- Clarified Step 6.1: Round-robin with counter (Critic finding #9)
- Clarified Step 7.1: detect_language function placement and fallback for mixed input (Critic finding #12)
- Updated AC1: Clarified that questions_asked resets while session history is preserved
- Added AC10: MAX_TURNS limit verification
- Added 3 risks to Risk table (LLM ignores urgency/empathy instructions)
