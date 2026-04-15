# Architecture Overview

Created: 2026-04-10
Last Updated: 2026-04-10

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Framework | React 18 + TypeScript | UI framework with type safety |
| Build | Vite | Fast dev server and production bundler |
| Package Manager | pnpm | Dependency management |
| UI Components | Shadcn/ui (Radix UI) | Accessible, composable component library |
| Styling | Tailwind CSS | Utility-first CSS with custom theme |
| State (Server) | TanStack Query v5 | Server state caching and synchronization |
| State (App) | React Context | Auth, Team, Project, Area contexts |
| Backend | Supabase | PostgreSQL, Auth, Storage, Edge Functions |
| AI | OpenAI Responses API | Document generation, chat, analysis |
| Routing | React Router v6 | Client-side routing with lazy loading |
| Forms | React Hook Form + Zod | Form handling and validation |
| i18n | Custom useI18n | Multi-language support (pt-BR, en-US) |
| Testing | Vitest + Playwright | Unit and E2E testing |

## Directory Structure

```
workforce/
├── src/
│   ├── components/        # 50+ component directories (UI, features, areas)
│   ├── config/            # App configuration (navigation, OpenAI, validation)
│   ├── constants/         # Static constants and mock data
│   ├── contexts/          # React Context providers (9 files)
│   ├── hooks/             # Custom hooks (120+ files)
│   ├── lib/               # Core business logic (75+ files)
│   │   ├── rag/           # RAG system (16 files)
│   │   ├── services/      # Service layer (65+ files)
│   │   ├── utils/         # Utility functions (35+ files)
│   │   ├── constants/     # Lib-level constants
│   │   ├── jira/          # Jira integration helpers
│   │   ├── navigation/    # Navigation utilities
│   │   ├── security/      # Security utilities
│   │   ├── errors/        # Error handling
│   │   ├── migrations/    # Data migration helpers
│   │   └── test-generator/# Test generation logic
│   ├── pages/             # Route-level page components (50+ files)
│   ├── types/             # TypeScript type definitions (78+ files)
│   ├── locales/           # i18n translation files
│   ├── prompts/           # AI prompt templates
│   ├── schemas/           # Zod validation schemas
│   └── main.tsx           # App entry point
├── supabase/
│   └── functions/         # 80+ Edge Functions (Deno)
│       └── _shared/       # Shared modules across functions
├── public/                # Static assets
├── scripts/               # Utility scripts
├── sql/                   # SQL migrations and queries
├── tests/                 # E2E and integration tests
├── helpbot/               # Telegram bot knowledge base (11 .md files)
└── docs/                  # Project documentation
```

## Data Flow

```
User Action
    ↓
React Component (page/component)
    ↓
Custom Hook (src/hooks/)
    ↓
TanStack Query (caching, retry, background refetch)
    ↓
Service Layer (src/lib/services/)
    ↓
Supabase Client (src/lib/supabase.ts)
    ↓
┌─────────────────────────────────────────┐
│  Supabase Backend                        │
│  ├── PostgreSQL (RLS by project_id)      │
│  ├── Auth (JWT sessions)                 │
│  ├── Storage (file uploads)              │
│  └── Edge Functions (AI operations)      │
│       └── OpenAI API                     │
└─────────────────────────────────────────┘
```

## Key Architectural Decisions

1. **Project Isolation**: All database queries filtered by `project_id` via RLS
2. **Edge Functions for AI**: API keys never exposed to client; server-side only
3. **Lazy Loading**: Every page uses `lazyWithRetry` for code splitting and error recovery
4. **Area-Based Navigation**: 4 color-coded areas with independent sidebars
5. **Custom i18n**: Not using i18next; custom `useI18n` hook with namespace support
6. **Context Hierarchy**: Auth → Team → ProjectSelection → Area → AreaAccess
