from router.bailey import strip_prefix, route, dispatch


# --- strip_prefix ---

def test_strip_prefix_lexie_colon():
    agent, text = strip_prefix("Lexie: เพิ่งคิดได้ว่า")
    assert agent == "lexie"
    assert text == "เพิ่งคิดได้ว่า"


def test_strip_prefix_april_colon():
    agent, text = strip_prefix("April: กาแฟ 65")
    assert agent == "april"
    assert text == "กาแฟ 65"


def test_strip_prefix_case_insensitive():
    agent, text = strip_prefix("LEXIE: บันทึกด้วย")
    assert agent == "lexie"
    assert text == "บันทึกด้วย"


def test_strip_prefix_no_prefix():
    agent, text = strip_prefix("กาแฟ 65")
    assert agent is None
    assert text == "กาแฟ 65"


def test_strip_prefix_george():
    agent, text = strip_prefix("George: จองโรงแรม")
    assert agent == "george"
    assert text == "จองโรงแรม"


def test_strip_prefix_arizona():
    agent, text = strip_prefix("Arizona: เครียดมาก")
    assert agent == "arizona"
    assert text == "เครียดมาก"


# --- route ---

def test_route_expense_pattern():
    assert route("กาแฟ 65") == "april"


def test_route_income_pattern():
    assert route("เงินเดือน 50000") == "april"


def test_route_summary_keyword():
    assert route("summary") == "april"


def test_route_summary_thai():
    assert route("สรุป") == "april"


def test_route_arizona_stressed():
    assert route("เครียดมากวันนี้") == "arizona"


def test_route_arizona_tired():
    assert route("เหนื่อยมาก") == "arizona"


def test_route_george_trip():
    assert route("อยากจองทริปไปโตเกียว") == "george"


def test_route_george_flight():
    assert route("เช็กตั๋วบินได้เลย") == "george"


def test_route_lexie_idea():
    assert route("ไอเดียใหม่เพิ่งคิดได้") == "lexie"


def test_route_lexie_note():
    assert route("จดไว้ก่อนนะ") == "lexie"


def test_route_unknown():
    assert route("สวัสดี") == "unknown"


# --- dispatch ---

def test_dispatch_explicit_prefix_lexie():
    agent, text = dispatch("Lexie: บันทึกเรื่องหนัง")
    assert agent == "lexie"
    assert text == "บันทึกเรื่องหนัง"


def test_dispatch_no_prefix_finance():
    agent, text = dispatch("กาแฟ 65")
    assert agent == "april"
    assert text == "กาแฟ 65"


def test_dispatch_no_prefix_unknown():
    # layer3 is called when route returns unknown; with no API key it returns ("unknown", "")
    from unittest.mock import patch
    with patch("router.layer3.classify", return_value=("unknown", "")):
        agent, text = dispatch("สวัสดี")
    assert agent == "unknown"


def test_dispatch_strips_prefix_before_routing():
    # "April: สวัสดี" — explicit prefix overrides pattern matching
    agent, text = dispatch("April: สวัสดี")
    assert agent == "april"
    assert text == "สวัสดี"


# --- layer3 integration ---

def test_dispatch_unknown_calls_layer3():
    from unittest.mock import patch, MagicMock
    mock_llm = MagicMock()
    msg = MagicMock()
    msg.content = [MagicMock(text='{"agent": "arizona", "reply": ""}')]
    mock_llm.messages.create.return_value = msg
    with patch("router.layer3._get_llm", return_value=mock_llm):
        agent, text = dispatch("สวัสดี")
    assert agent == "arizona"


def test_dispatch_unknown_direct_reply():
    from unittest.mock import patch, MagicMock
    mock_llm = MagicMock()
    msg = MagicMock()
    msg.content = [MagicMock(text='{"agent": "direct", "reply": "สวัสดีเช่นกัน!"}')]
    mock_llm.messages.create.return_value = msg
    with patch("router.layer3._get_llm", return_value=mock_llm):
        agent, text = dispatch("สวัสดี")
    assert agent == "direct"
    assert text == "สวัสดีเช่นกัน!"
