# Jira Integration

Created: 2026-04-10
Last Updated: 2026-04-10

## Overview

Bidirectional integration between WORKFORCE and Jira for task synchronization, webhooks, and health monitoring.

## Architecture

```
WORKFORCE  ←→  Jira Sync Service  ←→  Jira Cloud API
    ↑                                    ↑
    └── Edge Functions (server-side)  ───┘
    └── Webhooks (event-driven)       ───┘
```

## Edge Functions

| Function | Purpose |
|----------|---------|
| `jira-sync-tasks` | Bidirectional task sync |
| `jira-webhook` | Receive Jira event webhooks |
| `jira-health` | Jira connection health check |
| `sync-jira-to-drai` | Pull changes from Jira |
| `sync-drai-to-jira` | Push changes to Jira |

## Frontend Components

Located in `src/components/jira/` (11 files):

| Component | Purpose |
|-----------|---------|
| Jira config forms, status displays, sync controls |

## Hooks

| Hook | Purpose |
|------|---------|
| `useJiraConfig` | Jira configuration CRUD |
| `useJiraSync` | Trigger sync operations |
| `useGovernanceJiraConfig` | Governance Jira config access |

## Services

| Service | Purpose |
|---------|---------|
| `jira-sync-service.ts` (19k) | Bidirectional sync logic |

## Shared Modules (Edge Functions)

Located in `supabase/functions/_shared/`:

| File | Purpose |
|------|---------|
| `jira-client.ts` (12k) | Jira Cloud API client |
| `jira-db-service.ts` (19k) | Jira database operations |
| `jira-db-service-optimized.ts` (17k) | Optimized database operations |
| `jira-alerts.ts` (17k) | Alert system for sync issues |
| `jira-error-handler.ts` (17k) | Error handling |
| `jira-logger.ts` (12k) | Sync logging |
| `jira-metrics.ts` (16k) | Sync metrics |

## Configuration

Managed via Governance area:
- `/governance/jira` - List Jira integrations
- `/governance/jira/:id` - Configure integration
- Stores: Jira URL, API token, project mapping, field mapping

## Pages

| Page | Route |
|------|-------|
| Jira Integrations List | `/governance/jira` |
| Jira Config Form | `/governance/jira/:id` |
