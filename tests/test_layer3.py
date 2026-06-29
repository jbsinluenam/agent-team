from unittest.mock import MagicMock
import router.layer3 as layer3


def _make_llm(response_text: str):
    mock = MagicMock()
    msg = MagicMock()
    msg.content = [MagicMock(text=response_text)]
    mock.messages.create.return_value = msg
    return mock


def test_classify_routes_to_arizona():
    llm = _make_llm('{"agent": "arizona", "reply": ""}')
    agent, reply = layer3.classify("รู้สึกหนักใจมาก", llm=llm)
    assert agent == "arizona"
    assert reply == ""


def test_classify_routes_to_april():
    llm = _make_llm('{"agent": "april", "reply": ""}')
    agent, reply = layer3.classify("อยากรู้ยอดเงิน", llm=llm)
    assert agent == "april"
    assert reply == ""


def test_classify_direct_returns_reply():
    llm = _make_llm('{"agent": "direct", "reply": "ยินดีเลย!"}')
    agent, reply = layer3.classify("ขอบคุณนะ", llm=llm)
    assert agent == "direct"
    assert reply == "ยินดีเลย!"


def test_classify_llm_exception_returns_unknown():
    llm = MagicMock()
    llm.messages.create.side_effect = Exception("API error")
    agent, reply = layer3.classify("สวัสดี", llm=llm)
    assert agent == "unknown"
    assert reply == ""


def test_classify_malformed_json_returns_unknown():
    llm = _make_llm("this is not json")
    agent, reply = layer3.classify("สวัสดี", llm=llm)
    assert agent == "unknown"
    assert reply == ""


def test_classify_markdown_fenced_json_is_parsed():
    llm = _make_llm('```json\n{"agent": "lexie", "reply": ""}\n```')
    agent, reply = layer3.classify("จดไว้ก่อน", llm=llm)
    assert agent == "lexie"
    assert reply == ""
