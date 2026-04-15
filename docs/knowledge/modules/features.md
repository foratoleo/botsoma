# Features Module

Created: 2026-04-10
Last Updated: 2026-04-10

## Overview

Feature management with creation wizard, relationships/dependencies, file attachments, and AI generation.

## Components

| Directory | Purpose |
|-----------|---------|
| `src/components/features/` (28 files) | Feature management UI |
| `src/components/feature-creation/` (7 files) | Feature creation wizard with steps |

## Pages

| Page | Route | File |
|------|-------|------|
| Features List | `/planning/features/list` | `pages/planning/FeaturesListPage.tsx` |
| Feature Detail | `/planning/features/:id` | `pages/planning/FeatureDetailPage.tsx` |
| Create Feature | `/planning/features/new` | `pages/planning/FeatureCreationPage.tsx` |

## Hooks

| Hook | Purpose |
|------|---------|
| `useFeatures` (21k) | Feature CRUD with filtering |
| `useFeatureRelationships` (22k) | Dependency graph management |
| `useFeatureGeneration` (11k) | AI feature generation |
| `useFeatureAttachments` (11k) | File attachments |

## Services

| Service | Purpose |
|---------|---------|
| `feature-service.ts` (20k) | Feature CRUD |
| `feature-attachment-service.ts` (25k) | File attachments |
| `feature-conversion.ts` (13k) | Feature to task conversion |

## Edge Functions

| Function | Purpose |
|----------|---------|
| `api-features` | Feature CRUD API |
| `create-features` | AI feature generation |
| `get-feature-normalized-record` | Normalize for RAG |

## Feature Data Model

```typescript
interface Feature {
  id: string;
  project_id: string;
  name: string;
  description?: string;
  status: 'draft' | 'proposed' | 'accepted' | 'in_development' | 'completed' | 'rejected';
  priority: 'must_have' | 'should_have' | 'could_have' | 'wont_have';
  category?: string;
  tags?: string[];
  created_at: string;
  updated_at: string;
}
```

## Feature Relationships

Features can have relationships managed via `useFeatureRelationships`:
- `depends_on` - Feature A depends on Feature B
- `blocks` - Feature A blocks Feature B
- `relates_to` - General relationship
