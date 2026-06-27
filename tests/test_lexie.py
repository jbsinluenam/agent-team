from unittest.mock import MagicMock
from agents.lexie import handle


def make_client(page_url="https://notion.so/test-page"):
    client = MagicMock()
    client.add_idea.return_value = page_url
    return client


def test_captures_idea_calls_add_idea():
    client = make_client()
    handle("ความเหงาใน The Apartment", client)
    client.add_idea.assert_called_once()
    kwargs = client.add_idea.call_args[1]
    assert kwargs["title"] == "ความเหงาใน The Apartment"


def test_response_confirms_capture():
    client = make_client()
    result = handle("เพิ่งคิดได้ว่าโลกมันแบน", client)
    assert "บันทึกแล้ว" in result
    assert "🏷" in result


def test_detects_film_tag():
    client = make_client()
    handle("หนังเรื่องนี้ทำให้คิดเรื่องความเหงา", client)
    kwargs = client.add_idea.call_args[1]
    assert "film" in kwargs["tags"]


def test_detects_work_tag():
    client = make_client()
    handle("ในงานประชุมวันนี้มีเรื่องน่าสนใจ", client)
    kwargs = client.add_idea.call_args[1]
    assert "work" in kwargs["tags"]


def test_detects_writing_tag():
    client = make_client()
    handle("อยากเขียน essay เรื่องความเหงา", client)
    kwargs = client.add_idea.call_args[1]
    assert "writing" in kwargs["tags"]


def test_default_tag_is_random_when_no_match():
    client = make_client()
    handle("สิ่งที่อยากจำ", client)
    kwargs = client.add_idea.call_args[1]
    assert "random" in kwargs["tags"]


def test_source_defaults_to_observation():
    client = make_client()
    handle("เพิ่งสังเกตเห็นอะไรบางอย่าง", client)
    kwargs = client.add_idea.call_args[1]
    assert kwargs["source"] == "observation"
