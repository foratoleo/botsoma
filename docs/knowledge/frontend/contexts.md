# React Context Providers

Created: 2026-04-10
Last Updated: 2026-04-10

## Context Hierarchy

The app wraps providers in this order (outermost to innermost):

```
BrowserRouter
  └── QueryClientProvider        (TanStack Query)
      └── AuthProvider           (AuthContext)
          └── TeamProvider       (TeamContext)
              └── ProjectSelectionProvider  (ProjectSelectionContext)
                  └── AreaProvider          (AreaContext)
                      └── AreaAccessProvider (AreaAccessContext)
                          └── GovernanceProvider (GovernanceContext)
                              └── ErrorMonitorProvider (ErrorMonitorContext)
                                  └── App Routes
```

## Context Details

### AuthContext
- **File**: `src/contexts/AuthContext.tsx`
- **Purpose**: Supabase Auth state management
- **Provides**: `user`, `session`, `loading`, `signUp`, `signIn`, `signOut`

### TeamContext
- **File**: `src/contexts/TeamContext.tsx`
- **Purpose**: Current team selection and team data
- **Provides**: `currentTeam`, `teams`, `setCurrentTeam`, `loading`

### ProjectSelectionContext
- **File**: `src/contexts/ProjectSelectionContext.tsx`
- **Purpose**: Current project selection - central to all data operations
- **Provides**: `selectedProject`, `setSelectedProject`, `projects`, `loading`
- **IMPORTANT**: Use `selectedProject?.id` (NOT `selectedProjectId`)

### AreaContext
- **File**: `src/contexts/AreaContext.tsx`
- **Purpose**: Current workflow area detection and state
- **Provides**: `currentArea`, `setCurrentArea`
- **Areas**: `planning`, `development`, `testing`, `quality`, `governance`
- **Auto-detects**: Area from current route path

### AreaAccessContext
- **File**: `src/contexts/AreaAccessContext.tsx`
- **Purpose**: User's access permissions for each area
- **Provides**: `areaAccess`, `hasAccess(area)`, `loading`

### GovernanceContext
- **File**: `src/contexts/GovernanceContext.tsx`
- **Purpose**: Governance-specific state
- **Provides**: `governanceState`, governance operations

### ErrorMonitorContext
- **File**: `src/contexts/ErrorMonitorContext.tsx`
- **Purpose**: Global error tracking and display
- **Provides**: `errors`, `addError`, `clearErrors`, `showModal`

### ProjectConversationContext
- **File**: `src/contexts/ProjectConversationContext.tsx`
- **Purpose**: AI conversation continuity per project
- **Provides**: `conversationId`, `responseId`, `setResponseId`

### TaskSyncStatusContext
- **File**: `src/contexts/TaskSyncStatusContext.tsx`
- **Purpose**: Real-time task sync status
- **Provides**: `syncStatus`, `lastSynced`

## Usage Pattern

```typescript
// Access context in components
const { selectedProject } = useProjectSelection();
const { currentArea } = useArea();
const { user } = useAuth();
const { t } = useI18n('namespace');

// Always filter by project
const projectId = selectedProject?.id;
```
