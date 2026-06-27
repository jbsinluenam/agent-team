from core.parser import parse

_AGENT_PREFIXES = ["april", "lexie", "george", "arizona"]

_APRIL_KEYWORDS = ["summary", "สรุป", "balance", "บัญชี"]
_GEORGE_KEYWORDS = ["เที่ยว", "ทริป", "จอง", "บิน", "นัด", "ตั๋ว", "โรงแรม", "passport", "วีซ่า", "checklist"]
_ARIZONA_KEYWORDS = ["เครียด", "เหนื่อย", "กังวล", "stuck", "overwhelmed", "tired", "เศร้า", "ท้อ", "หนักใจ", "อยากคุย"]
_LEXIE_KEYWORDS = ["ไอเดีย", "จด", "จำไว้", "โน้ต", "note", "idea", "เพิ่งคิด", "บันทึกไว้"]


def strip_prefix(text: str) -> tuple[str | None, str]:
    lower = text.lower().strip()
    for name in _AGENT_PREFIXES:
        if lower.startswith(name + ":"):
            return name, text[len(name) + 1:].strip()
    return None, text


def route(text: str) -> str:
    lower = text.lower().strip()

    if any(w in lower for w in _APRIL_KEYWORDS):
        return "april"
    if parse(text) is not None:
        return "april"
    if any(w in lower for w in _ARIZONA_KEYWORDS):
        return "arizona"
    if any(w in lower for w in _GEORGE_KEYWORDS):
        return "george"
    if any(w in lower for w in _LEXIE_KEYWORDS):
        return "lexie"

    return "unknown"


def dispatch(raw: str) -> tuple[str, str]:
    agent_name, text = strip_prefix(raw)
    if agent_name is None:
        agent_name = route(raw)
        text = raw
    return agent_name, text
