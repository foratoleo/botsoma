# Planning Area

Created: 2026-04-10
Last Updated: 2026-04-10

## Theme

- **Primary**: Dark Gold (#B8860B)
- **Accent**: #DAA520
- **Background**: rgba(255, 249, 230, 0.4)
- **CSS Variable**: `[data-area="planning"]`

## Navigation Items

| ID | Route | Icon | Description |
|----|-------|------|-------------|
| project-details | `/projects/:id` | FolderOpen | Project details and management |
| backlog | `/planning/backlog` | ListTodo | Backlog management |
| features | `/planning/features/list` | Boxes | Feature list |
| prds-user-stories | `/planning/prds-user-stories` | FileText | PRDs and user stories |
| sprints | `/sprints` | Layers | Sprint planning |
| tasks | `/tasks` | CheckSquare | Task management |
| team | `/team` | Users | Team management |
| meetings | `/meetings` | Calendar | Meeting scheduling |

## Key Components

| Directory/File | Purpose |
|---------------|---------|
| `src/components/backlog/` | BacklogBoard, BacklogColumn, BacklogItem, BacklogFilters, BacklogTable, BacklogToolbar |
| `src/components/backlog-creation/` | BacklogGenerationWizard, BacklogGenerationProgress |
| `src/components/backlog/statistics/` | AgeDistributionCard, BusinessValueMatrix, FeaturePipelineCard, HealthScoreCard |
| `src/components/features/` | Feature components (28 files) |
| `src/components/feature-creation/` | Feature creation wizard with steps |
| `src/components/sprints/` | Sprint management components |
| `src/components/sprint-analytics/` | Sprint analytics charts and dashboards (19 files) |
| `src/components/tasks/` | Task management, comments, attachments (40 files) |
| `src/components/meetings/` | Meeting management (30 files) |
| `src/components/kanban/` | Kanban board components |
| `src/components/planning/` | PlanningDocumentCreator |
| `src/components/projects/` | Project management (44 files) |

## Key Hooks

| Hook | Purpose |
|------|---------|
| `useBacklog` | Full backlog CRUD with filtering, sorting, pagination |
| `useBacklogDragDrop` | Drag-and-drop for backlog prioritization |
| `useBacklogGeneration` | AI-powered backlog generation |
| `useFeatures` | Feature CRUD with relationships |
| `useFeatureRelationships` | Feature dependency mapping |
| `useFeatureGeneration` | AI-powered feature generation |
| `useFeatureAttachments` | File attachments on features |
| `useSprints` / `useSprintDetails` | Sprint management |
| `useBatchSprintCreation` | Create multiple sprints at once |
| `useTasks` | Task CRUD and filtering |
| `useBatchTaskOperations` | Bulk task operations |
| `useGenerateTasks` | AI-powered task generation |
| `useMeetings` | Meeting CRUD |
| `useMeetingMutations` | Meeting create/update/delete (27k lines, complex) |
| `useMeetingAssets` | Meeting file attachments |
| `useMeetingShareToken` | Public meeting sharing |

## Key Services

| Service | Purpose |
|---------|---------|
| `backlog-service.ts` | Backlog CRUD and conversion |
| `backlog-conversion.ts` | Convert backlog items to features/tasks |
| `feature-service.ts` | Feature CRUD |
| `feature-attachment-service.ts` | Feature file attachments |
| `feature-conversion.ts` | Feature to task conversion |
| `sprint-service.ts` | Sprint CRUD and analytics |
| `task-service.ts` | Task CRUD, status updates |
| `task-attachment-service.ts` | Task file attachments |
| `comment-service.ts` | Task comments |
| `meeting-service.ts` | Meeting CRUD (31k lines, comprehensive) |
| `meeting-participant-service.ts` | Meeting participant management |
| `meeting-share-service.ts` | Meeting sharing |
| `meeting-recorder-service.ts` | Meeting recording |

## Pages

| Page | Route | File |
|------|-------|------|
| Planning Landing | `/planning` | `pages/areas/PlanningLanding.tsx` |
| Planning Documents | `/planning/prds-user-stories` | `pages/planning/PlanningDocumentsPage.tsx` |
| Features List | `/planning/features/list` | `pages/planning/FeaturesListPage.tsx` |
| Feature Detail | `/planning/features/:id` | `pages/planning/FeatureDetailPage.tsx` |
| Feature Creation | `/planning/features/new` | `pages/planning/FeatureCreationPage.tsx` |
| Backlog Hub | `/planning/backlog` | `pages/backlog/BacklogHubPage.tsx` |
| Backlog Statistics | `/planning/backlog/statistics` | `pages/backlog/BacklogStatisticsPage.tsx` |
| Backlog Board | `/planning/backlog/board` | `pages/backlog/BacklogBoardPage.tsx` |
| Sprint List | `/sprints` | `pages/SprintList.tsx` |
| Sprint Details | `/sprints/:id` | `pages/sprints/SprintDetails.tsx` |
| Tasks | `/tasks` | `pages/Tasks.tsx` |
| Meetings | `/meetings` | `pages/MeetingList.tsx` |
| Meeting Create | `/meetings/new` | `pages/MeetingCreate.tsx` |
