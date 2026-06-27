from core.notion import NotionClient

_client = None

_TAG_KEYWORDS: dict[str, list[str]] = {
    "film": ["หนัง", "film", "cinema", "movie", "ดูหนัง", "ซีรีส์"],
    "work": ["งาน", "work", "meeting", "ประชุม", "office", "บริษัท"],
    "writing": ["เขียน", "write", "essay", "บทความ", "script", "caption"],
    "life": ["ชีวิต", "life", "ความรู้สึก", "รู้สึก", "คิดถึง", "สังคม"],
}


def _get_client() -> NotionClient:
    global _client
    if _client is None:
        _client = NotionClient()
    return _client


def _reset_client() -> None:
    global _client
    _client = None


def _detect_tags(text: str) -> list[str]:
    lower = text.lower()
    tags = [tag for tag, keywords in _TAG_KEYWORDS.items() if any(k in lower for k in keywords)]
    return tags if tags else ["random"]


def handle(text: str, client: NotionClient | None = None) -> str:
    if client is None:
        client = _get_client()

    tags = _detect_tags(text)
    client.add_idea(title=text, tags=tags, source="observation")

    tag_str = ", ".join(tags)
    return f"✅ Lexie บันทึกแล้ว\n📝 {text}\n🏷 {tag_str}\n\nมี tag เพิ่มไหม? (film / work / writing / life / random)"
