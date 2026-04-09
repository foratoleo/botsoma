# DR AI Workforce — Visão Geral

## O que é o DR AI Workforce?

O **DR AI Workforce** é uma plataforma avançada de planejamento e gestão de projetos de desenvolvimento de software, impulsionada por Inteligência Artificial. Desenvolvida pela **Digital Republic**, a plataforma transforma requisitos e transcrições de reuniões em documentação estruturada, automatizando tarefas repetitivas e aumentando a produtividade das equipes.

Em essência, é um hub centralizado onde equipes de desenvolvimento podem:

- **Planejar** projetos e sprints
- **Gerenciar** tarefas, equipes e cronogramas
- **Gerar documentação** automaticamente com IA (PRDs, User Stories, Especificações Técnicas, etc.)
- **Conversar com seus documentos** via um chat inteligente (Guru)
- **Acompanhar métricas** e indicadores de desempenho em dashboards visuais

---

## Missão

> Transformar a forma como equipes de desenvolvimento de software trabalham, fornecendo ferramentas inteligentes que aumentam a produtividade e a qualidade das entregas.

## Visão 2025-2027

> Ser a plataforma de referência em gestão de desenvolvimento de software assistida por IA na América Latina, atendendo mais de 500 empresas e 10.000 usuários ativos.

---

## Valores

| Valor | Descrição |
|---|---|
| **Excelência Técnica** | Buscamos sempre as melhores soluções técnicas, priorizando qualidade sobre velocidade. |
| **Transparência** | Comunicação aberta com clientes, parceiros e colaboradores em todas as situções. |
| **Inovação Contínua** | Experimentação constante com novas tecnologias e metodologias. |
| **Foco no Cliente** | Todas as decisões partem das necessidades reais dos usuários. |

---

## Funcionalidades Principais

### 1. Gestão de Projetos
- Criação e gerenciamento completo de projetos
- Sistema de seleção de contexto — todos os dados são filtrados pelo projeto ativo
- Controle de visibilidade e permissões
- Histórico de atividades e colaboradores
- Upload e gestão de documentos de referência

### 2. Geração de Documentação com IA
- Conversão automática de transcrições de reuniões em documentação estruturada
- Geração de PRDs, User Stories, Especificações Técnicas, Notas de Reunião e Casos de Teste
- Integração com OpenAI (GPT-4o e GPT-4o-mini)
- Sistema de conversação contínua para gerar múltiplos documentos na mesma sessão
- Redução de 71-75% no uso de tokens com a Responses API

### 3. Gestão de Equipes
- Criação e administração de times
- Sistema de convites e permissões (papéis: admin, membro, visualizador)
- Controle de membros e limites baseados em plano de assinatura

### 4. Gestão de Sprints e Tarefas
- Planejamento e acompanhamento de sprints com métricas de velocidade
- Tarefas com status (todo, in_progress, done, blocked) e prioridades (critical, high, medium, low)
- Integração com geração de tarefas por IA
- Visualização de progresso (Kanban e lista)

### 5. Dashboard e Métricas
- Visão geral de projetos ativos
- Indicadores de desempenho e produtividade
- Análise de métricas por sprint
- Relatórios customizáveis

### 6. Sistema de Transcrições
- Upload e gestão de transcrições de reuniões
- Filtros e busca avançada
- Geração de múltiplos documentos a partir de uma única transcrição
- Histórico de documentos gerados

### 7. Chat RAG — Guru
- Chat inteligente que responde perguntas com base nos documentos do projeto
- Busca híbrida (semântica + textual) usando pgvector
- Conversas persistentes com histórico
- Referências e fontes indicadas nas respostas

### 8. Navegação Hierárquica por Fases
- 4 áreas de trabalho com identidade visual própria
- Sidebar colapsável com navegação contextual
- Suporte a idiomas (Português e Inglês)
- Tema claro/escuro

---

## Stack Tecnológico

### Frontend
| Tecnologia | Função |
|---|---|
| React 18 | Biblioteca para construção de interfaces |
| TypeScript | Tipagem estática e segurança no código |
| Vite | Build tool e dev server ultra-rápido |
| Tailwind CSS | Framework CSS utility-first |
| Shadcn/ui + Radix UI | Componentes UI modernos e acessíveis |
| TanStack Query v5 | Gerenciamento de estado assíncrono (server state) |
| React Router DOM v6 | Roteamento SPA |
| Framer Motion | Animações declarativas |
| Recharts | Gráficos e visualizações |

### Backend & Infraestrutura
| Tecnologia | Função |
|---|---|
| Supabase | Backend as a Service (PostgreSQL, Auth, Storage, Edge Functions) |
| OpenAI API (GPT-4o) | Geração de conteúdo com IA |
| Edge Functions (Deno) | Funções serverless para geração de documentos |
| pgvector | Busca semântica no banco de dados |

### Qualidade
| Tecnologia | Função |
|---|---|
| ESLint v9 | Linting de código |
| Zod | Validação de schemas |
| React Hook Form | Gerenciamento de formulários |

---

## Como tudo se conecta

```
┌──────────────────────────────────────────────────────┐
│                    USUÁRIO                           │
│  (Autenticado via Supabase Auth)                     │
└──────────────┬───────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────┐
│              INTERFACE REACT                          │
│  ┌─────────┐ ┌──────────┐ ┌───────────┐ ┌────────┐  │
│  │Planning │ │Develop.  │ │Testing    │ │Governa.│  │
│  └─────────┘ └──────────┘ └───────────┘ └────────┘  │
│         │         │           │            │         │
│         ▼         ▼           ▼            ▼         │
│  ┌──────────────────────────────────────────────┐    │
│  │        ProjectSelectionContext                │    │
│  │   (Filtra TODOS os dados por project_id)     │    │
│  └──────────────────┬───────────────────────────┘    │
│                     │                                 │
│         ┌───────────┼───────────┐                     │
│         ▼           ▼           ▼                     │
│  ┌────────────┐ ┌────────┐ ┌───────────┐             │
│  │  Supabase  │ │ OpenAI │ │ Edge      │             │
│  │  (DB/Auth) │ │  API   │ │ Functions │             │
│  └────────────┘ └────────┘ └───────────┘             │
└──────────────────────────────────────────────────────┘
```

---

## Próximos Passos

Para entender cada parte do sistema em detalhes, consulte os outros arquivos desta documentação:

- **[02-navegacao-e-areas.md](./02-navegacao-e-areas.md)** — Navegação e áreas de trabalho
- **[03-gestao-projetos.md](./03-gestao-projetos.md)** — Gestão de projetos
- **[04-gestao-equipes-tarefas-sprints.md](./04-gestao-equipes-tarefas-sprints.md)** — Equipes, tarefas e sprints
- **[05-transcricoes-e-reunioes.md](./05-transcricoes-e-reunioes.md)** — Transcrições e reuniões
- **[06-geracao-documentos-ia.md](./06-geracao-documentos-ia.md)** — Geração de documentos com IA
- **[07-chat-rag-guru.md](./07-chat-rag-guru.md)** — Chat RAG (Guru)
- **[08-upload-documentos.md](./08-upload-documentos.md)** — Upload de documentos
- **[09-arquitetura-tecnica.md](./09-arquitetura-tecnica.md)** — Arquitetura técnica
- **[10-integracoes.md](./10-integracoes.md)** — Integrações externas
- **[11-perguntas-frequentes.md](./11-perguntas-frequentes.md)** — Perguntas frequentes
