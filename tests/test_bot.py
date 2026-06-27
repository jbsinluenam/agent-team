from unittest.mock import patch
import bot


def test_handle_message_routes_to_april():
    with patch("agents.april.handle", return_value="april response") as mock_april:
        result = bot.handle_message("กาแฟ 65")
        assert result == "april response"
        mock_april.assert_called_once_with("กาแฟ 65")


def test_handle_message_routes_to_lexie():
    with patch("agents.lexie.handle", return_value="lexie response") as mock_lexie:
        result = bot.handle_message("Lexie: เพิ่งคิดได้ว่า")
        assert result == "lexie response"
        mock_lexie.assert_called_once_with("เพิ่งคิดได้ว่า")


def test_handle_message_unknown_returns_bailey_message():
    result = bot.handle_message("สวัสดี")
    assert "Bailey" in result or "ไม่แน่ใจ" in result


def test_handle_message_routes_to_george():
    with patch("agents.george.handle", return_value="george response") as mock_george:
        result = bot.handle_message("George: จองโรงแรม")
        assert result == "george response"
        mock_george.assert_called_once_with("จองโรงแรม")


def test_handle_message_phase2_arizona_returns_coming_soon():
    result = bot.handle_message("Arizona: เครียดมาก")
    assert "Phase 2" in result or "ยังไม่พร้อม" in result
