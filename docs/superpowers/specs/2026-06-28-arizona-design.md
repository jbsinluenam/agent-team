# Arizona — Emotional Support Agent

**Date:** 2026-06-28
**Scope:** agent-team `agents/arizona.py` + Notion Mood Log DB + studio `/arizona` skill

## Overview

Arizona is a warm emotional support agent. She listens first, validates feelings, then gently helps the user examine thought patterns — using Active Listening (Carl Rogers) as the base, with light CBT reframing when the user is stuck in negative loops.

Two surfaces:
- **agent-team (LINE/Telegram):** quick support + mood logging via Haiku LLM
- **studio (desktop):** deeper conversations with Notion recall

---

## Notion Schema

### Mood Log DB (`NOTION_MOOD_LOG_DB_ID`)

| Property | Type | Notes |
|---|---|---|
| Title | Title | auto: "2026-06-28 เครียดเรื่องงาน" |
| Entry | Text | raw message from user |
| Response | Text | Arizona's reply |
| Tags | Multi-select | งาน, ความสัมพันธ์, สุขภาพ, ครอบครัว, เงิน, ตัวเอง, อื่นๆ |
| Mood | Select | positive / neutral / negative |
| Date | Date | log date |

Lives under the existing `agent-studio` parent page.

---

## agent-team: `agents/arizona.py`

### Intents

Pattern matching decides intent before any LLM call.

**1. Recall**
Trigger keywords: "ย้อนดู", "recall", "ดูเรื่อง", "ที่ผ่านมา"
- Query Notion Mood Log filtered by tag matching the topic keyword
- LLM summarizes pattern from fetched entries
- Reply: summary of past moods/themes

**2. Support** (default — everything else)
- Single LLM call (Haiku) returns JSON: `{response, tags, mood}`
- Log entry + response to Notion
- Reply: `response`

### LLM Call (Support intent)

**Model:** `claude-haiku-4-5-20251001`

**System prompt:**
```
You are Arizona, an emotional support companion. Your approach:
- Active Listening first: reflect back what you heard, name the emotion, validate before advising
- CBT-lite: if the user is caught in a negative thought loop, gently surface the pattern ("ดูเหมือนความคิดนี้วนซ้ำอยู่ — มีส่วนไหนที่อาจไม่ใช่ความจริงทั้งหมดไหม?")
- Never diagnose, prescribe, or replace professional help
- Always reply in Thai
- Keep responses warm, concise (2-4 sentences), human

Return JSON only:
{
  "response": "<your reply>",
  "tags": ["<tag1>", "<tag2>"],  // from: งาน, ความสัมพันธ์, สุขภาพ, ครอบครัว, เงิน, ตัวเอง, อื่นๆ
  "mood": "<positive|neutral|negative>"
}
```

**User message:** the raw text after stripping the "Arizona:" prefix

### LLM Call (Recall intent)

**System prompt:**
```
You are Arizona. The user wants to reflect on past emotional entries about a topic.
Summarize the themes, patterns, and any shifts in mood you notice.
Reply in Thai, warm and insightful. 3-5 sentences.
```

**User message:** list of past entries (title + entry text, max 10)

### Interface

```python
handle(text: str, client: NotionClient | None = None) -> str
_detect_intent(text: str) -> str  # "recall" | "support"
_extract_recall_topic(text: str) -> str
_call_llm_support(text: str) -> dict  # {response, tags, mood}
_call_llm_recall(entries: list[dict]) -> str
```

---

## NotionClient Extensions

Add to `core/notion.py`:

```python
log_mood(entry: str, response: str, tags: list[str], mood: str, date: str) -> str  # page_id
recall_moods(topic: str, limit: int = 10) -> list[dict]  # [{title, entry, tags, mood, date}]
```

Env var: `NOTION_MOOD_LOG_DB_ID`

---

## bot.py

Wire Arizona the same way as George:

```python
import agents.arizona as arizona
# in handle_message:
if agent_name == "arizona":
    return arizona.handle(text)
```

---

## studio: `/arizona` skill

Conversational — no structured intent matching needed. The LLM handles the whole conversation.

Uses the same Haiku model + system prompt. Can also recall from Notion via MCP when user asks.

---

## Dependencies

- `anthropic` Python package (new — not currently in requirements.txt)
- `ANTHROPIC_API_KEY` env var (new — add to .env.example + Render)
- `NOTION_MOOD_LOG_DB_ID` env var (new)

---

## Testing

Follow the existing pattern (`unittest.mock`):
- Mock `anthropic.Anthropic` client
- Mock `NotionClient`
- Test: detect_intent, extract_recall_topic, handle (support + recall + no entries)
- Test: NotionClient.log_mood, recall_moods
- Test: bot.py routing to arizona

---

## Out of Scope

- Multi-turn conversation memory within a session
- Crisis detection / escalation
- Sentiment trend charts
