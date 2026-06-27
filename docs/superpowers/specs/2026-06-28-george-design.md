# George — Travel Logistics Agent

**Date:** 2026-06-28
**Scope:** agent-team `agents/george.py` + studio `/george` skill + Notion schema

## Overview

George handles travel logistics across two surfaces:
- **agent-team (LINE/Telegram):** quick capture and lookup via pattern matching
- **studio (desktop):** deep trip planning with Notion sync

Both surfaces share the same Notion Travel databases.

---

## Notion Schema

### Trips DB (`NOTION_TRIPS_DB_ID`)

| Property | Type | Options |
|---|---|---|
| Title | Title | e.g. "Bali Jul 2026" |
| Destination | Text | |
| Start / End | Date range | |
| Status | Select | Planning / Booked / Done |
| Budget | Number | THB |
| Travelers | Number | |

### Bookings DB (`NOTION_BOOKINGS_DB_ID`)

| Property | Type | Options |
|---|---|---|
| Title | Title | e.g. "Wyndham Bali" |
| Trip | Relation | → Trips DB |
| Type | Select | Flight / Hotel / Activity / Other |
| Date | Date | |
| Amount | Number | THB |
| Status | Select | Pending / Confirmed / Cancelled |
| Note | Text | |

Both DBs live under the existing `agent-studio` parent page.

---

## agent-team: `agents/george.py`

Pattern matching only — no LLM. Three intents:

### 1. New trip
Trigger: "เที่ยว", "ไป", "ทริป" + destination keyword, no amount  
Action: create page in Trips DB  
Reply: trip name + Notion URL

### 2. Log booking
Trigger: "จอง", "ตั๋ว", "โรงแรม", "บิน" + numeric amount  
Parse: type (Flight/Hotel/Activity/Other), date, amount  
Link to: most recent trip, or trip matched by name mention  
Reply: booking title + amount + trip it was linked to

### 3. Lookup
Trigger: "ดู", "มีอะไร", "checklist", or `george: <trip-name>`  
Action: fetch trip + all linked bookings  
Reply: trip summary + booking list

Unknown intent → ask for clarification, no LLM fallback.

---

## studio: `/george` skill

### `/george`
Opens a new planning session. Claude asks for destination, dates, travelers, and budget, then helps build itinerary, packing list, and budget breakdown. When the user confirms, Claude pushes the trip (and any bookings agreed on) to Notion via MCP.

### `/george <trip-name>`
Loads that trip's context from Notion (properties + all bookings), then opens a session to continue planning — e.g. check what's booked, what's missing, remaining budget.

Notion writes happen via Notion MCP directly from the desktop skill, not through the agent-team server.

---

## `core/notion.py` Extensions

Four new methods on `NotionClient`:

```python
create_trip(destination, start, end, status, budget, travelers) → str   # page_id
add_booking(trip_id, title, type, date, amount, status, note) → str     # page_id
get_trip(name_or_id) → dict    # trip properties + bookings list
list_trips(status=None) → list[dict]
```

New env vars (add to Render + local `.env`):
- `NOTION_TRIPS_DB_ID`
- `NOTION_BOOKINGS_DB_ID`

---

## Tests

- `tests/test_george.py` — unit tests for intent detection and `handle()`: new trip, booking, lookup, unknown
- `tests/test_notion.py` — unit tests for 4 new NotionClient methods with mocked client

No integration tests (consistent with existing lexie pattern).
