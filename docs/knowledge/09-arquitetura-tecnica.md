# Arquitetura Técnica

## Visão Geral

O DR AI Workforce é uma aplicação web moderna com arquitetura baseada em **frontend React** + **backend Supabase** + **Edge Functions serverless**. A separação de responsabilidades é clara: o frontend gerencia a interface e o estado, o Supabase provê dados e autenticação, e as Edge Functions lidam com integrações de IA.

---

## Stack Completo

```
┌─────────────────────────────────────────────────┐
│                    FRONTEND                      │
│                                                  │
│  React 18 + TypeScript + Vite                   │
│  Tailwind CSS + Shadcn/ui + Radix UI            │
│  TanStack Query v5 (server state)               │
│  React Router DOM v6 (routing)                  │
│  Framer Motion (animações)                      │
│  React Hook Form + Zod (formulários)            │
│  Recharts (gráficos)                            │
│  Sonner (toasts)                                │
└───────────────────────┬─────────────────────────┘
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
┌──────────────┐ ┌───────────┐ ┌──────────────┐
│   SUPABASE   │ │  OPENAI   │ │    S3        │
│              │ │    API    │ │ (Storage)    │
│ PostgreSQL   │ │           │ │              │
│ Auth         │ │ GPT-4o    │ │ Arquivos     │
│ Edge Funct.  │ │ GPT-4o-   │ │ binários     │
│ Realtime     │ │   mini    │ │              │
│ pgvector     │ │ Embeddings│ │              │
└──────────────┘ └───────────┘ └──────────────┘
```

---

## Frontend — Gerenciamento de Estado

### Estratégia em Camadas:

| Camada | Tecnologia | Uso |
|---|---|---|
| **Server State** | TanStack Query v5 | Dados do Supabase (projetos, tarefas, documentos) |
| **Auth State** | AuthContext | Sessão do usuário (Supabase Auth) |
| **Project State** | ProjectSelectionContext | Projeto ativo e filtragem |
| **Team State** | TeamContext | Equipe atual e membros |
| **UI State** | useState/useReducer | Estado local de componentes |

### Contextos Principais:

```
App
├── AuthContext (sessão, login, logout)
├── ProjectSelectionContext (projeto ativo)
│   └── Filtra TODOS os dados por project_id
├── TeamContext (equipe atual)
│   └── Membros, papéis, convites
└── Componentes
    ├── TanStack Query (cache de dados do servidor)
    └── Estado local (useState, useReducer)
```

### Padrão de Query (TanStack Query):
```typescript
const { data, isLoading, error } = useQuery({
  queryKey: ['tasks', selectedProject?.id],
  queryFn: async () => {
    const { data, error } = await supabase
      .from('dev_tasks')
      .select('*')
      .eq('project_id', selectedProject?.id)
      .order('created_at', { ascending: false });
    
    if (error) throw error;
    return data;
  },
  enabled: !!selectedProject?.id, // Só executa se houver projeto
});
```

---

## Banco de Dados — PostgreSQL (Supabase)

### Visão Geral:
- **29 tabelas** no schema principal
- **22 views** para consultas otimizadas
- **pgvector** para busca semântica
- **RLS (Row Level Security)** para isolamento de dados

### Tabelas Principais:

| Tabela | Função |
|---|---|
| `projects` | Projetos da plataforma |
| `team_members` | Perfis de usuários |
| `dev_tasks` | Tarefas de desenvolvimento |
| `sprints` | Sprints de trabalho |
| `meeting_transcripts` | Transcrições de reuniões |
| `generated_documents` | Documentos gerados por IA |
| `ai_interactions` | Rastreamento de uso de IA |
| `project_knowledge_base` | Base de conhecimento |
| `teams` | Equipes |
| `conversations` | Conversas do Guru |
| `messages` | Mensagens do chat |
| `document_chunks` | Chunks para RAG |
| `document_embeddings` | Embeddings vetoriais |

### Isolamento por Projeto:
**TODAS** as queries filtram por `project_id`:
```sql
SELECT * FROM dev_tasks
WHERE project_id = :selected_project_id
ORDER BY created_at DESC;
```

### Row Level Security (RLS):
- Políticas de acesso por projeto
- Usuários só veem dados dos projetos que pertencem
- Admin tem acesso total ao projeto

---

## Edge Functions (Deno)

### Funções de Geração de Documentos:

| Função | Caminho | Modelo IA |
|---|---|---|
| `create-prd` | `supabase/functions/create-prd/` | GPT-4o |
| `create-user-story` | `supabase/functions/create-user-story/` | GPT-4o |
| `create-meeting-notes` | `supabase/functions/create-meeting-notes/` | GPT-4o |
| `create-technical-specs` | `supabase/functions/create-technical-specs/` | GPT-4o |
| `create-test-cases` | `supabase/functions/create-test-cases/` | GPT-4o |
| `create-unit-tests` | `supabase/functions/create-unit-tests/` | GPT-4o |
| `analyze-transcript` | `supabase/functions/analyze-transcript/` | GPT-4o |

### Infraestrutura Compartilhada:
```
supabase/functions/_shared/document-generation/
├── types.ts           # Interfaces TypeScript compartilhadas
├── utils.ts           # Retry, auth, logging
└── business-logic/    # Lógica de negócio reutilizável
```

### Características:
- Runtime **Deno** (TypeScript nativo)
- Chaves de API via Supabase Secrets (seguro)
- Retry automático com exponential backoff
- Rastreamento de tokens automático
- Seleção de modelo (GPT-4o vs GPT-4o-mini) por complexidade

---

## Pipeline RAG (Guru)

### Componentes do Pipeline:

```
1. INGESTÃO
   Upload de documento
       │
       ▼
   Chunking (divisão em trechos)
       │
       ▼
   Geração de Embeddings (OpenAI)
       │
       ▼
   Armazenamento no pgvector

2. CONSULTA
   Pergunta do usuário
       │
       ▼
   Embedding da pergunta
       │
       ▼
   Busca Híbrida
   ├─ Semântica (cosine similarity)
   └─ Textual (full-text search)
       │
       ▼
   Combinação de resultados (RRF)
       │
       ▼
   Construção do contexto
       │
       ▼
   Geração de resposta (GPT-4o)
       │
       ▼
   Resposta + referências
```

---

## Autenticação

### Fluxo:
1. Usuário acessa a aplicação
2. Supabase Auth gerencia login/signup
3. Sessão é mantida via JWT
4. `AuthContext` disponibiliza o estado em toda a aplicação
5. Todas as chamadas ao Supabase incluem o token de autenticação

### Métodos suportados:
- E-mail + senha
- OAuth (quando configurado)

---

## Estrutura de Diretórios

```
src/
├── components/           # Componentes React
│   ├── ui/              # Shadcn/ui (componentes base)
│   ├── projects/        # Componentes de projetos
│   ├── team/            # Componentes de equipes
│   ├── navigation/      # Sidebar e navegação
│   ├── dashboard/       # Dashboard
│   ├── sprints/         # Sprints
│   ├── transcriptions/  # Transcrições
│   ├── planning/        # Planejamento
│   └── tasks/           # Tarefas
├── contexts/            # React Contexts
│   ├── AuthContext.tsx
│   ├── TeamContext.tsx
│   └── ProjectSelectionContext.tsx
├── hooks/               # Custom Hooks
├── lib/                 # Lógica de negócio
│   ├── openai.ts        # OpenAI (legado - docs)
│   ├── openai-secure.ts # OpenAI seguro
│   ├── services/        # Serviços
│   └── utils/           # Utilitários
├── pages/               # Páginas (rotas)
├── types/               # TypeScript types
├── integrations/        # Supabase client
├── locales/             # i18n (pt-br, en-us)
├── prompts/             # Templates de prompts
│   └── document-templates/
└── schemas/             # Zod schemas
```

---

## Performance

### Otimizações Implementadas:
- **Lazy Loading**: Rotas carregadas sob demanda
- **Query Caching**: TanStack Query cacheia respostas
- **Code Splitting**: Vite divide automaticamente chunks
- **Image Optimization**: Formatos otimizados e lazy loading
- **Bundle Splitting**: Vendor chunks separados

### Monitoramento:
- Dashboard de métricas de IA (tokens, custos)
- Indicadores de produtividade por sprint
- Relatórios de uso por projeto
