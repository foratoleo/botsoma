# Bugs Module

Created: 2026-04-10
Last Updated: 2026-04-10

## Overview

Bug tracking with severity/priority classification, AI analysis, and statistics.

## Components

| Directory | Purpose |
|-----------|---------|
| `src/components/bugs/` (12 files) | Bug tracking UI |

### Component Details

| Component | Purpose |
|-----------|---------|
| `BugCard` | Bug card display |
| `BugCreateSheet` | Slide-over creation form |
| `BugForm` | Form with validation (title, description, severity, priority, tags) |
| `BugList` | Filtered bug listing |
| `BugFilters` | Filter by status, severity, priority, assignee |
| `BugAnalysisDialog` | AI-powered bug analysis |
| `BugPriorityBadge` | P0 (critical) through P4 (low) |
| `BugSeverityBadge` | critical, major, moderate, minor, trivial |
| `BugStatusBadge` | open, in_progress, resolved, closed, reopened |

## Pages

| Page | Route | File |
|------|-------|------|
| Bug Reports Dashboard | `/quality/bugs` | `pages/quality/BugReportsDashboard.tsx` |
| Bug List | `/quality/bugs/list` | `pages/quality/BugListPage.tsx` |
| Bug Detail | `/quality/bugs/:id` | `pages/quality/BugDetailPage.tsx` |

## Hooks

| Hook | Purpose |
|------|---------|
| `useBugs` | Bug listing with filters and pagination |
| `useBugById` | Single bug fetch |
| `useBugCreate` | Bug creation mutation |
| `useBugStatistics` | Aggregated bug stats |

## Services

| Service | Purpose |
|---------|---------|
| `bug-service.ts` (18k) | Bug CRUD with advanced filtering |

## Utilities

| File | Purpose |
|------|---------|
| `src/lib/utils/bug-trends.ts` (2k) | Bug trend calculations |

## Bug Data Model

```typescript
interface Bug {
  id: string;
  project_id: string;
  title: string;
  description?: string;
  severity: 'critical' | 'major' | 'moderate' | 'minor' | 'trivial';
  priority: 'P0' | 'P1' | 'P2' | 'P3' | 'P4';
  status: 'open' | 'in_progress' | 'resolved' | 'closed' | 'reopened';
  assignee_id?: string;
  reporter_id?: string;
  tags?: string[];
  steps_to_reproduce?: string;
  expected_behavior?: string;
  actual_behavior?: string;
  environment?: string;
  created_at: string;
  updated_at: string;
}
```

## Bug Status Flow

```
open → in_progress → resolved → closed
  ↑                                 ↓
  └─────── reopened ←───────────────┘
```

## Types

Defined in `src/types/bug.ts` (3k) with all interfaces and enums for bug management.
