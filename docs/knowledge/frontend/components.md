# Components Architecture

Created: 2026-04-10
Last Updated: 2026-04-10

## Component Organization

Components live in `src/components/` with 50+ subdirectories, each representing a feature domain.

## Component Directories

| Directory | Files | Purpose |
|-----------|-------|---------|
| `ui/` | 57 | Shadcn/ui base primitives (Button, Dialog, Sheet, etc.) |
| `tasks/` | 40 | Task CRUD, comments, attachments, assignment, status |
| `projects/` | 44 | Project management, wizard, details, settings |
| `documents/` | 24 | Document management, renderers, cards, dialogs |
| `meetings/` | 30 | Meeting CRUD, scheduling, recording, sharing |
| `teams/` | 22 | Team management, expansion, invitations |
| `features/` | 28 | Feature CRUD, relationships, dependencies |
| `governance/` | 25 | Permissions, access control, admin |
| `sprint-analytics/` | 19 | Charts, velocity, burndown, metrics |
| `navigation/` | 11 | Sidebar, top menu, area guards, team selector |
| `transcriptions/` | 18 | Upload, processing, document generation |
| `ai-agents/` | 10+ | AI agent config with tabbed interface |
| `style-guides/` | 17 | Code style guide management |
| `backlog/` | 20 | Board, table, filters, statistics |
| `bugs/` | 12 | Bug tracking, severity, priority |
| `legacy-code/` | 8 | Legacy code health, migration |
| `chat/` | 10 | Floating chat, messages, sources panel |
| `jira/` | 11 | Jira integration UI |
| `auth/` | 9 | Login, signup, password reset |
| `kanban/` | 7 | Kanban board drag-and-drop |
| `markdown/` | 11 | Markdown editor and preview |
| `rag/` | 8 | RAG configuration UI |
| `quality/` | 6 | Quality management |
| `test-generator/` | 10 | Test generation wizard |
| `sprints/` | 14 | Sprint planning and management |
| `knowledge/` | 7 | Knowledge base entries |
| `calendar-integration/` | 8 | Microsoft Calendar UI |
| `upload/` | 4 | File upload components |
| `backlog-creation/` | 5 | Backlog generation wizard |
| `feature-creation/` | 7 | Feature creation wizard |
| `calendar-events/` | 5 | Calendar event details |
| `common/` | 4 | Shared components (ProjectSelector, TagInput) |
| `demos/` | 5 | Public demo video pages |
| `errors/` | 6 | Error monitoring and display |
| `guards/` | 4 | Route guards |
| `team/` | 9 | Team display components |
| `team-members/` | 4 | Team member management |
| `user/` | 5 | User profile components |

## Top-Level Components

| File | Purpose |
|------|---------|
| `Layout.tsx` | Main app layout with area-based sidebar, navigation, footer |
| `ErrorBoundary.tsx` | Global error boundary with recovery |
| `ProtectedRoute.tsx` | Auth guard for protected routes |
| `PageLoader.tsx` | Loading spinner for page transitions |
| `advanced-ai-settings.tsx` | AI configuration panel |
| `document-type-selector.tsx` | Document type picker |
| `prompt-selector.tsx` | Prompt template selector |
| `project-selector.tsx` | Project switcher dropdown |
| `sequential-generation-progress.tsx` | AI generation progress display |

## Component Pattern

All components follow this structure:
```
1. Type definitions and interfaces
2. Component function with hooks at top
3. Event handlers
4. Render logic with conditional rendering
5. Export statement
```

## Shadcn/ui Components (src/components/ui/)

57 base components including: accordion, alert, avatar, badge, breadcrumb, button, calendar, card, chart, checkbox, collapsible, command, context-menu, dialog, dropdown-menu, form, hover-card, input, label, menubar, navigation-menu, pagination, popover, progress, radio-group, resizable, scroll-area, select, separator, sheet, sidebar, skeleton, slider, sonner, switch, table, tabs, textarea, toast, toaster, toggle, tooltip.

These are Radix UI primitives wrapped with Tailwind styling. Never modify directly; use `npx shadcn-ui@latest add <component>` to add new ones.
