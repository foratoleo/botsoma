# Sprints Module

Created: 2026-04-10
Last Updated: 2026-04-10

## Overview

Sprint planning with analytics, velocity tracking, snapshots, and AI-powered analysis.

## Components

| Directory | Purpose |
|-----------|---------|
| `src/components/sprints/` (14 files) | Sprint management UI |
| `src/components/sprint-analytics/` (19 files) | Charts, velocity, burndown |

## Pages

| Page | Route | File |
|------|-------|------|
| Sprint List | `/sprints` | `pages/SprintList.tsx` |
| Sprint Details | `/sprints/:id` | `pages/sprints/SprintDetails.tsx` |
| Create Sprint | `/sprints/new` | `pages/sprints/SprintForm.tsx` |
| Sprint Tasks | `/sprints/:id/tasks` | `pages/sprints/SprintTasks.tsx` |
| Sprint Analytics | `/sprints/:id/analytics` | `pages/sprints/SprintAnalyticsPage.tsx` |

## Hooks

| Hook | Purpose |
|------|---------|
| `useSprints` | Sprint listing |
| `useSprintDetails` | Single sprint data |
| `useBatchSprintCreation` | Create multiple sprints at once |
| `useSprintAnalytics` | Sprint metrics and charts |

## Services

| Service | Purpose |
|---------|---------|
| `sprint-service.ts` (15k) | Sprint CRUD and analytics |

## Utilities

| File | Purpose |
|------|---------|
| `src/lib/utils/sprint-utils.ts` (16k) | Sprint date calculations, velocity |
| `src/lib/utils/sprint-analytics-utils.ts` (15k) | Analytics computations |

## Edge Functions

| Function | Purpose |
|----------|---------|
| `api-sprints` | Sprint CRUD API |
| `api-sprints-list` | Sprint listing |
| `api-sprint-details` | Sprint detail |
| `analyze-sprint` | AI sprint analysis |
| `snapshot-active-sprints` | Snapshot current sprint state |

## Sprint Data Model

```typescript
interface Sprint {
  id: string;
  project_id: string;
  name: string;
  goal?: string;
  status: 'planning' | 'active' | 'completed' | 'cancelled';
  start_date: string;
  end_date: string;
  velocity?: number;
  created_at: string;
}
```
