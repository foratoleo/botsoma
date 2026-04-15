# RAG (Retrieval Augmented Generation) System

Created: 2026-04-10
Last Updated: 2026-04-10

## Overview

The RAG system enables AI-powered search and chat over project documents, meetings, tasks, and other content. It uses vector embeddings stored in Supabase for semantic search.

## Architecture

```
Document Upload → Content Chunking → Embedding Generation → Vector Storage
                                                                    ↓
User Query → Embedding Generation → Vector Search → Context Assembly → LLM Response
```

## Frontend RAG Module

Located in `src/lib/rag/` (16 files):

| File | Purpose |
|------|---------|
| `index.ts` | Module exports |
| `chat-service.ts` (11k) | Chat with RAG context |
| `content-chunker.ts` (16k) | Split documents into chunks for embedding |
| `embedding-generator.ts` (4k) | Generate embeddings via OpenAI |
| `initial-indexer.ts` (17k) | Index existing project content |
| `prompt-builder.ts` (30k) | Build prompts with RAG context |
| `search-engine.ts` (6k) | Vector similarity search |
| `source-tracker.ts` (11k) | Track and display source documents |
| `streaming-client.ts` (3k) | Streaming response handling |
| `sync-orchestrator.ts` (18k) | Orchestrate data synchronization |
| `vector-storage.ts` (7k) | Supabase pgvector operations |
| `conversation-context.ts` (10k) | Conversation context management |
| `prompts/` | RAG-specific prompt templates |
| `templates/` | RAG response templates |

## RAG UI Components

| Component | File | Purpose |
|-----------|------|---------|
| Chat Container | `src/components/chat/ChatContainer.tsx` | Chat wrapper |
| Floating Chat | `src/components/chat/FloatingChatButton.tsx` | Persistent chat button |
| Message Bubble | `src/components/chat/MessageBubble.tsx` | Chat message display |
| Message Input | `src/components/chat/MessageInput.tsx` | Chat input field |
| Message List | `src/components/chat/MessageList.tsx` | Message history |
| Sources Panel | `src/components/chat/SourcesPanel.tsx` | Show source documents |
| Standalone Chat | `src/components/chat/standalone/` | Full-page chat |
| RAG Config | `src/components/rag/` | RAG configuration UI |

## RAG Configuration

Managed via Governance area (`/governance/rag-config`):

| Setting | Description |
|---------|-------------|
| Embedding model | OpenAI embedding model to use |
| Chunk size | Document chunk size for indexing |
| Chunk overlap | Overlap between chunks |
| Search results | Number of results to return |
| Temperature | LLM temperature for responses |
| System prompt | Custom system prompt for RAG responses |

## Edge Functions for RAG

| Function | Purpose |
|----------|---------|
| `api-rag-search` | RAG search API endpoint |
| `planning-rag-query` | Planning-specific queries |
| `planning-assistant` | AI planning assistant |
| `index-planning-docs` | Index planning documents |
| `index-single-document` | Index a single document |
| `process-indexing-queue` | Process pending index jobs |

## Shared RAG Infrastructure

Located in `supabase/functions/_shared/`:

| Directory/File | Purpose |
|---------------|---------|
| `indexing/` | Indexing utilities and helpers |
| `rag-context/` | Context building for RAG queries |

## Data Normalization for Indexing

Each entity type has a normalization function:

| Entity | Edge Function | Normalized Format |
|--------|--------------|-------------------|
| Tasks | `get-task-normalized-record` | Task details, status, assignee |
| Meetings | `get-meeting-normalized-record` | Meeting info, participants, transcript |
| Features | `get-feature-normalized-record` | Feature details, relationships |
| Backlog Items | `get-backlog-normalized-record` | Backlog item details |
| Generated Docs | `get-generated-document-normalized-record` | Document content |

## Key Hooks

| Hook | Purpose |
|------|---------|
| `useIndexingStatus` | Monitor indexing progress |
| `useCompanyKnowledge` | Knowledge base entries for context |

## Key Services

| Service | Purpose |
|---------|---------|
| `governance-indexing-service.ts` | Manage indexing operations |
| `indexing-ignore-service.ts` | Manage ignored records |
| `knowledge-selector.ts` | Knowledge base selection for context |
