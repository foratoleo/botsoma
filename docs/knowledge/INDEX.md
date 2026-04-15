# WORKFORCE - Bot Knowledge Base Index

> LLM-optimized reference for the WORKFORCE project management platform.

Created: 2026-04-10
Last Updated: 2026-04-10

## Quick Navigation

| Category | File | Content |
|----------|------|---------|
| Architecture | [architecture/overview.md](architecture/overview.md) | High-level system architecture, tech stack, data flow |
| Areas | [areas/planning.md](areas/planning.md) | Planning area (projects, backlog, features, sprints, tasks, teams, meetings) |
| Areas | [areas/development.md](areas/development.md) | Development area (PRs, metrics, AI agents, style guides, repositories) |
| Areas | [areas/quality.md](areas/quality.md) | Quality area (bugs, test cases, automated testing, accessibility, performance) |
| Areas | [areas/governance.md](areas/governance.md) | Governance area (permissions, RAG config, Jira, platform settings, user management) |
| Frontend | [frontend/components.md](frontend/components.md) | Component architecture, 50+ component directories |
| Frontend | [frontend/hooks.md](frontend/hooks.md) | 120+ custom hooks for data fetching and logic |
| Frontend | [frontend/contexts.md](frontend/contexts.md) | React Context providers (Auth, Team, Project, Area, Governance) |
| Frontend | [frontend/pages-and-routing.md](frontend/pages-and-routing.md) | Page components and route definitions |
| Frontend | [frontend/services.md](frontend/services.md) | 65+ service files for business logic |
| Backend | [backend/edge-functions.md](backend/edge-functions.md) | 80+ Supabase Edge Functions (Deno) |
| Backend | [backend/shared-modules.md](backend/shared-modules.md) | Shared modules in `_shared/` directory |
| AI | [ai/document-generation.md](ai/document-generation.md) | AI document generation pipeline (PRD, user stories, meeting notes, etc.) |
| AI | [ai/openai-integration.md](ai/openai-integration.md) | OpenAI integration patterns, conversation tracking, cost management |
| AI | [ai/rag-system.md](ai/rag-system.md) | RAG (Retrieval Augmented Generation) system |
| Integrations | [integrations/jira.md](integrations/jira.md) | Jira sync, webhooks, bidirectional integration |
| Integrations | [integrations/github.md](integrations/github.md) | GitHub PR sync, code review metrics |
| Integrations | [integrations/calendar.md](integrations/calendar.md) | Microsoft Calendar (Outlook) integration, OAuth, Recall.ai |
| Integrations | [integrations/recall.md](integrations/recall.md) | Recall.ai meeting bot integration |
| Modules | [modules/projects.md](modules/projects.md) | Project CRUD, wizard, details, import/export |
| Modules | [modules/teams.md](modules/teams.md) | Team management, members, invitations, allocation |
| Modules | [modules/tasks.md](modules/tasks.md) | Task CRUD, comments, attachments, status management |
| Modules | [modules/sprints.md](modules/sprints.md) | Sprint planning, analytics, snapshots |
| Modules | [modules/meetings.md](modules/meetings.md) | Meeting CRUD, recording, sharing, participants |
| Modules | [modules/transcriptions.md](modules/transcriptions.md) | Transcription upload, processing, PDF extraction |
| Modules | [modules/backlog.md](modules/backlog.md) | Backlog management, prioritization, AI generation |
| Modules | [modules/features.md](modules/features.md) | Feature management, relationships, attachments |
| Modules | [modules/bugs.md](modules/bugs.md) | Bug tracking, severity, priority, analysis |
| Modules | [modules/knowledge.md](modules/knowledge.md) | Knowledge base, company knowledge entries |
| Modules | [modules/documents.md](modules/documents.md) | Document management, approval, versioning |
| Helpbot | [helpbot/helpbot.md](helpbot/helpbot.md) | Telegram/Helpbot knowledge base for end-users |

## System Overview

WORKFORCE is a **project management platform** with AI-powered document generation, built with:

- **Frontend**: React 18 + TypeScript + Vite + Shadcn/ui + Tailwind CSS
- **State**: TanStack Query v5 (server), React Context (app state)
- **Backend**: Supabase (PostgreSQL + Auth + Storage + Edge Functions)
- **AI**: OpenAI Responses API with Edge Functions for secure generation
- **Build**: pnpm
- **i18n**: Custom `useI18n` hook with `pt-br.ts` and `en-us.ts` locale files

## 4 Workflow Areas

The app is organized into 4 color-coded areas, each with dedicated sidebar navigation:

| Area | Theme Color | Focus |
|------|------------|-------|
| **Planning** | Dark Gold (#B8860B) | Projects, backlog, features, sprints, tasks, teams, meetings |
| **Development** | Gray/Silver (#9E9E9E) | PRs, code review, AI agents, style guides, repositories |
| **Quality/Testing** | Bronze (#CD7F32) | Bugs, test cases, automated testing, accessibility, performance |
| **Governance** | Dark Green (#1B4332) | Permissions, RAG config, Jira, platform settings, user management |

## Key Patterns

- **Project Context**: All data filtered by `selectedProject?.id` via `useProjectSelection()` hook
- **Area Detection**: `useArea()` / `AreaContext` determines current area and sidebar
- **Lazy Loading**: All pages use `lazyWithRetry` for code splitting
- **Edge Functions**: All AI operations run server-side via Supabase Edge Functions (Deno)
- **Document Generation**: `generateDocumentAPI()` in `src/lib/services/document-generation-service.ts`
