# Custom Hooks Reference

Created: 2026-04-10
Last Updated: 2026-04-10

## Overview

120+ custom hooks in `src/hooks/`, built on TanStack Query v5 for server state management. Every hook follows the pattern of `useQuery` for reads and `useMutation` for writes.

## Hook Categories

### Project & Team

| Hook | File | Purpose |
|------|------|---------|
| `useProjectSelection` | via `ProjectSelectionContext` | Current selected project |
| `useProjects` | `project-hooks.ts` | Project listing and CRUD |
| `useBulkProjectActions` | `useBulkProjectActions.ts` | Bulk project operations |
| `useMemberProjects` | `useMemberProjects.ts` | Projects by team member |
| `useTeams` | via `TeamContext` | Team listing |
| `useTeamMembers` | `useTeamMembers.ts` | Team member listing |
| `useMemberAllocation` | `useMemberAllocation.ts` | Member allocation status |
| `useAllocationRequests` | `useAllocationRequests.ts` | Allocation request CRUD |

### Tasks & Sprints

| Hook | File | Purpose |
|------|------|---------|
| `useTasks` | `useTasks.ts` | Task listing with filters |
| `useBatchTaskOperations` | `useBatchTaskOperations.ts` | Bulk task operations |
| `useGenerateTasks` | `useGenerateTasks.ts` | AI task generation |
| `useSprints` | `useSprints.ts` | Sprint listing |
| `useSprintDetails` | `useSprintDetails.ts` | Single sprint data |
| `useBatchSprintCreation` | `useBatchSprintCreation.ts` | Create multiple sprints |
| `useSprintAnalytics` | `useSprintAnalytics.ts` | Sprint metrics |

### Backlog & Features

| Hook | File | Purpose |
|------|------|---------|
| `useBacklog` | `useBacklog.ts` | Full backlog management (26k lines) |
| `useBacklogDragDrop` | `useBacklogDragDrop.ts` | Drag-and-drop prioritization |
| `useBacklogGeneration` | `useBacklogGeneration.ts` | AI backlog generation |
| `useFeatures` | `useFeatures.ts` | Feature CRUD (21k lines) |
| `useFeatureRelationships` | `useFeatureRelationships.ts` | Feature dependency graph |
| `useFeatureGeneration` | `useFeatureGeneration.ts` | AI feature generation |
| `useFeatureAttachments` | `useFeatureAttachments.ts` | Feature file attachments |

### Meetings & Transcriptions

| Hook | File | Purpose |
|------|------|---------|
| `useMeetings` | `useMeetings.ts` | Meeting listing |
| `useMeetingDetails` | `useMeetingDetails.ts` | Single meeting data |
| `useMeetingMutations` | `useMeetingMutations.ts` | Meeting CRUD (27k lines, most complex) |
| `useMeetingAssets` | `useMeetingAssets.ts` | Meeting file attachments |
| `useMeetingShareToken` | `useMeetingShareToken.ts` | Public sharing |
| `useMeetingWithTranscript` | `useMeetingWithTranscript.ts` | Meeting + transcript combined |
| `useMeetingTranscripts` | `useMeetingTranscripts.ts` | Transcripts for a meeting |
| `useCopyCalendarEventToMeeting` | `useCopyCalendarEventToMeeting.ts` | Calendar event to meeting conversion |
| `useMeetingRecordingSettings` | `useMeetingRecordingSettings.ts` | Recording configuration |

### Documents & AI

| Hook | File | Purpose |
|------|------|---------|
| `useDocuments` | `useDocuments.ts` | Document listing (25k lines) |
| `useDocumentActions` | `documents/useDocumentActions.ts` | Document CRUD actions |
| `useDocumentFilters` | `documents/useDocumentFilters.ts` | Filter state management |
| `useDocumentPagination` | `documents/useDocumentPagination.ts` | Pagination logic |
| `useDocumentSelection` | `documents/useDocumentSelection.ts` | Selection state |
| `useDocumentSort` | `documents/useDocumentSort.ts` | Sort state |
| `useDocumentApproval` | `useDocumentApproval.ts` | Document approval workflow |
| `useDocumentUpdate` | `useDocumentUpdate.ts` | Document update mutation |
| `useDocumentContent` | `useDocumentContent.ts` | Document content fetch |
| `useDocumentTypes` | `useDocumentTypes.ts` | Document type management |
| `useCentralizedDocumentTypes` | `useCentralizedDocumentTypes.ts` | Centralized type definitions |

### Development & Code

| Hook | File | Purpose |
|------|------|---------|
| `useDevPerformance` | `useDevPerformance.ts` | Developer performance metrics |
| `useAnalysisReports` | `useAnalysisReports.ts` | Code analysis reports |
| `useCodeReviewMetrics` | `useCodeReviewMetrics.ts` | Code review statistics |
| `useGitRepositories` | `useGitRepositories.ts` | Repository management (16k lines) |
| `useGitHubPRMetrics` | `useGitHubPRMetrics.ts` | PR metrics |
| `useGitHubPullRequests` | `useGitHubPullRequests.ts` | PR listing |
| `useGitHubAccountMappings` | `useGitHubAccountMappings.ts` | GitHub-to-team mapping |

### Governance & Access

| Hook | File | Purpose |
|------|------|---------|
| `useAreaAccess` | `useAreaAccess.ts` | Area permissions |
| `useAreaDetection` | `useAreaDetection.ts` | Auto-detect area from route |
| `useGovernance` | `useGovernance.ts` | Governance state |
| `useGovernanceJiraConfig` | `useGovernanceJiraConfig.ts` | Jira config |
| `useJiraSync` | `useJiraSync.ts` | Jira sync operations |
| `useIndexingStatus` | `useIndexingStatus.ts` | RAG indexing status |
| `usePermissionService` | via `useAreaAccess.ts` | Permission checks |

### Calendar Integration

| Hook | File | Purpose |
|------|------|---------|
| `useCalendarConnection` | `useCalendarConnection.ts` | Microsoft Calendar OAuth and sync (20k lines) |
| `useCalendarEventDetail` | `useCalendarEventDetail.ts` | Calendar event details |

### Quality & Testing

| Hook | File | Purpose |
|------|------|---------|
| `useBugs` | `useBugs.ts` | Bug listing |
| `useBugById` | `useBugById.ts` | Single bug |
| `useBugCreate` | `useBugCreate.ts` | Bug creation |
| `useBugStatistics` | `useBugStatistics.ts` | Bug statistics |
| `useAccessibilityTest` | `useAccessibilityTest.ts` | Accessibility testing |
| `useLoadTest` | `useLoadTest.ts` | Load testing |

### Utility Hooks

| Hook | File | Purpose |
|------|------|---------|
| `useDebounce` | `useDebounce.ts` | Debounce values |
| `useI18n` | `useI18n.ts` | Internationalization |
| `use-toast` | `use-toast.ts` | Toast notifications |
| `use-mobile` | `use-mobile.tsx` | Mobile detection |

## Hook Pattern

```typescript
// Standard TanStack Query hook pattern
export function useEntity(entityId: string) {
  const { selectedProject } = useProjectSelection();

  return useQuery({
    queryKey: ['entity', entityId, selectedProject?.id],
    queryFn: () => fetchEntity(entityId, selectedProject?.id),
    enabled: !!entityId && !!selectedProject?.id,
  });
}

// Standard mutation hook pattern
export function useCreateEntity() {
  const queryClient = useQueryClient();
  const { selectedProject } = useProjectSelection();

  return useMutation({
    mutationFn: (data: CreateEntityInput) => createEntity(data, selectedProject?.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['entities'] });
      toast.success('Entity created');
    },
  });
}
```

## Important Notes

- ALL hooks filter by `selectedProject?.id` (never use `selectedProjectId` - property doesn't exist)
- Query keys follow pattern: `['entityName', id?, ...filters]`
- Mutations always invalidate related queries on success
- Toast notifications used for user feedback via `sonner`
