# AI Document Generation Pipeline

Created: 2026-04-10
Last Updated: 2026-04-10

## Architecture (v2.0 - Edge Function Based)

```
User Input (transcript/content)
    ↓
generateDocumentAPI() [src/lib/services/document-generation-service.ts]
    ↓
Supabase Edge Function [supabase/functions/create-{type}/]
    ↓
OpenAI Responses API
    ↓
Save to generated_documents table
    ↓
Track in ai_interactions table (server-side)
    ↓
Return response to client
```

## Supported Document Types

| Type | Edge Function | Output |
|------|--------------|--------|
| `prd` | `create-prd` | Product Requirements Document |
| `user-stories` | `create-user-story` | User Stories |
| `meeting-notes` | `create-meeting-notes` | Structured Meeting Notes |
| `technical-specs` | `create-technical-specs` | Technical Specifications |
| `test-cases` | `create-test-cases` | Test Cases |
| `unit-tests` | `create-unit-tests` | Unit Tests |
| `analyze-transcript` | `analyze-transcript` | Transcript Analysis |
| `functional-specification` | `create-functional-specification` | Functional Specification |
| `tasks` | `create-tasks` | Generated Tasks |

## Entry Point

```typescript
// src/lib/services/document-generation-service.ts
import { generateDocumentAPI } from '@/lib/services/document-generation-service';

const result = await generateDocumentAPI(
  'user-stories',        // Document type string
  transcriptContent,     // Input content (transcript, text)
  projectId,            // Project ID
  meetingTranscriptId,  // Optional: link to meeting transcript
  userId                // Optional: user tracking
);

if (result.success) {
  console.log('Generated:', result.document);
  console.log('Response ID:', result.response_id); // For conversation continuity
}
```

## Edge Function Request Format

```typescript
interface EdgeFunctionRequest {
  content: string;                  // Transcript or input content
  project_id: string;              // Project identifier
  meeting_transcript_id?: string;  // Optional transcript reference
  user_id?: string;                // Optional user tracking
  system_prompt?: string;          // Optional custom system prompt
  user_prompt?: string;            // Optional custom user prompt
  previous_response_id?: string;   // For conversation continuity (Responses API)
  model?: string;                  // Optional model override
  temperature?: number;            // Optional temperature override
  token_limit?: number;            // Optional token limit override
}
```

## Edge Function Response Format

```typescript
interface EdgeFunctionResponse {
  success: boolean;
  document?: string;        // Generated document (Markdown)
  response_id?: string;     // OpenAI response ID for continuity
  error?: string;           // Error message if failed
}
```

## Shared Infrastructure

Located in `supabase/functions/_shared/document-generation/`:

| File | Purpose |
|------|---------|
| `types.ts` | TypeScript interfaces for all document types |
| Shared utilities | Retry logic, model selection, token tracking |

## Key Files in Frontend

| File | Purpose |
|------|---------|
| `src/lib/services/document-generation-service.ts` | Main API wrapper (46k) |
| `src/lib/openai.ts` | Legacy OpenAI integration (55k, deprecated for doc gen) |
| `src/lib/openai-secure.ts` | Secure OpenAI wrapper |
| `src/config/openai.ts` | OpenAI configuration (29k) |
| `src/components/planning/PlanningDocumentCreator.tsx` | Document creation UI |
| `src/components/transcriptions/DocumentGenerator.tsx` | Transcription-based generation |
| `src/components/transcriptions/RelatedDocuments.tsx` | Related documents display |

## Conversation Continuity

Uses OpenAI Responses API `previous_response_id` to maintain conversation context across multiple document generations:

```typescript
// First generation
const result1 = await generateDocumentAPI('prd', content, projectId);

// Follow-up with continuity
const result2 = await generateDocumentAPI('user-stories', content, projectId, undefined, undefined, {
  previous_response_id: result1.response_id
});
```

## Token Tracking

All AI operations are automatically tracked in `ai_interactions` table:
- Token usage (prompt + completion)
- Model used
- Cost estimation
- Response ID for continuity
- User and project association

## Model Selection

Automatic model selection based on complexity:
- **Complex** (PRD, technical specs): GPT-4o
- **Simple** (meeting notes, summaries): GPT-4o-mini

## Template System

- Templates in `src/prompts/document-templates/` use Handlebars syntax
- Version control with `is_current_version` flag in database
- Templates loaded by Edge Functions, not frontend
- `src/lib/prompt-templates.ts` (38k) manages template system
- `src/lib/prompt-storage.ts` (17k) handles template storage

## Related Lib Files

| File | Purpose |
|------|---------|
| `src/lib/document-pipeline.ts` | Document processing pipeline (44k) |
| `src/lib/document-model-selector.ts` | Model selection logic (25k) |
| `src/lib/sequential-document-generator.ts` | Sequential generation (24k) |
| `src/lib/sequential-cost-optimizer.ts` | Cost optimization (28k) |
| `src/lib/sequential-caching-system.ts` | Generation caching (39k) |
| `src/lib/sequential-error-recovery.ts` | Error recovery (17k) |
| `src/lib/conversation-tracking.ts` | Conversation tracking (39k) |
| `src/lib/conversation-tracking-integration.ts` | Tracking integration (19k) |
| `src/lib/cost-management.ts` | Cost management (29k) |
| `src/lib/cost-monitoring-dashboard.tsx` | Cost monitoring UI (25k) |
| `src/lib/token-optimization.ts` | Token optimization (25k) |
| `src/lib/quality-gates.ts` | Quality validation (17k) |
| `src/lib/quality-validation.ts` | Quality checks (25k) |
| `src/lib/quality-metrics-calculator.ts` | Quality metrics (25k) |
