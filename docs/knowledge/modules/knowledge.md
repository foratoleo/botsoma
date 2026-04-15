# Knowledge Base Module

Created: 2026-04-10
Last Updated: 2026-04-10

## Overview

Company and project knowledge management with entries that feed into RAG context for AI operations.

## Components

| Directory | Purpose |
|-----------|---------|
| `src/components/knowledge/` (7 files) | Knowledge entry UI |

### Key Component

| Component | Purpose |
|-----------|---------|
| `KnowledgeEntryDetail` | View knowledge entry with content |

## Pages

| Page | Route | File |
|------|-------|------|
| Knowledge List | `/knowledge` | `pages/KnowledgeListPage.tsx` |
| Create Entry | `/knowledge/new` | `pages/KnowledgeFormPage.tsx` |
| Edit Entry | `/knowledge/:id/edit` | `pages/KnowledgeFormPage.tsx` |

## Hooks

| Hook | Purpose |
|------|---------|
| `useCompanyKnowledge` (7k) | Knowledge entries CRUD and selection |

## Services

| Service | Purpose |
|---------|---------|
| `knowledge-selector.ts` (15k) | Knowledge selection for RAG context |

## Data Model

```typescript
interface KnowledgeEntry {
  id: string;
  project_id: string;
  title: string;
  content: string;
  category?: string;
  tags?: string[];
  is_company_wide?: boolean;
  created_by?: string;
  created_at: string;
  updated_at: string;
}
```

## Knowledge Types

Defined in `src/types/knowledge.ts` (3k).

## Knowledge in RAG

Knowledge entries are indexed into the RAG system and used as context for AI operations:
- Chat responses reference relevant knowledge
- Document generation can incorporate knowledge
- Search includes knowledge entries in results

## Knowledge Selector Service

The `knowledge-selector.ts` service manages which knowledge entries are relevant for a given query, using:
- Tag matching
- Category filtering
- Semantic similarity via RAG
