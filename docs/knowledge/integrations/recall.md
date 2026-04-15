# Recall.ai Meeting Bot Integration

Created: 2026-04-10
Last Updated: 2026-04-10

## Overview

Integration with Recall.ai for automated meeting recording and transcription. Recall.ai bots join meetings, record audio/video, and produce transcripts.

## Architecture

```
WORKFORCE  →  recall-bot-create  →  Recall.ai API  →  Bot joins meeting
                                                          ↓
Recall.ai  →  recall-webhook     →  WORKFORCE      ←  Recording/Transcript ready
                ↓
recall-transcript  →  Process transcript  →  Store in database
```

## Edge Functions

| Function | Purpose |
|----------|---------|
| `recall-bot-create` | Create a Recall.ai bot for a meeting |
| `recall-bot-list` | List active Recall.ai bots |
| `recall-webhook` | Receive Recall.ai event webhooks |
| `recall-transcript` | Fetch transcript from Recall.ai |
| `recall-calendar-webhook` | Calendar webhook for auto-recording |
| `sync-recall-bot` | Sync bot status |
| `add-meet-recorder` | Add recorder to existing meeting |

## Shared Types

| File | Purpose |
|------|---------|
| `supabase/functions/_shared/recall-bot-types.ts` (21k) | Recall.ai type definitions |

## Frontend Components

| Component | Purpose |
|-----------|---------|
| `UpcomingRecordedMeetings` | Show meetings with bots |
| `CalendarConnectionStatus` | Bot connection status |

## Hooks

| Hook | Purpose |
|------|---------|
| `useMeetingRecordingSettings` | Configure recording preferences |
| `useCalendarConnection` | Bot management via calendar |

## Services

| Service | Purpose |
|---------|---------|
| `meeting-recorder-service.ts` (15k) | Recording CRUD |
| `calendar-integration-service.ts` (39k) | Calendar-bot coordination |

## Recording Flow

1. User connects Microsoft Calendar
2. Calendar events synced to WORKFORCE
3. User configures auto-recording for specific calendars
4. Recall.ai bot created for matching events
5. Bot joins meeting, records, produces transcript
6. Webhook notifies WORKFORCE of completion
7. Transcript processed and stored
