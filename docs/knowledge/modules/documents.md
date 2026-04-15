# Documents Module

Created: 2026-04-10
Last Updated: 2026-04-10

## Overview

AI-generated document management with versioning, approval workflows, content rendering, and filtering.

## Components

| Directory | Purpose |
|-----------|---------|
| `src/components/documents/` (24 files) | Document management UI |
| `src/components/documents/DocumentManager/cards/` | Document cards |
| `src/components/documents/DocumentManager/dialogs/` | Document dialogs |
| `src/components/documents/renderers/` | Content renderers |
| `src/components/planning/PlanningDocumentCreator.tsx` | Document creation from planning |
| `src/components/transcriptions/DocumentGenerator.tsx` | Generation from transcriptions |
| `src/components/transcriptions/RelatedDocuments.tsx` | Related documents display |

## Pages

| Page | Route | File |
|------|-------|------|
| Documents Listing | `/documents` | `pages/DocumentsListingPage.tsx` |
| Document Viewer | `/documents/:id/view` | `pages/TaskDocumentViewerPage.tsx` |
| My Drafts | `/drafts` | `pages/MyDraftsPage.tsx` |
| Planning Documents | `/planning/prds-user-stories` | `pages/planning/PlanningDocumentsPage.tsx` |

## Hooks

| Hook | Purpose |
|------|---------|
| `useDocuments` (26k) | Document listing with advanced filtering |
| `useDocumentActions` | CRUD action handlers |
| `useDocumentFilters` | Filter state management |
| `useDocumentPagination` | Pagination logic |
| `useDocumentSelection` | Multi-select state |
| `useDocumentSort` | Sort state |
| `useDocumentApproval` (10k) | Approval workflow |
| `useDocumentUpdate` | Update mutation |
| `useDocumentContent` | Content fetch |
| `useDocumentTypes` | Document type management |
| `useCentralizedDocumentTypes` | Centralized type definitions |
| `useDescriptionGeneration` | AI description generation |
| `useEnhanceDescription` | AI description enhancement |

## Services

| Service | Purpose |
|---------|---------|
| `document-generation-service.ts` (46k) | Main generation API |
| `document-service.ts` (15k) | Document CRUD |
| `document-approval-service.ts` (16k) | Approval workflow |
| `document-suggestion-service.ts` (9k) | AI suggestions |
| `document-task-generator.ts` (8k) | Generate tasks from docs |
| `document-content-extractor.ts` (3k) | Content extraction |
| `document-content-fetcher.ts` (3k) | Content fetching |
| `ai-document-generation.ts` (2k) | AI generation wrapper |

## Document Types

Supported types (from centralized config):

| Type | Label |
|------|-------|
| `prd` | Product Requirements Document |
| `user-stories` | User Stories |
| `meeting-notes` | Meeting Notes |
| `technical-specs` | Technical Specifications |
| `test-cases` | Test Cases |
| `unit-tests` | Unit Tests |
| `functional-specification` | Functional Specification |
| `analyze-transcript` | Transcript Analysis |

## Edge Functions

| Function | Purpose |
|----------|---------|
| `create-prd` | Generate PRD |
| `create-user-story` | Generate User Stories |
| `create-meeting-notes` | Generate Meeting Notes |
| `create-technical-specs` | Generate Technical Specs |
| `create-test-cases` | Generate Test Cases |
| `create-unit-tests` | Generate Unit Tests |
| `create-functional-specification` | Generate Functional Spec |
| `analyze-transcript` | Analyze Transcript |
| `get-generated-document-normalized-record` | Normalize for RAG |

## Document Data Model

```typescript
interface GeneratedDocument {
  id: string;
  project_id: string;
  meeting_transcript_id?: string;
  document_type: string;
  title: string;
  content: string;         // Markdown content
  status: 'draft' | 'review' | 'approved' | 'rejected';
  version: number;
  is_current_version: boolean;
  created_by?: string;
  response_id?: string;    // OpenAI response ID for continuity
  created_at: string;
  updated_at: string;
}
```

## Approval Workflow

1. Document generated → status: `draft`
2. Submitted for review → status: `review`
3. Reviewer approves → status: `approved`
4. Or rejects → status: `rejected` (can resubmit)

## Versioning

Documents support versioning via `version` and `is_current_version` fields. Only the current version is displayed by default.
