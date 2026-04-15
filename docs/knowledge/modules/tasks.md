# Tasks Module

Created: 2026-04-10
Last Updated: 2026-04-10

## Overview

Task management with CRUD, status tracking, comments, attachments, assignment, and AI-powered generation.

## Components

| Directory | Purpose |
|-----------|---------|
| `src/components/tasks/` (40 files) | Full task management UI |
| `src/components/tasks/comments/` | Task comments |
| `src/components/kanban/` (7 files) | Kanban board view |

## Pages

| Page | Route | File |
|------|-------|------|
| Tasks | `/tasks` | `pages/Tasks.tsx` |
| Tasks Landing | `/tasks` (area-aware) | `pages/tasks/TasksLandingPage.tsx` |
| AI Suggested Tasks | `/tasks/suggested` | `pages/tasks/AISuggestedTasksPage.tsx` |
| Task Edit | `/tasks/:id/edit` | `pages/tasks/TaskEditPage.tsx` |

## Hooks

| Hook | Purpose |
|------|---------|
| `useTasks` | Task listing with filtering and sorting |
| `useBatchTaskOperations` | Bulk status/assignee updates |
| `useGenerateTasks` | AI-powered task generation from content |

## Services

| Service | Purpose |
|---------|---------|
| `task-service.ts` (15k) | Task CRUD, status management |
| `task-attachment-service.ts` (25k) | File attachments on tasks |
| `comment-service.ts` (9k) | Task comments CRUD |
| `task-content-service.ts` (2k) | Task content management |

## Task Data Model

```typescript
interface DevTask {
  id: string;
  project_id: string;
  title: string;
  description?: string;
  status: 'todo' | 'in_progress' | 'done' | 'blocked';
  priority: 'low' | 'medium' | 'high' | 'critical';
  assignee_id?: string;
  sprint_id?: string;
  feature_id?: string;
  story_points?: number;
  due_date?: string;
  tags?: string[];
  created_at: string;
  updated_at: string;
}
```

## Task Status Flow

```
todo → in_progress → done
  ↓         ↓
blocked ←──┘
  ↓
in_progress (unblocked)
```

## Edge Functions

| Function | Purpose |
|----------|---------|
| `api-tasks` | Task CRUD API |
| `api-task-details` | Single task detail |
| `api-task-status` | Status update |
| `api-task-assign` | Assignment |
| `api-task-comments` | Comments CRUD |
| `api-tasks-list` | Task listing |
| `api-tasks-status-update` | Batch status update |
| `create-tasks` | AI task generation |
