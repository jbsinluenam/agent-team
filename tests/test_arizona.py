import json
from unittest.mock import MagicMock, patch
from agents.arizona import handle, _detect_intent, _extract_recall_topic


def make_notion_client(entries=None):
    client = MagicMock()
    client.log_mood.return_value = "mood-id-1"
    client.recall_moods.return_value = entries if entries is not None else [
        {"date": "2026-06-27", "entry": "เครียดเรื่องงาน", "tags": ["งาน"], "mood": "negative"}
    ]
    return client


def make_llm(response_text=None):
    llm = MagicMock()
    msg = MagicMock()
    msg.content[0].text = response_text or json.dumps({
        "response": "ฟังดูเหนื่อยมากเลย รู้สึกแบบนี้มานานแล้วไหม?",
        "tags": ["งาน"],
        "mood": "negative",
    })
    llm.messages.create.return_value = msg
    return llm


# --- _detect_intent ---

def test_detect_intent_recall_thai():
    assert _detect_intent("ย้อนดูเรื่องงาน") == "recall"


def test_detect_intent_recall_english():
    assert _detect_intent("recall งาน") == "recall"


def test_detect_intent_recall_du_ruang():
    assert _detect_intent("ดูเรื่องความสัมพันธ์") == "recall"


def test_detect_intent_support_default():
    assert _detect_intent("เครียดมากเรื่องงานวันนี้") == "support"


def test_detect_intent_support_empty_feeling():
    assert _detect_intent("รู้สึกแย่ไม่รู้ทำไม") == "support"


# --- _extract_recall_topic ---

def test_extract_recall_topic_after_ruang():
    assert _extract_recall_topic("ย้อนดูเรื่องงาน") == "งาน"


def test_extract_recall_topic_after_recall():
    assert _extract_recall_topic("recall ความสัมพันธ์") == "ความสัมพันธ์"


def test_extract_recall_topic_fallback():
    assert _extract_recall_topic("ที่ผ่านมา") == ""


# --- handle: support ---

def test_handle_support_calls_llm():
    client = make_notion_client()
    llm = make_llm()
    result = handle("เครียดมากเรื่องงาน", client, llm)
    llm.messages.create.assert_called_once()
    assert "ฟังดูเหนื่อย" in result


def test_handle_support_logs_to_notion():
    client = make_notion_client()
    llm = make_llm()
    handle("เครียดมากเรื่องงาน", client, llm)
    client.log_mood.assert_called_once()
    kwargs = client.log_mood.call_args[1]
    assert kwargs["entry"] == "เครียดมากเรื่องงาน"
    assert kwargs["mood"] == "negative"
    assert "งาน" in kwargs["tags"]


def test_handle_support_returns_response_text():
    client = make_notion_client()
    llm = make_llm(json.dumps({
        "response": "Arizona ได้ยินนะ",
        "tags": ["ตัวเอง"],
        "mood": "neutral",
    }))
    result = handle("รู้สึกงงๆ", client, llm)
    assert result == "Arizona ได้ยินนะ"


# --- handle: recall ---

def test_handle_recall_queries_notion():
    client = make_notion_client()
    llm = make_llm("ช่วงที่ผ่านมานายเครียดเรื่องงานบ่อยมาก")
    result = handle("ย้อนดูเรื่องงาน", client, llm)
    client.recall_moods.assert_called_once_with("งาน")
    assert "เครียด" in result


def test_handle_recall_no_entries_returns_message():
    client = make_notion_client(entries=[])
    llm = make_llm()
    result = handle("ย้อนดูเรื่องครอบครัว", client, llm)
    assert "ยังไม่มี" in result or "ครอบครัว" in result
    llm.messages.create.assert_not_called()


def test_handle_recall_passes_entries_to_llm():
    client = make_notion_client(entries=[
        {"date": "2026-06-01", "entry": "คิดถึงแม่มาก", "tags": ["ครอบครัว"], "mood": "neutral"},
        {"date": "2026-06-10", "entry": "คุยกับแม่แล้วดีขึ้น", "tags": ["ครอบครัว"], "mood": "positive"},
    ])
    llm = make_llm("สังเกตว่าความรู้สึกเรื่องครอบครัวดีขึ้นเรื่อยๆ")
    result = handle("ดูเรื่องครอบครัว", client, llm)
    call_args = llm.messages.create.call_args[1]["messages"][0]["content"]
    assert "คิดถึงแม่มาก" in call_args
    assert "สังเกตว่า" in result
