# Projects Module

Created: 2026-04-10
Last Updated: 2026-04-10

## Overview

Projects are the central organizing entity. ALL data in the system is scoped by `project_id`.

## Components

| Directory/File | Purpose |
|---------------|---------|
| `src/components/projects/` (44 files) | Project management UI |
| `src/components/projects/wizard/` | Project creation wizard |
| `src/components/common/ProjectSelector.tsx` | Project switcher dropdown |

## Pages

| Page | Route | File |
|------|-------|------|
| Project Selector (Home) | `/` | `pages/ProjectSelector.tsx` |
| Manage Projects | `/projects` | `pages/ManageProjects.tsx` |
| Project Details | `/projects/:id` | `pages/ProjectDetails.tsx` |
| Create Project | `/projects/new` | `pages/ProjectForm.tsx` |
| Edit Project | `/projects/:id/edit` | `pages/ProjectForm.tsx` |
| Project Wizard | `/projects/wizard` | `components/projects/wizard/ProjectCreationWizard.tsx` |

## Hooks

| Hook | Purpose |
|------|---------|
| `useProjectSelection` | Current project from context |
| `useProjects` | Project listing and CRUD |
| `useBulkProjectActions` | Bulk operations |
| `useDashboardStats` | Project dashboard metrics |

## Services

| Service | Purpose |
|---------|---------|
| `enhanced-project-service.ts` (42k) | Full project CRUD with wizard, import/export |
| `projects.ts` (13k) | Project utilities |
| `projects-import-export.ts` (6k) | Import/export functionality |
| `meeting-project-service.ts` (21k) | Project-meeting associations |

## Context

`ProjectSelectionContext` (`src/contexts/ProjectSelectionContext.tsx`):

```typescript
// ALWAYS access project this way:
const { selectedProject } = useProjectSelection();
const projectId = selectedProject?.id;

// NEVER use selectedProjectId (property doesn't exist)
```

## Project Data Model

```typescript
interface Project {
  id: string;
  name: string;
  description?: string;
  team_id: string;
  status: 'active' | 'archived' | 'on_hold';
  area?: 'planning' | 'development' | 'quality' | 'governance';
  created_at: string;
  updated_at: string;
}
```

## Project Isolation Pattern

ALL database queries enforce project isolation:

```typescript
const { data, error } = await supabase
  .from('any_table')
  .select('*')
  .eq('project_id', selectedProject?.id);
```

RLS (Row Level Security) policies in Supabase enforce this at the database level.
