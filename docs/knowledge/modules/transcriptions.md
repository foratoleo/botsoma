# Transcriptions Module

Created: 2026-04-10
Last Updated: 2026-04-10

## Overview

Transcription management with upload, processing, PDF extraction, and AI-powered analysis.

## Components

| Directory | Purpose |
|-----------|---------|
| `src/components/transcriptions/` (18 files) | Upload, display, document generation |

## Pages

| Page | Route | File |
|------|-------|------|
| Transcription List | `/transcriptions` | `pages/transcriptions/TranscriptionsPage.tsx` |
| Transcription Detail | `/transcriptions/:id` | `pages/transcriptions/TranscriptionDetailPage.tsx` |
| Upload | `/transcriptions/upload` | `pages/transcriptions/upload/` |
| Edit | `/transcriptions/:id/edit` | `pages/transcriptions/edit/` |

## Hooks

| Hook | Purpose |
|------|---------|
| `useMeetingTranscripts` | Transcripts for a meeting |
| `useMeetingWithTranscript` (10k) | Combined meeting + transcript data |

## Services

| Service | Purpose |
|---------|---------|
| `transcript-analysis-service.ts` (3k) | Transcript analysis |
| `pdf-extraction-service.ts` (18k) | PDF text extraction |
| `text-content-extractor.ts` (6k) | Text content extraction |

## Edge Functions

| Function | Purpose |
|----------|---------|
| `process-transcript` | Process uploaded transcript (largest, 16 subfiles) |
| `process-recall-transcript` | Process Recall.ai transcript |
| `transcribe-audio` | Audio to text via OpenAI Whisper |
| `extract-pdf` | PDF text extraction |
| `analyze-transcript` | AI transcript analysis |

## Utilities

| File | Purpose |
|------|---------|
| `src/lib/transcript-analyzer.ts` (4k) | Analysis logic |
| `src/lib/transcription-openai-service.ts` (12k) | OpenAI transcription |
| `src/lib/utils/transcript-format-detector.ts` (16k) | Detect transcript format |
| `supabase/functions/_shared/transcript-streaming-parser.ts` (4k) | Parse streaming transcripts |

## Transcription Data Model

```typescript
interface Transcript {
  id: string;
  meeting_id?: string;
  project_id: string;
  content: string;
  format: 'text' | 'vtt' | 'srt' | 'json' | 'pdf';
  source: 'upload' | 'recall' | 'whisper';
  duration_seconds?: number;
  created_at: string;
}
```

## Processing Flow

1. Upload: User uploads audio/video/text/PDF file
2. Storage: File stored in Supabase Storage or S3
3. Processing: Edge Function processes based on format:
   - Audio → OpenAI Whisper → Text
   - PDF → Text extraction
   - Text → Format detection and parsing
4. Storage: Processed transcript stored in database
5. AI: Optional analysis and document generation
