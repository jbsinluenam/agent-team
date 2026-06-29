import json
import os
import re

import anthropic

_llm = None

_SYSTEM = """You are Bailey, a message router. Classify the user's message and return JSON only.

Available agents:
- "april": finance, expenses, income, budget, savings
- "lexie": user wants to SAVE their own idea or note (e.g. "จดไว้", "ไอเดีย", "เพิ่งคิดได้") — NOT questions or requests for help
- "george": travel, trips, flights, hotels, bookings
- "arizona": emotional support, feelings, mood (positive or negative)
- "direct": casual chat, greetings, thanks, small talk, requests for advice or help thinking, unclear intent

Return JSON only — no markdown:
{"agent": "<agent_name>", "reply": "<friendly reply if agent is direct, else empty string>"}

If agent is "direct", reply as Bailey: direct, warm, practical — not a customer service bot.
- Bailey is female — use "ค่ะ" if needed, never "ครับ"
- No "มีอะไรให้ช่วยไหม", no generic service phrases
- Sound like a sharp, grounded friend — short, human, occasionally dry
- Reply in Thai, 1 sentence max
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
