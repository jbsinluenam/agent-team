# Bailey Layer 3 — LLM Fallback Design

**Date:** 2026-06-28
**Scope:** `router/layer3.py` (new) + `router/bailey.py` (modify dispatch) + `tests/test_layer3.py` (new) + `tests/test_bailey.py` (update)

## Overview

Bailey currently routes messages via two layers:
1. **Prefix** — explicit agent name prefix ("Arizona: ...", "April: ...")
2. **Keywords** — keyword matching per agent

When both fail, Bailey returns "unknown" and replies with a confusion message. Layer 3 adds an LLM fallback: Haiku classifies the intent and either routes to the correct agent or responds directly for casual/unclear messages.

---

## Flow

```
dispatch(raw)
  → strip_prefix         # "Arizona: ..." → ("arizona", text)
  → route (keywords)     # "เครียด" → "arizona"
  → layer3.classify(raw) # "ขอบคุณ" → ("direct", "ยินดีเลย!")
  → fallback "unknown"   # only if layer3 raises an exception
```

---

## layer3.classify()

**File:** `router/layer3.py`

**Interface:**
```python
classify(text: str, llm=None) -> tuple[str, str]
# returns (agent_name, reply_text)
# agent_name: "april" | "lexie" | "george" | "arizona" | "direct" | "unknown"
# reply_text: non-empty only when agent_name == "direct"
```

**Model:** `claude-haiku-4-5-20251001`

**System prompt:**
```
You are Bailey, a message router. Classify the user's message and return JSON only.

Available agents:
- "april": finance, expenses, income, budget, savings
- "lexie": ideas, notes, capturing thoughts
- "george": travel, trips, flights, hotels, bookings
- "arizona": emotional support, feelings, mood (positive or negative)
- "direct": casual chat, greetings, thanks, small talk, unclear intent

Return JSON only — no markdown:
{"agent": "<agent_name>", "reply": "<friendly reply if agent is direct, else empty string>"}

If agent is "direct", write a warm short reply in Thai (1-2 sentences).
If agent is a named agent, leave reply empty.
```

**Error handling:** if the LLM call raises any exception or JSON parse fails → return `("unknown", "")` silently (fallback to existing "ไม่แน่ใจ" message)

**Singleton pattern:** module-level `_llm` with `_get_llm()` / `_reset_llm()` — same pattern as `arizona.py`

---

## bailey.py changes

`dispatch()` gains one branch — after `route()` returns "unknown":

```python
def dispatch(raw: str) -> tuple[str, str]:
    agent_name, text = strip_prefix(raw)
    if agent_name is None:
        agent_name = route(raw)
        text = raw
    if agent_name == "unknown":
        agent_name, text = layer3.classify(raw)
    return agent_name, text
```

`handle_message()` in `bot.py` requires no changes — `("direct", reply_text)` falls through to the existing fallback `return f"⏳ {agent_name.capitalize()} ..."`. Instead, `dispatch()` returns `("direct", reply_text)` and `handle_message()` needs a new branch:

```python
if agent_name == "direct":
    return text  # text IS the reply from layer3
```

---

## bot.py change

One new branch in `handle_message()`:

```python
if agent_name == "direct":
    return text
```

---

## Testing

**`tests/test_layer3.py`** — unit tests with mocked Anthropic client:
- LLM returns `{"agent": "arizona", "reply": ""}` → `("arizona", "")`
- LLM returns `{"agent": "direct", "reply": "ยินดีเลย!"}` → `("direct", "ยินดีเลย!")`
- LLM raises exception → `("unknown", "")`
- LLM returns malformed JSON → `("unknown", "")`
- LLM returns markdown-fenced JSON → stripped and parsed correctly

**`tests/test_bailey.py`** — integration:
- Message with no keyword match → `layer3.classify` called
- Layer3 returns `("arizona", "")` → dispatches to arizona
- Layer3 returns `("direct", "สวัสดี!")` → bot returns that text

**`tests/test_bot.py`** — one new test:
- `dispatch` returns `("direct", "ยินดีเลย!")` → `handle_message` returns `"ยินดีเลย!"`

---

## Out of Scope

- Layer 3 does not override successful keyword matches
- Layer 3 does not maintain conversation history
- Layer 3 does not handle multi-turn "direct" conversations
