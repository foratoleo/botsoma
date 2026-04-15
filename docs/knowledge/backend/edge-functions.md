# Supabase Edge Functions

Created: 2026-04-10
Last Updated: 2026-04-10

## Overview

80+ Edge Functions in `supabase/functions/`, built with Deno runtime. They handle AI operations, API endpoints, integrations, and background processing.

## Function Categories

### AI Document Generation

| Function | Purpose |
|----------|---------|
| `create-prd` | Generate Product Requirements Document |
| `create-user-story` | Generate User Stories |
| `create-meeting-notes` | Generate Meeting Notes |
| `create-technical-specs` | Generate Technical Specifications |
| `create-test-cases` | Generate Test Cases |
| `create-unit-tests` | Generate Unit Tests |
| `create-functional-specification` | Generate Functional Specification |
| `analyze-transcript` | Analyze meeting transcript |
| `generate-documents` | Generic document generation |
| `create-backlog-items` | Generate backlog items from content |
| `create-features` | Generate features from content |
| `create-tasks` | Generate tasks from content |

All use shared infrastructure from `_shared/document-generation/`.

### API Endpoints (REST)

| Function | Purpose |
|----------|---------|
| `api-projects` | Project CRUD API |
| `api-tasks` | Task CRUD API |
| `api-task-comments` | Task comments API |
| `api-task-details` | Task detail API |
| `api-task-status` | Task status update |
| `api-task-assign` | Task assignment |
| `api-tasks-list` | Task listing |
| `api-tasks-status-update` | Batch status update |
| `api-sprints` | Sprint CRUD API |
| `api-sprints-list` | Sprint listing |
| `api-sprint-details` | Sprint detail API |
| `api-meetings` | Meeting CRUD API |
| `api-features` | Feature CRUD API |
| `api-backlog-items` | Backlog CRUD API |
| `api-docs` | API documentation |
| `api-rag-search` | RAG search API |
| `api-team-members-list` | Team members listing |

### Data Normalization (for RAG)

| Function | Purpose |
|----------|---------|
| `get-task-normalized-record` | Normalize task for indexing |
| `get-meeting-normalized-record` | Normalize meeting for indexing |
| `get-feature-normalized-record` | Normalize feature for indexing |
| `get-backlog-normalized-record` | Normalize backlog item for indexing |
| `get-generated-document-normalized-record` | Normalize generated doc for indexing |

### Transcript & Recording Processing

| Function | Purpose |
|----------|---------|
| `process-transcript` | Process uploaded transcript (16 subfiles) |
| `process-recall-transcript` | Process Recall.ai transcript |
| `transcribe-audio` | Audio transcription via OpenAI |
| `extract-pdf` | PDF text extraction |
| `create-media-meeting` | Create meeting from media upload |
| `media-meeting-callback` | Media processing callback |

### Calendar Integration

| Function | Purpose |
|----------|---------|
| `ms-oauth-initiate` | Start Microsoft OAuth flow |
| `ms-oauth-callback` | Handle OAuth callback |
| `ms-token-refresh` | Refresh Microsoft access token |
| `ms-calendar-sync` | Sync calendar events |
| `ms-calendar-create-event` | Create calendar event |

### Recall.ai Integration

| Function | Purpose |
|----------|---------|
| `recall-bot-create` | Create Recall.ai meeting bot |
| `recall-bot-list` | List active bots |
| `recall-webhook` | Handle Recall.ai webhooks |
| `recall-transcript` | Fetch Recall.ai transcript |
| `recall-calendar-webhook` | Calendar webhook for Recall |
| `sync-recall-bot` | Sync bot status |
| `add-meet-recorder` | Add meeting recorder |

### Jira Integration

| Function | Purpose |
|----------|---------|
| `jira-sync-tasks` | Sync tasks with Jira |
| `jira-webhook` | Handle Jira webhooks |
| `jira-health` | Jira health check |
| `sync-jira-to-drai` | Jira to DRAI sync |
| `sync-drai-to-jira` | DRAI to Jira sync |

### GitHub Integration

| Function | Purpose |
|----------|---------|
| `sync-github-prs` | Sync GitHub pull requests |
| `sync-code-review-metrics` | Sync code review metrics |

### Storage & Upload

| Function | Purpose |
|----------|---------|
| `upload-to-s3` | Upload file to AWS S3 |
| `upload-to-presigned-s3` | Upload to S3 via presigned URL |
| `generate-presigned-download-url` | Generate presigned download URL |

### RAG & Search

| Function | Purpose |
|----------|---------|
| `api-rag-search` | RAG-powered search API |
| `planning-rag-query` | Planning-specific RAG queries |
| `planning-assistant` | AI planning assistant |
| `index-planning-docs` | Index planning documents |
| `index-single-document` | Index a single document |
| `process-indexing-queue` | Process indexing queue |

### Analysis & Testing

| Function | Purpose |
|----------|---------|
| `analyze-sprint` | Sprint analysis with AI |
| `accessibility-test` | Accessibility testing |
| `performance-test` | Performance testing |

### Other

| Function | Purpose |
|----------|---------|
| `suggest-backlog-item` | AI backlog suggestions |
| `service-call-to-markdown` | Convert service data to Markdown |
| `chat-style-guide` | Style guide chatbot |
| `generate-meeting-share-token` | Generate public share token |
| `get-shared-meeting` | Get shared meeting by token |
| `snapshot-active-sprints` | Snapshot sprint data |
| `tts-notification` | Text-to-speech notification |
| `admin-create-user` | Admin user creation |
| `admin-soft-delete-user` | Admin soft delete user |

## Request/Response Pattern

All API endpoints follow this pattern:

```typescript
// Request
interface EdgeFunctionRequest {
  content?: string;
  project_id: string;
  [key: string]: unknown;
}

// Response
interface EdgeFunctionResponse {
  success: boolean;
  data?: unknown;
  error?: string;
}
```

## Shared Infrastructure

Located in `supabase/functions/_shared/`:

| Module | Purpose |
|--------|---------|
| `document-generation/` | Shared types, utilities for doc generation |
| `indexing/` | RAG indexing utilities |
| `github/` | GitHub API helpers |
| `storage/` | S3 and Supabase Storage helpers |
| `pdf-extraction/` | PDF processing |
| `rag-context/` | RAG context building |
| `platform-settings/` | Platform configuration |
| `supabase/` | Supabase client utilities |
| `developer-matrix/` | Developer skill matrix |
| `cors.ts` | CORS headers |
| `validation.ts` | Request validation |
| `encryption.ts` | Data encryption |
| `batch-processor.ts` | Batch processing |
| `field-mapper.ts` | Field mapping (25k lines) |
| `api-response-builder.ts` | Standardized API responses |
| `database-utils.ts` | Database helper functions |
| `admin-user-types.ts` | Admin user type definitions |
| `external-service-*.ts` | External service utilities |
