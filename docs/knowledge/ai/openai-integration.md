# OpenAI Integration

Created: 2026-04-10
Last Updated: 2026-04-10

## Integration Points

### 1. Document Generation (v2.0 - Active)

Uses Edge Functions for server-side API key management.

**Key files:**
- `src/lib/services/document-generation-service.ts` - Main wrapper
- `src/config/openai.ts` - Configuration and model selection
- `supabase/functions/create-*/index.ts` - Edge Functions

**API:** OpenAI Responses API (`/v1/responses`) with `previous_response_id` for continuity

### 2. Chat / RAG (Active)

Uses OpenAI for conversational AI with RAG context.

**Key files:**
- `src/lib/rag/chat-service.ts` (11k) - Chat with context
- `src/lib/rag/streaming-client.ts` (3k) - Streaming responses
- `src/components/chat/` - Chat UI components
- `src/pages/ChatPage.tsx` - Chat page

### 3. Transcription (Active)

Uses OpenAI Whisper API for audio transcription.

**Key files:**
- `src/lib/transcription-openai-service.ts` (12k) - Transcription service
- `supabase/functions/transcribe-audio/` - Edge Function

### 4. Transcript Analysis (Active)

Analyzes meeting transcripts for insights.

**Key files:**
- `src/lib/transcript-analyzer.ts` (4k) - Analysis logic
- `src/lib/services/transcript-analysis-service.ts` (3k) - Service layer
- `supabase/functions/analyze-transcript/` - Edge Function

### 5. Legacy Frontend Direct Calls (Deprecated)

**DO NOT USE** for new document generation. Still used for task creation workflows only.

- `src/lib/openai.ts` (55k) - Deprecated for document generation
- Still contains `generateDocumentsWithOpenAI()` used for task creation

## Configuration

```typescript
// src/config/openai.ts (29k)
// Contains:
// - Model selection logic
// - Temperature defaults per document type
// - Token limits
// - Cost estimation
// - Retry configuration
```

## Cost Management System

| File | Purpose |
|------|---------|
| `src/lib/cost-management.ts` (29k) | Cost tracking and budgets |
| `src/lib/cost-monitoring-dashboard.tsx` (25k) | Cost monitoring UI |
| `src/lib/sequential-cost-optimizer.ts` (28k) | Cost optimization strategies |
| `src/lib/token-optimization.ts` (25k) | Token reduction techniques |
| `src/lib/performance-comparison.ts` (32k) | Performance vs cost analysis |

## Conversation Tracking

| File | Purpose |
|------|---------|
| `src/lib/conversation-tracking.ts` (39k) | Core tracking system |
| `src/lib/conversation-tracking-integration.ts` (19k) | Integration layer |
| `src/lib/conversation-context-utils.ts` (26k) | Context utilities |
| `src/contexts/ProjectConversationContext.tsx` | React context for conversations |

## Quality System

| File | Purpose |
|------|---------|
| `src/lib/quality-gates.ts` (17k) | Quality gate checks |
| `src/lib/quality-validation.ts` (25k) | Validation logic |
| `src/lib/quality-metrics-calculator.ts` (25k) | Metric calculations |
| `src/lib/pattern-quality-assessment.ts` (25k) | Pattern assessment |
| `src/lib/predictive-quality-analysis.ts` (24k) | Predictive quality |

## Prompt System

| File | Purpose |
|------|---------|
| `src/lib/prompts.ts` (5k) | Prompt definitions |
| `src/lib/prompt-loader.ts` (4k) | Prompt loading |
| `src/lib/prompt-storage.ts` (17k) | Prompt storage |
| `src/lib/prompt-templates.ts` (38k) | Template management |
| `src/lib/system-prompt-integration.ts` (15k) | System prompt builder |
| `src/lib/template-based-enhancement.ts` (21k) | Template enhancement |
| `src/lib/template-integration.ts` (17k) | Template integration |
| `src/config/transcription-prompts.ts` (3k) | Transcription prompts |
| `src/prompts/` | Prompt template files |

## API Key Management

- **Server-side**: Edge Functions use Supabase secrets (never exposed to client)
- **Client-side (legacy)**: `VITE_OPENAI_API_KEY` in `.env` (deprecated for doc gen)
- **User-configured**: Users can set their own API key in settings

## Database Tables

| Table | Purpose |
|-------|---------|
| `ai_interactions` | Token usage, cost tracking, response IDs |
| `generated_documents` | Generated documents with versioning |
