# Backlog Module

Created: 2026-04-10
Last Updated: 2026-04-10

## Overview

Backlog management with board/table views, prioritization, AI generation, statistics, and CSV import.

## Components

| Directory | Purpose |
|-----------|---------|
| `src/components/backlog/` (20 files) | Board, table, filters, items, toolbar |
| `src/components/backlog-creation/` (5 files) | AI generation wizard |
| `src/components/backlog/statistics/` (4 files) | Statistics cards |

### Key Components

| Component | Purpose |
|-----------|---------|
| `BacklogBoard` | Kanban-style board view |
| `BacklogBoardView` | Board container with columns |
| `BacklogColumn` | Individual board column |
| `BacklogTable` | Table view |
| `BacklogItem` | Single backlog item card |
| `BacklogItemCreator` | Quick item creation |
| `BacklogItemForm` | Item form with validation |
| `BacklogFilters` | Filter controls |
| `BacklogToolbar` | View controls and actions |
| `BacklogImportDialog` | CSV import dialog |
| `BacklogStatistics` | Statistics dashboard |
| `BacklogGenerationWizard` | AI generation flow |
| `BacklogGenerationProgress` | Generation progress display |

### Statistics Components

| Component | Purpose |
|-----------|---------|
| `AgeDistributionCard` | Item age distribution chart |
| `BusinessValueMatrix` | Value vs effort matrix |
| `FeaturePipelineCard` | Pipeline visualization |
| `HealthScoreCard` | Backlog health score |

## Pages

| Page | Route | File |
|------|-------|------|
| Backlog Hub | `/planning/backlog` | `pages/backlog/BacklogHubPage.tsx` |
| Backlog List | `/planning/backlog/list` | `pages/backlog/BacklogListPage.tsx` |
| Backlog Board | `/planning/backlog/board` | `pages/backlog/BacklogBoardPage.tsx` |
| Backlog Statistics | `/planning/backlog/statistics` | `pages/backlog/BacklogStatisticsPage.tsx` |
| Backlog Prioritization | `/planning/backlog/prioritize` | `pages/backlog/BacklogPrioritizationPage.tsx` |
| Backlog Generation | `/planning/backlog/generate` | `pages/backlog/BacklogGenerationPage.tsx` |

## Hooks

| Hook | Purpose |
|------|---------|
| `useBacklog` (27k) | Full backlog CRUD with filtering, sorting, pagination |
| `useBacklogDragDrop` (9k) | Drag-and-drop prioritization |
| `useBacklogGeneration` (12k) | AI-powered backlog generation |

## Services

| Service | Purpose |
|---------|---------|
| `backlog-service.ts` (15k) | Backlog CRUD |
| `backlog-conversion.ts` (10k) | Convert backlog items to features/tasks |

## Utilities

| File | Purpose |
|------|---------|
| `src/lib/utils/csv-backlog-parser.ts` (13k) | CSV import parsing |
| `src/lib/utils/backlog-utils.ts` (8k) | Backlog utility functions |
| `src/lib/utils/backlog-style-helpers.ts` (12k) | Styling helpers |
| `src/lib/universal-backlog-integration.ts` (10k) | Universal backlog adapter |

## Edge Functions

| Function | Purpose |
|----------|---------|
| `api-backlog-items` | Backlog CRUD API |
| `create-backlog-items` | AI backlog generation |
| `suggest-backlog-item` | AI backlog suggestions |
| `get-backlog-normalized-record` | Normalize for RAG indexing |

## Backlog Data Model

```typescript
interface BacklogItem {
  id: string;
  project_id: string;
  title: string;
  description?: string;
  type: 'feature' | 'bug' | 'task' | 'improvement';
  priority: 'critical' | 'high' | 'medium' | 'low';
  status: 'new' | 'groomed' | 'ready' | 'in_progress' | 'done';
  business_value?: number;
  effort_estimate?: number;
  tags?: string[];
  source?: 'manual' | 'ai_generated' | 'csv_import';
  created_at: string;
}
```
