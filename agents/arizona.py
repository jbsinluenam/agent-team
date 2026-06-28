import json
import os
import re
from datetime import date as _date

import anthropic

from core.notion import NotionClient

_client = None
_llm = None

_RECALL_KEYWORDS = ["ย้อนดู", "recall", "ดูเรื่อง", "ที่ผ่านมา"]
_TOPIC_STRIP = re.compile(r"(ย้อนดู|recall|ดูเรื่อง|ที่ผ่านมา)(เรื่อง)?\s*", re.IGNORECASE)

_SUPPORT_SYSTEM = """You are Arizona, an emotional support companion. Your approach:
- Active Listening first: reflect back what you heard, name the emotion, validate before advising
- CBT-lite: if the user is caught in a negative thought loop, gently surface the pattern (e.g. "ดูเหมือนความคิดนี้วนซ้ำอยู่ — มีส่วนไหนที่อาจไม่ใช่ความจริงทั้งหมดไหม?")
- Never diagnose, prescribe, or replace professional help
- Always reply in Thai
- Keep responses warm, concise (2-4 sentences), human

Return JSON only — no markdown, no extra text:
{"response": "<your reply>", "tags": ["<tag>"], "mood": "<positive|neutral|negative>"}

Valid tags: งาน, ความสัมพันธ์, สุขภาพ, ครอบครัว, เงิน, ตัวเอง, อื่นๆ"""

_RECALL_SYSTEM = """You are Arizona. The user wants to reflect on past emotional entries about a topic.
Summarize the themes, patterns, and any shifts in mood you notice.
Reply in Thai, warm and insightful. 3-5 sentences."""


def _get_client() -> NotionClient:
    global _client
    if _client is None:
        _client = NotionClient()
    return _client


def _get_llm() -> anthropic.Anthropic:
    global _llm
    if _llm is None:
        _llm = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    return _llm


def _reset_client() -> None:
    global _client
    _client = None


def _reset_llm() -> None:
    global _llm
    _llm = None


def _detect_intent(text: str) -> str:
    lower = text.lower()
    if any(k in lower for k in _RECALL_KEYWORDS):
        return "recall"
    return "support"


def _extract_recall_topic(text: str) -> str:
    return _TOPIC_STRIP.sub("", text).strip()


def _call_llm_support(text: str, llm) -> dict:
    message = llm.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        system=_SUPPORT_SYSTEM,
        messages=[{"role": "user", "content": text}],
    )
    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)


def _call_llm_recall(entries: list[dict], llm) -> str:
    formatted = "\n".join(f"[{e['date']}] {e['entry']}" for e in entries)
    message = llm.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        system=_RECALL_SYSTEM,
        messages=[{"role": "user", "content": formatted}],
    )
    return message.content[0].text


def handle(text: str, client: NotionClient | None = None, llm=None) -> str:
    if client is None:
        client = _get_client()
    if llm is None:
        llm = _get_llm()

    intent = _detect_intent(text)

    if intent == "recall":
        return _handle_recall(text, client, llm)
    return _handle_support(text, client, llm)


def _handle_support(text: str, client: NotionClient, llm) -> str:
    result = _call_llm_support(text, llm)
    today = str(_date.today())
    client.log_mood(
        entry=text,
        response=result["response"],
        tags=result.get("tags", ["อื่นๆ"]),
        mood=result.get("mood", "neutral"),
        date=today,
    )
    return result["response"]


def _handle_recall(text: str, client: NotionClient, llm) -> str:
    topic = _extract_recall_topic(text)
    entries = client.recall_moods(topic)
    if not entries:
        return f"Arizona: ยังไม่มี entries เรื่อง '{topic}' ในบันทึก"
    return _call_llm_recall(entries, llm)
