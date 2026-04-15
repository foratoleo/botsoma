# Microsoft Calendar Integration

Created: 2026-04-10
Last Updated: 2026-04-10

## Overview

Integration with Microsoft Outlook/Calendar for event sync, OAuth authentication, and meeting recording via Recall.ai.

## Architecture

```
WORKFORCE  →  ms-oauth-initiate  →  Microsoft Login
                ↓
WORKFORCE  ←  ms-oauth-callback  ←  OAuth Token
                ↓
ms-calendar-sync  →  Microsoft Graph API  →  Calendar Events
                ↓
Calendar Events  →  Copy to Meeting  →  WORKFORCE Meetings
```

## Edge Functions

| Function | Purpose |
|----------|---------|
| `ms-oauth-initiate` | Start Microsoft OAuth flow |
| `ms-oauth-callback` | Handle OAuth callback, store tokens |
| `ms-token-refresh` | Refresh expired access tokens |
| `ms-calendar-sync` | Sync calendar events from Microsoft |
| `ms-calendar-create-event` | Create event in Microsoft Calendar |

## Shared Modules

Located in `supabase/functions/_shared/`:

| File | Purpose |
|------|---------|
| `ms-oauth-utils.ts` (17k) | OAuth flow utilities |
| `ms-oauth-scopes.ts` (2k) | OAuth scope definitions |
| `ms-calendar-types.ts` (12k) | Calendar type definitions |

## Frontend Components

| Component | Purpose |
|-----------|---------|
| `CalendarConnectionStatus` | Show connection status |
| `CalendarIntegrationCard` | Integration card |
| `CalendarSelectionList` | Select calendars to sync |
| `ConnectMicrosoftButton` | Start OAuth flow |
| `UpcomingRecordedMeetings` | Show upcoming meetings |
| `AttendeeCard` | Meeting attendee display |
| `CalendarEventHeroSection` | Event detail hero |
| `CopyToMeetingDialog` | Copy calendar event to meeting |

## Hooks

| Hook | Purpose |
|------|---------|
| `useCalendarConnection` (21k) | Full OAuth + sync lifecycle |
| `useCalendarEventDetail` | Event details |
| `useCopyCalendarEventToMeeting` (15k) | Copy event to meeting |
| `useMeetingRecordingSettings` | Recording configuration |

## Services

| Service | Purpose |
|---------|---------|
| `calendar-integration-service.ts` (39k) | Calendar CRUD, OAuth, sync |
| `calendar-event-to-meeting.ts` (20k) | Event to meeting conversion |

## Pages

| Page | Route |
|------|-------|
| Calendar Event Detail | `/calendar-events/:id` |
| Calendar OAuth Callback | `/auth/calendar-callback` |

## Utilities

| File | Purpose |
|------|---------|
| `src/lib/utils/meeting-calendar-utils.ts` (7k) | Calendar helper functions |
| `src/lib/utils/recurrence-dates.ts` (10k) | Recurrence pattern handling |
| `src/lib/utils/calendar-event-to-meeting.ts` (20k) | Event mapping |
