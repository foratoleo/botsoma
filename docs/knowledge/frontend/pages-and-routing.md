# Pages and Routing

Created: 2026-04-10
Last Updated: 2026-04-10

## Routing Setup

Defined in `src/App.tsx` using React Router v6 with lazy-loaded page components. All pages use `lazyWithRetry()` for code splitting with automatic retry on chunk load failure.

## Route Structure

### Auth Routes (public)

| Route | Page Component | Purpose |
|-------|---------------|---------|
| `/login` | `Login` | User login |
| `/forgot-password` | `ForgotPassword` | Password reset request |
| `/reset-password` | `ResetPassword` | Password reset form |
| `/auth/calendar-callback` | `CalendarOAuthCallback` | Microsoft Calendar OAuth callback |

### Area Landing Pages

| Route | Page Component | Purpose |
|-------|---------------|---------|
| `/planning` | `PlanningLanding` | Planning area dashboard |
| `/development` | `DevelopmentLanding` | Development area dashboard |
| `/quality` | `QualityLanding` | Quality area dashboard |
| `/governance` | `GovernanceLanding` | Governance area dashboard |
| `/development/legacy-code` | `LegacyCodeLanding` | Legacy code management |

### Project Routes

| Route | Page Component | Purpose |
|-------|---------------|---------|
| `/` | `ProjectSelector` | Project selection (home) |
| `/projects` | `ManageProjects` | Project list management |
| `/projects/new` | `ProjectForm` | Create new project |
| `/projects/:id` | `ProjectDetails` | Project details |
| `/projects/:id/edit` | `ProjectForm` | Edit project |
| `/projects/wizard` | `ProjectCreationWizard` | Guided project creation |

### Team Routes

| Route | Page Component | Purpose |
|-------|---------------|---------|
| `/team` | `Teams` | Team list |
| `/team/new` | `CreateTeam` | Create team |
| `/team/:id` | `TeamMemberDetailPage` | Team member detail |
| `/team/expansion` | `TeamExpansionPage` | Team expansion |

### Sprint Routes

| Route | Page Component | Purpose |
|-------|---------------|---------|
| `/sprints` | `SprintList` | Sprint list |
| `/sprints/:id` | `SprintDetails` | Sprint details |
| `/sprints/new` | `SprintForm` | Create sprint |
| `/sprints/:id/tasks` | `SprintTasks` | Sprint tasks |
| `/sprints/:id/analytics` | `SprintAnalyticsPage` | Sprint analytics |

### Task Routes

| Route | Page Component | Purpose |
|-------|---------------|---------|
| `/tasks` | `Tasks` | Task list |
| `/tasks/suggested` | `SuggestedTasks` | AI suggested tasks |
| `/tasks/:id/edit` | `TaskEditPage` | Edit task |

### Meeting Routes

| Route | Page Component | Purpose |
|-------|---------------|---------|
| `/meetings` | `MeetingList` | Meeting list |
| `/meetings/new` | `MeetingCreate` | Create meeting |
| `/meetings/:id/edit` | `MeetingEdit` | Edit meeting |
| `/meetings/:id` | `MeetingDetailPage` | Meeting detail |
| `/meetings/share/:token` | `PublicMeetingSharePage` | Public meeting view |

### Transcription Routes

| Route | Page Component | Purpose |
|-------|---------------|---------|
| `/transcriptions` | `TranscriptionsPage` | Transcription list |
| `/transcriptions/:id` | `TranscriptionDetailPage` | Transcription detail |
| `/transcriptions/upload` | `TranscriptionUploadPage` | Upload transcription |
| `/transcriptions/:id/edit` | `TranscriptionEditPage` | Edit transcription |

### Document Routes

| Route | Page Component | Purpose |
|-------|---------------|---------|
| `/documents` | `DocumentsListingPage` | Document list |
| `/documents/:id/view` | `TaskDocumentViewerPage` | Document viewer |
| `/drafts` | `MyDraftsPage` | User's draft documents |

### Knowledge Routes

| Route | Page Component | Purpose |
|-------|---------------|---------|
| `/knowledge` | `KnowledgeListPage` | Knowledge base list |
| `/knowledge/new` | `KnowledgeFormPage` | Create knowledge entry |

### Chat Route

| Route | Page Component | Purpose |
|-------|---------------|---------|
| `/chat` | `ChatPage` | AI Chat (Guru) |

### Quality Routes

| Route | Page Component | Purpose |
|-------|---------------|---------|
| `/quality/test-cases` | `TestCasesPage` | Test cases |
| `/quality/bugs` | `BugReportsDashboard` | Bug dashboard |
| `/quality/bugs/list` | `BugListPage` | Bug list |
| `/quality/bugs/:id` | `BugDetailPage` | Bug detail |
| `/quality/automated-testing` | `AutomatedTestingDashboard` | Automated testing |
| `/quality/test-generator` | `TestGeneratorPage` | AI test generator |
| `/quality/accessibility-reports` | `AccessibilityReportsPage` | Accessibility reports |
| `/quality/accessibility-test` | `AccessibilityTestPage` | Accessibility test |
| `/quality/performance-reports` | `PerformanceReportsPage` | Performance reports |
| `/quality/performance-test` | `PerformanceTestPage` | Performance test |

### Development Routes

| Route | Page Component | Purpose |
|-------|---------------|---------|
| `/development/pull-requests` | `PullRequestsDashboard` | PR dashboard |
| `/development/pr-metrics` | `PRMetricsDashboard` | PR metrics |
| `/development/code-review` | `CodeReviewMetricsPage` | Code review metrics |
| `/development/dev-performance` | `DevPerformanceDashboard` | Dev performance |
| `/development/dev-performance/:id` | `DevPerformanceDetailPage` | Performance detail |
| `/development/dev-performance/compare` | `DevPerformanceComparePage` | Performance compare |
| `/development/refactor-insights` | `RefactorInsightsPage` | Refactor insights |
| `/development/repositories` | `RepositoriesListingPage` | Repository list |
| `/development/analysis-reports` | `AnalysisReportsPage` | Analysis reports |
| `/development/analysis-reports/:id` | `AnalysisReportDetailPage` | Report detail |
| `/development/ai-agents` | `AIAgentsListPage` | AI agents |
| `/development/ai-agents/:id` | `AIAgentConfigPage` | Agent config |
| `/development/style-guides` | `StyleGuidesPage` | Style guides |
| `/development/style-guides/:id` | `StyleGuideDetailPage` | Style guide detail |

### Legacy Code Routes

| Route | Page Component | Purpose |
|-------|---------------|---------|
| `/development/legacy-code` | `CodeHealthDashboard` | Code health |
| `/development/migrations` | `MigrationTrackerPage` | Migration tracker |
| `/development/tech-debt` | `TechDebtRegistryPage` | Tech debt registry |
| `/development/compatibility` | `CompatibilityPage` | Compatibility |
| `/development/refactoring-plans` | `RefactoringPlansPage` | Refactoring plans |

### Governance Routes

| Route | Page Component | Purpose |
|-------|---------------|---------|
| `/governance/permissions` | `PermissionsVisibilityPage` | Permissions |
| `/governance/rag-config` | `RagConfigPage` | RAG config |
| `/governance/documents` | `GovernanceDocumentsPage` | Governance docs |
| `/governance/indexing` | `GovernanceIndexingPage` | Indexing management |
| `/governance/jira` | `GovernanceJiraIntegrationsListPage` | Jira list |
| `/governance/jira/:id` | `GovernanceJiraConfigFormPage` | Jira config |
| `/governance/settings` | `PlatformSettingsPage` | Platform settings |
| `/governance/access-control` | `AccessControlPage` | Access control |
| `/governance/area-access` | `AreaAccessPage` | Area access |
| `/governance/allocations` | `AllocationRequestsPage` | Allocations |
| `/governance/users` | `UserManagementPage` | User management |
| `/governance/meeting-share` | `GovernanceMeetingSharePage` | Meeting share |

### Other Routes

| Route | Page Component | Purpose |
|-------|---------------|---------|
| `/dashboard` | `Dashboard` | Main dashboard |
| `/code` | `Code` | Code view |
| `/qa` | `QA` | QA overview |
| `/metrics` | `Metrics` | Metrics overview |
| `/upload-media` | `UploadMedia` | Media upload |
| `/demos` | `DemosPage` | Public demos |
| `/profile/edit` | `UserProfileEditPage` | User profile |
| `/admin/indexing` | `IndexingManagementPage` | Admin indexing |
| `*` | `NotFound` | 404 page |

## Route Guards

- `ProtectedRoute`: Requires authenticated user
- `AreaAccessGuard`: Requires access to specific area
- `MultiAreaAccessGuard`: Requires access to any of specified areas

## Navigation Configuration

Defined in `src/config/navigation.ts` as `navigationConfig` object, mapping areas to navigation items with routes, icons, and i18n keys.

Feature flag `USE_NEW_NAVIGATION` in `src/config/navigation.config.ts` controls navigation version.
