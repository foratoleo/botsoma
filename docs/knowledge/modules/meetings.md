# Meetings Module

Created: 2026-04-10
Last Updated: 2026-04-10

## Overview

Meeting management with scheduling, recording, sharing, participants, calendar integration, and AI-powered analysis.

## Components

| Directory | Purpose |
|-----------|---------|
| `src/components/meetings/` (30 files) | Full meeting management UI |
| `src/components/calendar-integration/` (8 files) | Calendar-related meeting components |
| `src/components/calendar-events/` (5 files) | Calendar event displays |

## Pages

| Page | Route | File |
|------|-------|------|
| Meeting List | `/meetings` | `pages/MeetingList.tsx` |
| Create Meeting | `/meetings/new` | `pages/MeetingCreate.tsx` |
| Edit Meeting | `/meetings/:id/edit` | `pages/MeetingEdit.tsx` |
| Meeting Detail | `/meetings/:id` | `pages/meetings/MeetingDetailPage.tsx` |
| Public Share | `/meetings/share/:token` | `pages/meetings/PublicMeetingSharePage.tsx` |
| Upload Media | `/upload-media` | `pages/UploadMedia.tsx` |
| Recording Config | `/governance/meeting-recording` | `pages/governance/MeetingRecordingConfigPage.tsx` |
| Meeting Share Mgmt | `/governance/meeting-share` | `pages/governance/GovernanceMeetingSharePage.tsx` |

## Hooks

| Hook | Purpose |
|------|---------|
| `useMeetings` | Meeting listing |
| `useMeetingDetails` | Single meeting data |
| `useMeetingMutations` (27k) | Create/update/delete - most complex hook |
| `useMeetingAssets` | File attachments |
| `useMeetingShareToken` | Public sharing |
| `useMeetingWithTranscript` | Meeting + transcript combined |
| `useMeetingTranscripts` | Transcripts for meeting |
| `useMeetingRecordingSettings` | Recording config |
| `useCopyCalendarEventToMeeting` (15k) | Calendar event to meeting |
| `useMeetingViewPreference` | View mode preference |
| `useCalendarEventDetail` | Calendar event details |

## Services

| Service | Purpose |
|---------|---------|
| `meeting-service.ts` (31k) | Meeting CRUD - largest service |
| `meeting-participant-service.ts` (20k) | Participant management |
| `meeting-participant-mapper.ts` (12k) | Map participants to users |
| `meeting-recorder-service.ts` (15k) | Meeting recording |
| `meeting-share-service.ts` (9k) | Public sharing |
| `calendar-integration-service.ts` (39k) | Calendar integration |

## Edge Functions

| Function | Purpose |
|----------|---------|
| `api-meetings` | Meeting CRUD API |
| `create-media-meeting` | Create from media upload |
| `media-meeting-callback` | Media processing callback |
| `generate-meeting-share-token` | Generate share token |
| `get-shared-meeting` | Get shared meeting by token |

## Meeting Data Model

```typescript
interface Meeting {
  id: string;
  project_id: string;
  title: string;
  description?: string;
  date: string;
  start_time?: string;
  end_time?: string;
  location?: string;
  meeting_type?: string;
  status: 'scheduled' | 'in_progress' | 'completed' | 'cancelled';
  recording_url?: string;
  transcript_id?: string;
  organizer_id?: string;
  participants?: MeetingParticipant[];
  created_at: string;
}
```

## Recurring Meetings

| File | Purpose |
|------|---------|
| `src/types/recurring-meeting.ts` | Recurring meeting types |
| `src/lib/utils/recurrence-dates.ts` (10k) | Recurrence pattern calculations |

## Meeting Templates

| File | Purpose |
|------|---------|
| `src/lib/utils/meeting-template-resolver.ts` (6k) | Template resolution |
| `src/lib/utils/meeting-template-variables.ts` (10k) | Template variable substitution |
| `src/lib/constants/meeting-type-templates.ts` (8k) | Meeting type templates |
