import json
import os
import re

import anthropic

_llm = None

_SYSTEM = """You are Bailey, a message router. Classify the user's message and return JSON only.

Available agents:
- "april": finance, expenses, income, budget, savings
- "lexie": ideas, notes, capturing thoughts
- "george": travel, trips, flights, hotels, bookings
- "arizona": emotional support, feelings, mood (positive or negative)
- "direct": casual chat, greetings, thanks, small talk, unclear intent

Return JSON only — no markdown:
{"agent": "<agent_name>", "reply": "<friendly reply if agent is direct, else empty string>"}

If agent is "direct", write a warm short reply in Thai (1-2 sentences).
If agent is a named agent, leave reply empty."""


def _get_llm():
    global _llm
    if _llm is None:
        _llm = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    return _llm


def _reset_llm():
    global _llm
    _llm = None


def classify(text: str, llm=None) -> tuple[str, str]:
    if llm is None:
        llm = _get_llm()
    try:
        message = llm.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            system=_SYSTEM,
            messages=[{"role": "user", "content": text}],
        )
        raw = message.content[0].text.strip()
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)
        result = json.loads(raw)
        return result["agent"], result.get("reply", "")
    except Exception:
        return "unknown", ""
