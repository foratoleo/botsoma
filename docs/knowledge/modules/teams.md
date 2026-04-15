# Teams Module

Created: 2026-04-10
Last Updated: 2026-04-10

## Overview

Team management with member roles, invitations, allocation, and hybrid team support.

## Components

| Directory | Purpose |
|-----------|---------|
| `src/components/teams/` (22 files) | Team management, expansion, invitations |
| `src/components/team/` (9 files) | Team display components |
| `src/components/team/hybrid/` | Hybrid team support |
| `src/components/team-members/` (4 files) | Member management |
| `src/components/teams/expansion/` | Team expansion features |

## Pages

| Page | Route | File |
|------|-------|------|
| Teams | `/team` | `pages/Teams.tsx` |
| Create Team | `/team/new` | `pages/teams/CreateTeam.tsx` |
| Team Member Detail | `/team/:id` | `pages/teams/[id].tsx` |
| Team Expansion | `/team/expansion` | `pages/teams/TeamExpansionPage.tsx` |

## Hooks

| Hook | Purpose |
|------|---------|
| `useTeamMembers` | Team member listing |
| `useMemberAllocation` | Member allocation status |
| `useAllocationRequests` | Allocation request CRUD |
| `useMemberProjects` | Projects by member |

## Services

| Service | Purpose |
|---------|---------|
| `team-service.ts` (17k) | Team CRUD |
| `team-member-service.ts` (29k) | Member management with roles |
| `invitation-service.ts` (20k) | Team invitation flow |
| `project-team-member-service.ts` (14k) | Project-member associations |

## Context

`TeamContext` (`src/contexts/TeamContext.tsx`):

```typescript
const { currentTeam, teams, setCurrentTeam, loading } = useTeam();
```

## Team Data Model

```typescript
interface Team {
  id: string;
  name: string;
  description?: string;
  created_at: string;
}

interface TeamMember {
  id: string;
  team_id: string;
  user_id: string;
  role: 'admin' | 'manager' | 'member' | 'viewer';
  joined_at: string;
}
```
