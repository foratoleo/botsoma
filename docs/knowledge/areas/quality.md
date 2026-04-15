# Quality / Testing Area

Created: 2026-04-10
Last Updated: 2026-04-10

## Theme

- **Primary**: Bronze (#CD7F32)
- **Accent**: #D4A574
- **Background**: rgba(255, 245, 235, 0.4)
- **CSS Variable**: `[data-area="testing"]` or `[data-area="quality"]`

## Key Components

| Directory | Purpose |
|-----------|---------|
| `src/components/bugs/` | Bug tracking UI (12 files) |
| `src/components/quality/` | Quality management (6 files) |
| `src/components/test-generator/` | Test generation wizard (10 files) |

### Bug Tracking Components

| Component | Purpose |
|-----------|---------|
| `BugCard.tsx` | Bug card display |
| `BugCreateSheet.tsx` | Bug creation slide-over |
| `BugForm.tsx` | Bug form with validation |
| `BugList.tsx` | Bug listing with filters |
| `BugFilters.tsx` | Filter controls for bugs |
| `BugAnalysisDialog.tsx` | AI-powered bug analysis |
| `BugPriorityBadge.tsx` | Priority badge (P0-P4) |
| `BugSeverityBadge.tsx` | Severity badge (critical, major, minor) |
| `BugStatusBadge.tsx` | Status badge (open, in_progress, resolved) |

## Key Hooks

| Hook | Purpose |
|------|---------|
| `useBugs` | Bug listing with filtering and pagination |
| `useBugById` | Single bug fetch by ID |
| `useBugCreate` | Bug creation mutation |
| `useBugStatistics` | Bug statistics aggregation |
| `useAccessibilityTest` | Accessibility test execution and results |
| `useLoadTest` | Performance/load testing |
| `useContentValidation` | Content quality validation |

## Key Services

| Service | Purpose |
|---------|---------|
| `bug-service.ts` | Bug CRUD with filtering (18k lines, comprehensive) |
| `voice-task-generator.ts` | Voice-driven task generation |
| `voice-task-service.ts` | Voice task management |

## Pages

| Page | Route | File |
|------|-------|------|
| Quality Landing | `/quality` | `pages/areas/QualityLanding.tsx` |
| Test Cases | `/quality/test-cases` | `pages/quality/TestCasesPage.tsx` |
| Bug Reports Dashboard | `/quality/bugs` | `pages/quality/BugReportsDashboard.tsx` |
| Bug List | `/quality/bugs/list` | `pages/quality/BugListPage.tsx` |
| Bug Detail | `/quality/bugs/:id` | `pages/quality/BugDetailPage.tsx` |
| Automated Testing | `/quality/automated-testing` | `pages/quality/AutomatedTestingDashboard.tsx` |
| Test Generator | `/quality/test-generator` | `pages/quality/TestGeneratorPage.tsx` |
| Accessibility Reports | `/quality/accessibility-reports` | `pages/quality/AccessibilityReportsPage.tsx` |
| Accessibility Test | `/quality/accessibility-test` | `pages/quality/AccessibilityTestPage.tsx` |
| Performance Reports | `/quality/performance-reports` | `pages/quality/PerformanceReportsPage.tsx` |
| Performance Test | `/quality/performance-test` | `pages/quality/PerformanceTestPage.tsx` |
| QA | `/qa` | `pages/QA.tsx` |

## Bug Data Model

```
Bug {
  id: string
  project_id: string          // Always filtered by project
  title: string
  description: string
  severity: 'critical' | 'major' | 'moderate' | 'minor' | 'trivial'
  priority: 'P0' | 'P1' | 'P2' | 'P3' | 'P4'
  status: 'open' | 'in_progress' | 'resolved' | 'closed' | 'reopened'
  assignee_id?: string
  reporter_id?: string
  tags?: string[]
  created_at: string
  updated_at: string
}
```
