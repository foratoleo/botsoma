# Frontend Services

Created: 2026-04-10
Last Updated: 2026-04-10

## Overview

65+ service files in `src/lib/services/`, each encapsulating business logic and Supabase operations. Services are called by hooks, never directly from components.

## Service Categories

### Core Services

| Service | File Size | Purpose |
|---------|-----------|---------|
| `document-generation-service.ts` | 46k | Edge Function wrapper for AI document generation |
| `enhanced-project-service.ts` | 42k | Project CRUD with wizard, import/export |
| `calendar-integration-service.ts` | 39k | Microsoft Calendar OAuth, sync, events |
| `permission-service.ts` | 23k | Role-based access control system |
| `team-member-service.ts` | 29k | Team member management with invitations |
| `subscription-service.ts` | 27k | Subscription and billing |
| `meeting-service.ts` | 31k | Meeting CRUD with recording, sharing |

### Task & Sprint Services

| Service | File Size | Purpose |
|---------|-----------|---------|
| `task-service.ts` | 15k | Task CRUD, status, assignment |
| `task-attachment-service.ts` | 25k | Task file attachments |
| `sprint-service.ts` | 15k | Sprint CRUD and analytics |
| `comment-service.ts` | 9k | Task comments |

### Document Services

| Service | File Size | Purpose |
|---------|-----------|---------|
| `document-generation-service.ts` | 46k | Main entry point for all document generation |
| `document-service.ts` | 15k | Document CRUD |
| `document-approval-service.ts` | 16k | Document approval workflow |
| `document-suggestion-service.ts` | 9k | AI-powered document suggestions |
| `document-task-generator.ts` | 8k | Generate tasks from documents |
| `document-content-extractor.ts` | 3k | Extract content from documents |
| `document-content-fetcher.ts` | 3k | Fetch document content |
| `ai-document-generation.ts` | 2k | AI generation wrapper |

### Feature & Backlog Services

| Service | File Size | Purpose |
|---------|-----------|---------|
| `feature-service.ts` | 20k | Feature CRUD |
| `feature-attachment-service.ts` | 25k | Feature file attachments |
| `feature-conversion.ts` | 13k | Feature to task conversion |
| `backlog-service.ts` | 15k | Backlog CRUD |
| `backlog-conversion.ts` | 10k | Backlog item conversion |

### Team & User Services

| Service | File Size | Purpose |
|---------|-----------|---------|
| `team-service.ts` | 17k | Team CRUD |
| `invitation-service.ts` | 20k | Team invitation management |
| `user-area-access-service.ts` | 16k | User area access permissions |
| `user-project-access-service.ts` | 17k | User project access |
| `user-profile-service.ts` | 6k | User profile management |
| `admin-user-service.ts` | 14k | Admin user operations |
| `project-team-member-service.ts` | 14k | Project-team member associations |

### Integration Services

| Service | File Size | Purpose |
|---------|-----------|---------|
| `jira-sync-service.ts` | 19k | Bidirectional Jira sync |
| `github-pr-service.ts` | 12k | GitHub PR operations |
| `github-pr-metrics-service.ts` | 24k | PR metrics calculation |
| `github-sync-config-service.ts` | 10k | GitHub sync configuration |
| `git-repository-service.ts` | 25k | Git repository management |
| `code-review-metrics-service.ts` | 26k | Code review metrics |

### Analysis & Performance Services

| Service | File Size | Purpose |
|---------|-----------|---------|
| `analysis-reports-service.ts` | 21k | Code analysis reports |
| `dev-performance-service.ts` | 21k | Developer performance metrics |

### Meeting & Transcription Services

| Service | File Size | Purpose |
|---------|-----------|---------|
| `meeting-participant-service.ts` | 20k | Meeting participants |
| `meeting-participant-mapper.ts` | 12k | Map participants to users |
| `meeting-recorder-service.ts` | 15k | Meeting recording |
| `meeting-share-service.ts` | 9k | Public meeting sharing |
| `pdf-extraction-service.ts` | 18k | PDF text extraction |
| `transcript-analysis-service.ts` | 3k | Transcript analysis |
| `tts-service.ts` | 5k | Text-to-speech |
| `tts-notification-agent.ts` | 9k | TTS notifications |

### Other Services

| Service | File Size | Purpose |
|---------|-----------|---------|
| `style-guide-service.ts` | 18k | Code style guide management |
| `agent-config-service.ts` | 8k | AI agent configuration |
| `bug-service.ts` | 18k | Bug tracking CRUD |
| `knowledge-selector.ts` | 15k | Knowledge base selection |
| `governance-documents-service.ts` | 4k | Governance document management |
| `governance-indexing-service.ts` | 5k | Document indexing |
| `indexing-ignore-service.ts` | 12k | Ignored records management |
| `download-url-service.ts` | 10k | Presigned download URLs |
| `project-conversation-service.ts` | 15k | AI conversation management |
| `suggestions-service.ts` | 5k | AI suggestions |
| `tag-suggestion-service.ts` | 5k | Tag suggestions |
| `description-synthesizer.ts` | 3k | Description generation |
| `voice-task-generator.ts` | 7k | Voice-driven task generation |
| `voice-task-service.ts` | 8k | Voice task management |
| `text-content-extractor.ts` | 6k | Text extraction from files |
| `task-content-service.ts` | 2k | Task content management |

## Service Pattern

```typescript
// Standard service pattern
export class EntityService {
  static async getAll(projectId: string): Promise<Entity[]> {
    const { data, error } = await supabase
      .from('entities')
      .select('*')
      .eq('project_id', projectId)
      .order('created_at', { ascending: false });

    if (error) throw new Error(error.message);
    return data;
  }

  static async create(input: CreateEntityInput): Promise<Entity> {
    const { data, error } = await supabase
      .from('entities')
      .insert(input)
      .select()
      .single();

    if (error) throw new Error(error.message);
    return data;
  }
}
```

## Key Integration: document-generation-service.ts

The main entry point for all AI document generation via Edge Functions:

```typescript
import { generateDocumentAPI } from '@/lib/services/document-generation-service';

const result = await generateDocumentAPI(
  'user-stories',        // Document type
  transcriptContent,     // Input content
  projectId,            // Project context
  meetingTranscriptId,  // Optional transcript ID
  userId                // Optional user ID
);
```

Supported document types: `prd`, `user-stories`, `meeting-notes`, `technical-specs`, `test-cases`, `unit-tests`, `analyze-transcript`, `functional-specification`, `tasks`
