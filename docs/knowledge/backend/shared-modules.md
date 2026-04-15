# Backend Shared Modules

Created: 2026-04-10
Last Updated: 2026-04-10

## Overview

Located in `supabase/functions/_shared/` (35 files/directories), these modules are shared across Edge Functions.

## Directory Structure

```
_shared/
├── document-generation/     # AI doc generation shared code
├── developer-matrix/        # Developer skill matrix
├── github/                  # GitHub API helpers (13 files)
├── indexing/                 # RAG indexing utilities (13 files)
├── pdf-extraction/          # PDF processing (6 files)
├── platform-settings/       # Platform config (5 files)
├── rag-context/             # RAG context building (6 files)
├── storage/                 # S3/Supabase Storage (10 files)
├── supabase/                # Supabase client (4 files)
├── admin-user-types.ts      # Admin user type definitions (9k)
├── api-response-builder.ts  # Standardized API responses (4k)
├── batch-processor.ts       # Batch processing (11k)
├── cors.ts                  # CORS headers (0.2k)
├── database-utils.ts        # Database helpers (2k)
├── encryption.ts            # Data encryption (4k)
├── external-service-database.ts  # External service DB ops (16k)
├── external-service-types.ts     # External service types (10k)
├── external-service-utils.ts     # External service utils (12k)
├── field-mapper.ts          # Field mapping (25k)
├── jira-alerts.ts           # Jira alert system (17k)
├── jira-client.ts           # Jira API client (12k)
├── jira-db-service-optimized.ts  # Optimized Jira DB (17k)
├── jira-db-service.ts       # Jira DB operations (19k)
├── jira-error-handler.ts    # Jira error handling (17k)
├── jira-logger.ts           # Jira logging (12k)
├── jira-metrics.ts          # Jira metrics (16k)
├── ms-calendar-types.ts     # Microsoft Calendar types (12k)
├── ms-oauth-scopes.ts       # MS OAuth scopes (2k)
├── ms-oauth-utils.ts        # MS OAuth utilities (17k)
├── recall-bot-types.ts      # Recall.ai types (21k)
├── response-formatter.ts    # Response formatting (2k)
├── transcript-streaming-parser.ts  # Streaming parser (4k)
└── validation.ts            # Request validation (7k)
```

## Key Modules

### CORS (`cors.ts`)

Standard CORS headers for all Edge Functions. Every function must include these in responses.

### Document Generation (`document-generation/`)

Shared types and utilities used by all `create-*` Edge Functions:
- Request/response type definitions
- Error handling patterns
- Retry logic with exponential backoff
- Token usage tracking
- Model selection logic

### Field Mapper (`field-mapper.ts`, 25k)

Maps fields between external systems (Jira, GitHub) and internal data models. Handles:
- Field type conversion
- Default values
- Required field validation
- Custom field mapping

### External Services (`external-service-*.ts`)

Base classes and utilities for external API integrations:
- `external-service-types.ts` (10k) - Common types
- `external-service-utils.ts` (12k) - HTTP clients, retry, auth
- `external-service-database.ts` (16k) - Database operations for sync

### Validation (`validation.ts`, 7k)

Request validation utilities for Edge Functions:
- Input sanitization
- Type checking
- Required field validation
- Project ID verification

### Encryption (`encryption.ts`, 4k)

Encryption utilities for sensitive data:
- OAuth token encryption
- API key storage
- Secure credential handling

### Batch Processor (`batch-processor.ts`, 11k)

Generic batch processing for operations that need to handle large datasets:
- Configurable batch size
- Progress tracking
- Error recovery
- Rate limiting

### Storage (`storage/`)

S3 and Supabase Storage helpers:
- Presigned URL generation
- File upload handling
- Download URL management
- Storage bucket management
