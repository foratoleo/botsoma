# Governance Area

Created: 2026-04-10
Last Updated: 2026-04-10

## Theme

- **Primary**: Dark Green (#1B4332)
- **Accent**: #2D6A4F
- **Background**: rgba(240, 247, 244, 0.4)
- **CSS Variable**: `[data-area="governance"]`

## Focus

Administration, permissions, integrations, platform configuration, and user management.

## Key Components

| Directory | Purpose |
|-----------|---------|
| `src/components/governance/` | Governance area components (25 files) |
| `src/components/governance/wizard/` | Governance wizard flows |

## Key Hooks

| Hook | Purpose |
|------|---------|
| `useGovernance` | Governance state access |
| `useGovernanceDocuments` | Governance document listing |
| `useGovernanceIndexingStatus` | Document indexing progress |
| `useGovernanceJiraConfig` | Jira integration configuration |
| `useJiraConfig` | Jira config CRUD |
| `useJiraSync` | Jira sync operations |
| `useAreaAccess` | Area access permissions |
| `useAreaDetection` | Automatic area detection based on route |
| `useAllocationRequests` | Team member allocation requests |
| `useIndexingStatus` | RAG indexing status |
| `useAdminUserCreation` | Admin user creation flow |
| `usePermissionService` | Permission checks (via service) |

## Key Services

| Service | Purpose |
|---------|---------|
| `governance-service.ts` | Base governance service |
| `governance-documents-service.ts` | Governance document management |
| `governance-indexing-service.ts` | Document indexing for RAG |
| `indexing-ignore-service.ts` | Manage ignored records during indexing |
| `jira-sync-service.ts` | Bidirectional Jira synchronization |
| `permission-service.ts` | Role-based access control (22k lines) |
| `user-area-access-service.ts` | Area access management |
| `user-project-access-service.ts` | Project access management |
| `user-profile-service.ts` | User profile CRUD |
| `admin-user-service.ts` | Admin user operations |
| `invitation-service.ts` | Team invitation management |
| `subscription-service.ts` | Subscription and billing management (27k lines) |
| `project-team-member-service.ts` | Project-team member associations |

## Pages

| Page | Route | File |
|------|-------|------|
| Governance Landing | `/governance` | `pages/areas/GovernanceLanding.tsx` |
| Permissions & Visibility | `/governance/permissions` | `pages/PermissionsVisibilityPage.tsx` |
| RAG Configuration | `/governance/rag-config` | `pages/governance/RagConfigPage.tsx` |
| Governance Documents | `/governance/documents` | `pages/governance/GovernanceDocumentsPage.tsx` |
| Governance Indexing | `/governance/indexing` | `pages/governance/GovernanceIndexingPage.tsx` |
| Jira Integrations | `/governance/jira` | `pages/governance/GovernanceJiraIntegrationsListPage.tsx` |
| Jira Config Form | `/governance/jira/:id` | `pages/governance/GovernanceJiraConfigFormPage.tsx` |
| Platform Settings | `/governance/settings` | `pages/governance/PlatformSettingsPage.tsx` |
| Access Control | `/governance/access-control` | `pages/governance/AccessControlPage.tsx` |
| Area Access | `/governance/area-access` | `pages/governance/AreaAccessPage.tsx` |
| Allocation Requests | `/governance/allocations` | `pages/governance/AllocationRequestsPage.tsx` |
| User Management | `/governance/users` | `pages/governance/UserManagementPage.tsx` |
| Meeting Share | `/governance/meeting-share` | `pages/governance/GovernanceMeetingSharePage.tsx` |
| Meeting Recording Config | `/governance/meeting-recording` | `pages/governance/MeetingRecordingConfigPage.tsx` |

## Context Providers

| Provider | File | Purpose |
|----------|------|---------|
| `AreaContext` | `src/contexts/AreaContext.tsx` | Current area state management |
| `AreaAccessContext` | `src/contexts/AreaAccessContext.tsx` | User area permissions |
| `GovernanceContext` | `src/contexts/GovernanceContext.tsx` | Governance state |
| `GovernanceProvider` | Wraps governance pages | Enables governance features |

## Permission System

The permission system (`permission-service.ts`, 22k lines) implements role-based access control:

- **Roles**: admin, manager, member, viewer
- **Resources**: projects, areas, features, tasks, documents, meetings
- **Actions**: create, read, update, delete, manage
- **Scope**: global, project-level, area-level
