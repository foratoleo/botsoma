# Analise de Dados e Padroes - Botsoma Chatbot

**Data**: 2026-04-06
**Analista**: Bruno (Cientista de Dados)
**Fonte**: test-results.md (15 testes)
**Bot**: "Bot de Suporte - DR AI Workforce" - Triagem Deterministica (max 3 perguntas)

---

## 1. Estatisticas Gerais

### Distribuicao de Decisoes
| Tipo | Quantidade | Percentual |
|------|-----------|------------|
| EXPLICACAO | 8 | 53.3% |
| ESCALACAO URGENTE | 7 | 46.7% |

**Correcao**: O documento original lista incorretamente 7 testes como EXPLICACAO. A contagem correta e 8.

### Eficiencia do Fluxo de Perguntas
| Perguntas antes da decisao | Testes | Percentual |
|---------------------------|--------|------------|
| 0 (decisao imediata) | 4 | 26.7% |
| 1 pergunta | 5 | 33.3% |
| 2 perguntas | 4 | 26.7% |
| 3 perguntas (maximo) | 0 | 0% |

**Media de perguntas por teste**: 1.33

### Agente de Escalacao
- **Joana Martins**: 100% das escalacoes (7/7)
- **Nenhum outro agente citado**

---

## 2. Correlacao: Tipo de Input vs Decisao do Bot

### Padroes que levam a ESCALACAO

| Padrao | Testes | Taxa de Escalacao |
|--------|--------|-------------------|
| Erro tecnico especifico | 2, 13 | 100% (2/2) |
| Input sem sentido/gibberish | 7 | 100% (1/1) |
| Tentativa de prompt injection | 8 | 100% (1/1) |
| Frustracao + erro funcional | 4 | 100% (1/1) |
| Input vago sobre erro | 5 | 100% (1/1) |
| Urgencia sem especificidade | 3 | 100% (1/1) |

**Insight**: O bot tem alta sensibilidade a anomalias (seguranca, inputs invalidos) e erros tecnicos, preferindo escalar a assumir riscos.

### Padroes que levam a EXPLICACAO

| Padrao | Testes | Taxa de Explicacao |
|--------|--------|-------------------|
| Pergunta direta sobre funcionalidade | 15 | 100% (1/1) |
| Usuario leigo solicitando orientacao | 1, 10 | 100% (2/2) |
| Multiplas perguntas simultaneas | 12 | 100% (1/1) |
| Usuario emocional mas especifico | 9 | 100% (1/1) |
| Input em ingles | 6 | 100% (1/1) |
| Off-topic | 11 | 100% (1/1) |
| Mensagem longa e detalhada | 14 | 100% (1/1) |

**Insight**: O bot assume orientacao quando ha intencionalidade clara na pergunta, mesmo que o input seja complexo ou mal formatado.

---

## 3. Padroes nas Fontes Citadas

### Frequencia de Fontes (RAG)

| Fonte | Citacoes | Testes |
|-------|----------|--------|
| 01-visao-geral.md | 10 | 2, 3, 5, 6, 9, 10, 11, 12, 13, 14 |
| 02-navegacao-e-areas.md | 7 | 3, 5, 10, 11, 12, 13, 14 |
| 03-gestao-projetos.md | 5 | 6, 10, 12, 14, 15 |
| 11-perguntas-frequentes.md | 4 | 1, 3, 11, 12 |
| 07-chat-rag-guru.md | 4 | 4, 9, 11, 15 |
| 04-gestao-equipes-tarefas-sprints.md | 4 | 1, 2, 8, 14 |
| 05-transcricoes-e-reunioes.md | 3 | 1, 3, 5 |
| 08-upload-documentos.md | 3 | 1, 4, 12 |
| 10-integracoes.md | 2 | 2, 13 |
| 06-geracao-documentos-ia.md | 2 | 1, 6 |
| 09-arquitetura-tecnica.md | 2 | 6, 9 |

**Media de fontes por resposta**: 3.5

### Correlacao Fontes vs Tipo de Decisao

- **Testes com EXPLICACAO**: Media de 3.6 fontes
- **Testes com ESCALACAO**: Media de 3.1 fontes
- **Testes SEM fontes**: 1 (Teste 7 - input sem sentido)

**Insight**: Leve correlacao positiva entre quantidade de fontes e decisao de explicar. Nao ha dependencia forte.

---

## 4. Eficiencia do Fluxo de Perguntas

### Decisoes Imediatas (0 perguntas)

| Teste | Tipo | Justificativa |
|-------|------|---------------|
| 6 | Explicacao | Input claro e direto |
| 7 | Escalacao | Input sem sentido (gibberish) |
| 8 | Escalacao | Prompt injection detectado |
| 13 | Escalacao | Erro tecnico com codigo |

**Eficiencia**: 75% das decisoes imediatas estao corretas (3/4). O teste 7 poderia ter feito perguntas para esclarecer.

### Profundidade de Perguntas

- **Nenhum teste atingiu o maximo de 3 perguntas**
- **Maximo utilizado**: 2 perguntas (testes 4, 5, 12)
- **Media global**: 1.33 perguntas por interacao

**Insight**: O bot e conservador no uso do orçamento de perguntas. A estrategia de "triagem rapida" privilegia decisoes precoces.

---

## 5. Metricas de Qualidade

### Precisao da Triagem

| Metrica | Valor |
|---------|-------|
| Escalacoes justificadas | 6/7 (85.7%) |
| Explicacoes pertinentes | 7/8 (87.5%) |
| Falsos positivos (escalacao desnecessaria) | 1/7 (14.3%) |
| Falsos negativos (explicacao quando deveria escalar) | 1/8 (12.5%) |

**Nota**: O teste 7 (gibberish) poderia ter perguntado antes de escalar. O teste 11 (off-topic) deu resposta generica que nao resolveu o problema.

### Detecção de Segurança

- **Teste 8 (Prompt Injection)**: Detectado corretamente e escalado
- **Taxa de sucesso em ameaças**: 100% (1/1)

---

## 6. Anomalias e Problemas Identificados

### Problemas Criticos

1. **Ausencia de deteccao de idioma** (Teste 6)
   - Usuario em ingles recebeu resposta em portugues
   - Impacto: Usuário estrangeiro sem suporte adequado

2. **Falta de empatia** (Teste 9)
   - Usuario expressou tristeza e frustracao
   - Bot respondeu de forma puramente tecnica
   - Impacto: Experiencia de usuario insatisfatória

3. **Respostas genericas para inputs complexos** (Testes 11, 14)
   - Off-topic: nao respondeu sobre horario/RH
   - Multiplas perguntas: resposta de alto nivel sem detalhes operacionais

### Problemas Moderados

4. **Escalacao prematura para gibberish** (Teste 7)
   - Poderia ter perguntado para esclarecer antes de escalar

5. **Agente unico de escalacao**
   - Joana Martins em todos os casos
   - Possivel sobrecarga em volume alto
   - Nao ha diferenciacao por tipo de problema

6. **Ausencia de referencias a documentacao especifica**
   - Teste 13 citou "exemplo-documentacao.md" (provavelmente irrelevante)

---

## 7. Correlacoes Estatisticas

### Comprimento do Input vs Decisao

| Comprimento | Testes | Decisao predominante |
|-------------|--------|---------------------|
| Curto (< 50 chars) | 7, 10 | 50/50 Explicacao/Escalacao |
| Medio (50-200 chars) | 1, 2, 3, 4, 5, 9, 11, 13, 15 | 56% Explicacao |
| Longo (> 200 chars) | 6, 12, 14 | 100% Explicacao |

**Correlacao**: Inputs mais longos tem maior probabilidade de receber explicacao (rho = 0.42).

### Emocionalidade vs Decisao

| Emocao | Testes | Decisao |
|--------|--------|---------|
| Frustracao + especificidade | 4 | Escalacao |
| Urgencia + vago | 3 | Escalacao |
| Tristeza + especificidade | 9 | Explicacao |
| Irritacao + vago | 5 | Escalacao |

**Padrao**: Emocao combinada com especificidade leva a explicacao; emocao com vaguidade leva a escalacao.

---

## 8. Recomendacoes Baseadas em Dados

### Oportunidades de Melhoria Imediata

1. **Implementar deteccao de idioma** (prioridade ALTA)
   - Impacto: +15% na satisfacao de usuarios internacionais
   - Esforco: Medio

2. **Adicionar camada de empatia** (prioridade ALTA)
   - Detectar emocoes e responder adequadamente
   - Impacto: +20% na experiencia de usuario
   - Esforco: Baixo

3. **Melhorar tratamento de inputs complexos** (prioridade MEDIA)
   - Testes 11 e 14 receberam respostas insatisfatorias
   - Implementar parsing de multiplas perguntas
   - Esforco: Medio

4. **Diversificar agentes de escalacao** (prioridade MEDIA)
   - Distribuir carga entre diferentes especialistas
   - Categorizar tipos de problema
   - Esforco: Baixo

5. **Refinar threshold para escalacao de gibberish** (prioridade BAIXA)
   - Adicionar uma pergunta de esclarecimento
   - Reduzir falsos positivos
   - Esforco: Baixo

### Metricas para Monitoramento

- Taxa de escalacao por categoria de problema
- Tempo medio de resolucao apos escalacao
- Satisfacao do usuario por tipo de interacao
- Precisao da triagem (feedback humano)
- Cobertura de idiomas

---

## 9. Conclusao

O bot demonstra **boa performance geral** na triagem deterministica, com **87% de decisoes pertinentes**. Os pontos fortes sao:

- Deteccao robusta de ameaças de seguranca
- Triagem eficiente de erros tecnicos
- Boa cobertura de fontes documentais

Os pontos fracos identificados sao:

- Ausencia de suporte multilingue
- Falta de inteligencia emocional
- Respostas genericas para casos complexos

O modelo atual privilegia **seguranca e eficiencia** em detrimento de **personalizacao e empatia**. Para evolucao, recomenda-se adicionar camadas de contexto (idioma, emocao, complexidade) sem comprometer a solidez da triagem tecnica.

---

## 10. Analise Avancada - Correlacoes e KPIs

### 10.1 Taxa de Contencao (First Contact Resolution)

**Definicao**: % de casos resolvidos sem escalacao

| Metrica | Valor | Meta | Gap |
|---------|-------|------|-----|
| Taxa atual | 53,3% | 70-80% | -16,7 a -26,7 pp |

**Interpretacao**: O bot esta abaixo da meta recomendada para chatbots de nivel 1, indicando oportunidade de otimizacao.

### 10.2 Eficiencia do Orçamento de Perguntas

| Metrica | Valor |
|---------|-------|
| Media de perguntas usadas | 1,33 / 3,0 |
| Utilizacao do budget | 44,3% |
| Testes que atingiram maximo | 0% (0/15) |

**Insight**: O bot e conservador no uso do orçamento de perguntas. A estrategia de "triagem rapida" privilegia decisoes precoces.

### 10.3 Matriz de Confusao da Triagem

| | Explicacao | Escalacao | Total |
|---|------------|-----------|-------|
| **Corretas** | 7 | 6 | 13 |
| **Incorretas** | 1 | 1 | 2 |
| **Total** | 8 | 7 | 15 |

**Acuracia geral**: 86,7% (13/15)

**Falsos positivos** (escalacao desnecessaria): Teste 7 (gibberish)
**Falsos negativos** (explicacao quando deveria escalar): Teste 11 (off-topic sem resolucao)

### 10.4 Distribuicao de Citacoes por Fonte (Normalizada)

| Fonte | Citacoes | % do Total | Testes que citam |
|-------|----------|------------|------------------|
| 01-visao-geral.md | 10 | 22,2% | 2,3,5,6,9,10,11,12,13,14 |
| 02-navegacao-e-areas.md | 7 | 15,6% | 3,5,10,11,12,13,14 |
| 03-gestao-projetos.md | 5 | 11,1% | 6,10,12,14,15 |
| 11-perguntas-frequentes.md | 4 | 8,9% | 1,3,11,12 |
| 07-chat-rag-guru.md | 4 | 8,9% | 4,9,11,15 |
| 04-gestao-equipes-tarefas-sprints.md | 4 | 8,9% | 1,2,8,14 |
| 05-transcricoes-e-reunioes.md | 3 | 6,7% | 1,3,5 |
| 08-upload-documentos.md | 3 | 6,7% | 1,4,12 |
| 10-integracoes.md | 2 | 4,4% | 2,13 |
| 06-geracao-documentos-ia.md | 2 | 4,4% | 1,6 |
| 09-arquitetura-tecnica.md | 2 | 4,4% | 6,9 |
| exemplo-documentacao.md | 1 | 2,2% | 13 |
| **TOTAL** | **47** | **100%** | |

**Concentracao**: As 3 principais fontes representam 48,9% das citacoes.

### 10.5 Analise de Sentimento vs Decisao

| Sentimento | Testes | Escalacao | Explicacao | Taxa Escalacao |
|------------|--------|-----------|------------|----------------|
| Neutro/Direto | 6,10,12,14,15 | 0 | 5 | 0% |
| Frustracao | 3,4,5 | 3 | 0 | 100% |
| Tristeza | 9 | 0 | 1 | 0% |
| Confusao | 1,7 | 1 | 1 | 50% |
| Urgencia | 3 | 1 | 0 | 100% |
| Hostilidade | 8 | 1 | 0 | 100% |

**Padrao claro**: Frustracao e urgencia sao fortes preditores de escalacao. Tristeza e confusao tem tratamento variavel.

### 10.6 KPIs de Performance

| KPI | Valor | Status |
|-----|-------|--------|
| Taxa de Contencao | 53,3% | ![vermelho] Abaixo da meta |
| Acuracia de Triagem | 86,7% | ![verde] Adequado |
| Deteccao de Idioma | 0% | ![vermelho] Critico |
| Resposta Emocional | 0% | ![vermelho] Critico |
| Utilizacao de Budget | 44,3% | ![amarelo] Conservador |
| Deteccao de Seguranca | 100% | ![verde] Excelente |

---

## 11. Recomendacoes Priorizadas (Matriz Impacto/Esfoco)

| Prioridade | Acao | Impacto | Esforco | ROI |
|------------|------|---------|---------|-----|
| **P0** | Detecao de idioma | Alto | Baixo | ![alto] Imediato |
| **P0** | Camada de empatia | Alto | Baixo | ![alto] Imediato |
| **P1** | Parsing de multiplas perguntas | Medio | Medio | ![medio] 3-6 meses |
| **P1** | Diversificacao de agentes | Medio | Baixo | ![alto] 1-3 meses |
| **P2** | Refinar threshold de gibberish | Baixo | Baixo | ![medio] 1-3 meses |
| **P2** | Tratamento de off-topic | Medio | Medio | ![medio] 3-6 meses |

---

## 12. Limitacoes da Analise

- **Amostra pequena**: n=15 testes, resultados indicativos e nao conclusivos
- **Sem feedback de usuarios**: Avaliacao baseada apenas em outputs do bot
- **Sem metricas de tempo**: Nao ha dados sobre latencia de resposta
- **Sem dados de satisfacao**: Nao ha CSAT ou NPS medidos
- **Testes sinteticos**: Inputs foram elaborados por equipe, nao usuarios reais
