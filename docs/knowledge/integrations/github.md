# GitHub Integration

Created: 2026-04-10
Last Updated: 2026-04-10

## Overview

Integration with GitHub for pull request tracking, code review metrics, and repository management.

## Edge Functions

| Function | Purpose |
|----------|---------|
| `sync-github-prs` | Sync pull requests from GitHub |
| `sync-code-review-metrics` | Sync code review metrics |

## Shared Modules

Located in `supabase/functions/_shared/github/` (13 files):

| File | Purpose |
|------|---------|
| GitHub API client, PR fetching, metrics calculation |

## Hooks

| Hook | Purpose |
|------|---------|
| `useGitRepositories` (16k) | Repository management |
| `useGitHubPullRequests` | PR listing |
| `useGitHubPRMetrics` | PR metrics data |
| `useGitHubPRStats` | PR statistics |
| `useGitHubPullRequestDetail` | Single PR detail |
| `useGitHubAccountMappings` | GitHub-to-team member mapping |

## Services

| Service | Purpose |
|---------|---------|
| `git-repository-service.ts` (25k) | Repository CRUD and sync |
| `github-pr-service.ts` (12k) | PR operations |
| `github-pr-metrics-service.ts` (24k) | PR metrics calculation |
| `github-sync-config-service.ts` (10k) | Sync configuration |

## Pages

| Page | Route |
|------|-------|
| Pull Requests | `/development/pull-requests` |
| PR Metrics | `/development/pr-metrics` |
| Code Review Metrics | `/development/code-review` |
| Repositories | `/development/repositories` |

## Components

Located in `src/components/`:
- GitHub PR displays
- PR metrics dashboards
- Repository management UI

## Utilities

| File | Purpose |
|------|---------|
| `src/lib/utils/github-pr-mappers.ts` (9k) | Map GitHub API data to app models |
