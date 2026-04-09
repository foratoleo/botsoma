# Integrações

## Visão Geral

O DR AI Workforce integra-se com diversos serviços externos para prover funcionalidades de IA, armazenamento, autenticação, comunicação e gerenciamento. Este documento detalha cada integração.

---

## 1. Supabase

### O que é:
Backend as a Service que provê banco de dados, autenticação, armazenamento de arquivos e funções serverless.

### Componentes Utilizados:

| Componente | Uso no Sistema |
|---|---|
| **PostgreSQL** | Banco de dados principal — 29 tabelas, 22 views |
| **Supabase Auth** | Autenticação de usuários (JWT, sessões) |
| **Supabase Storage** | Armazenamento de arquivos (S3-compatible) |
| **Edge Functions** | Funções serverless em Deno (geração de docs) |
| **Realtime** | Subscriptions para atualizações em tempo real |
| **pgvector** | Extensão para busca vetorial/semântica |

### Configuração:
```env
VITE_SUPABASE_URL=https://xxxxx.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

### Segurança:
- **Row Level Security (RLS)**: Políticas por projeto
- **JWT**: Tokens de autenticação em todas as requisições
- **API Keys**: Chaves gerenciadas via Supabase Secrets

---

## 2. OpenAI

### O que é:
API de Inteligência Artificial para geração de texto e embeddings.

### Modelos Utilizados:

| Modelo | Uso |
|---|---|
| **GPT-4o** | Geração de documentos complexos (PRDs, Specs) |
| **GPT-4o-mini** | Tarefas mais simples (resumos, análises rápidas) |
| **Text Embedding** | Geração de embeddings para busca semântica (Guru) |

### APIs Utilizadas:

| API | Função |
|---|---|
| **Chat Completions** | Geração de conteúdo textual |
| **Responses API** | Conversação contínua (múltiplos documentos) |
| **Embeddings** | Conversão de texto em vetores para busca |

### Integração:
- Chamadas feitas via **Edge Functions** (chaves seguras no servidor)
- **Responses API** mantém contexto entre gerações → 71-75% redução de tokens
- Seleção automática de modelo baseada em complexidade

### Custos:
- Rastreamento automático via tabela `ai_interactions`
- Tokens de entrada e saída registrados
- Custo estimado por interação
- Dashboard de métricas de uso

---

## 3. Microsoft Calendar

### O que é:
Integração com o calendário Microsoft para capturar reuniões agendadas.

### Funcionalidades:
- Sincronização automática de reuniões
- Captura de título, participantes, data e duração
- Integração com Recall.ai para gravação automática

### Fluxo:
```
Microsoft Calendar
       │
       ▼
Sincronização de reuniões
       │
       ▼
Recall.ai inicia gravação
       │
       ▼
Transcrição automática
       │
       ▼
Conteúdo disponível na plataforma
```

---

## 4. Recall.ai

### O que é:
Serviço de gravação e transcrição automatizada de reuniões online.

### Funcionalidades:
- Gravação automática de videoconferências
- Transcrição com identificação de falantes
- Integração com principais plataformas (Zoom, Teams, Meet)
- Processamento em tempo real ou pós-reunião

### Uso no Sistema:
1. Reunião detectada via Microsoft Calendar
2. Recall.ai inicia gravação automaticamente
3. Transcrição gerada ao fim da reunião
4. Texto é importado para a plataforma
5. Disponível para geração de documentos e Guru

---

## 5. Jira (Planejado)

### Status: Integração futura

### Funcionalidades planejadas:
- Sincronização bidirecional de tarefas
- Importação de issues e épics
- Exportação de sprints e stories
- Mapeamento de status entre plataformas

---

## 6. GitHub (Planejado)

### Status: Integração futura

### Funcionalidades planejadas:
- Vincular tarefas a PRs e commits
- Importar issues como tarefas
- Dashboard de atividade de código
- Métricas de contribuição

---

## Diagrama de Integrações

```
                    ┌─────────────────┐
                    │   DR AI Workforce│
                    │   (Frontend)    │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
     ┌──────────────┐ ┌───────────┐ ┌───────────┐
     │   SUPABASE   │ │  OPENAI   │ │ MICROSOFT │
     │              │ │           │ │ CALENDAR  │
     │ • PostgreSQL │ │ • GPT-4o  │ │           │
     │ • Auth       │ │ • Embeds  │ │ Reuniões  │
     │ • Storage    │ │ • Resp.API│ │           │
     │ • Edge Func. │ │           │ └─────┬─────┘
     │ • pgvector   │ │           │       │
     └──────────────┘ └───────────┘       ▼
                                       ┌───────────┐
                                       │ RECALL.AI │
                                       │           │
                                       │ Gravação  │
                                       │ Transcrição│
                                       └───────────┘

     ┌──────────────┐  ┌──────────────┐
     │    JIRA      │  │   GITHUB     │
     │ (Futuro)     │  │ (Futuro)     │
     └──────────────┘  └──────────────┘
```

---

## Configuração de Integrações

### Variáveis de Ambiente:

```env
# Supabase (Obrigatório)
VITE_SUPABASE_URL=https://xxxxx.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key

# OpenAI (Opcional — pode ser via Supabase Secrets)
VITE_OPENAI_API_KEY=sk-your-openai-key

# Microsoft Calendar (Configurado no Supabase)
# Recall.ai (Configurado no Supabase)
```

### Edge Function Secrets:
As chaves sensíveis são configuradas via Supabase Secrets, não no código:
```bash
supabase secrets set OPENAI_API_KEY=sk-...
```

---

## Tratamento de Erros por Integração

| Integração | Erro Comum | Ação |
|---|---|---|
| Supabase | Auth expirada | Redirecionar para login |
| Supabase | RLS bloqueou acesso | Verificar permissões do projeto |
| OpenAI | Rate limit | Aguardar e tentar novamente |
| OpenAI | API key inválida | Contatar admin |
| Recall.ai | Falha na gravação | Upload manual da transcrição |
| Calendar | Token expirado | Reconectar conta Microsoft |
