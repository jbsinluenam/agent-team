from unittest.mock import MagicMock
from agents.george import handle, _detect_intent, _detect_booking_type, _extract_amount


def make_client(trips=None, trip=None):
    client = MagicMock()
    client.create_trip.return_value = "trip-id-1"
    client.add_booking.return_value = "bk-id-1"
    client.list_trips.return_value = trips if trips is not None else [
        {"id": "trip-id-1", "title": "Bali Jul 2026", "destination": "Bali", "status": "Planning"}
    ]
    client.get_trip.return_value = trip
    return client


# --- _detect_intent ---

def test_detect_intent_new_trip_thai():
    assert _detect_intent("จะไป Bali กรกฎาคม") == "new_trip"


def test_detect_intent_new_trip_trip_keyword():
    assert _detect_intent("ทริปโตเกียวปีหน้า") == "new_trip"


def test_detect_intent_booking_with_amount():
    assert _detect_intent("จอง Wyndham Bali 12000") == "booking"


def test_detect_intent_flight_booking():
    assert _detect_intent("ตั๋วบิน BKK-DPS 8500") == "booking"


def test_detect_intent_lookup():
    assert _detect_intent("ดูทริปทั้งหมด") == "lookup"


def test_detect_intent_checklist():
    assert _detect_intent("checklist บาหลี") == "lookup"


def test_detect_intent_unknown():
    assert _detect_intent("สวัสดี") == "unknown"


# --- _detect_booking_type ---

def test_detect_booking_type_flight():
    assert _detect_booking_type("ตั๋วบิน BKK-DPS") == "Flight"


def test_detect_booking_type_hotel():
    assert _detect_booking_type("จอง Wyndham Bali") == "Hotel"


def test_detect_booking_type_activity():
    assert _detect_booking_type("ทัวร์ดำน้ำ") == "Activity"


def test_detect_booking_type_other():
    assert _detect_booking_type("จอง 5000") == "Other"


# --- _extract_amount ---

def test_extract_amount_plain_number():
    assert _extract_amount("จอง Wyndham 12000") == 12000.0


def test_extract_amount_with_comma():
    assert _extract_amount("ตั๋ว 8,500") == 8500.0


def test_extract_amount_none_when_missing():
    assert _extract_amount("จะไป Bali") is None


# --- handle ---

def test_handle_new_trip_calls_create_trip():
    client = make_client()
    result = handle("จะไป Bali กรกฎาคม", client)
    client.create_trip.assert_called_once()
    assert "บันทึก" in result or "Planning" in result


def test_handle_booking_calls_add_booking():
    client = make_client()
    result = handle("จอง Wyndham Bali 12000", client)
    client.add_booking.assert_called_once()
    kwargs = client.add_booking.call_args[1]
    assert kwargs["trip_id"] == "trip-id-1"
    assert kwargs["amount"] == 12000.0
    assert kwargs["type"] == "Hotel"


def test_handle_booking_no_trips_returns_guidance():
    client = make_client(trips=[])
    result = handle("จอง Wyndham 12000", client)
    assert "ทริป" in result
    client.add_booking.assert_not_called()


def test_handle_lookup_returns_trip_list():
    client = make_client()
    result = handle("ดูทริปทั้งหมด", client)
    assert "Bali Jul 2026" in result


def test_handle_unknown_returns_guidance():
    client = make_client()
    result = handle("สวัสดี", client)
    assert "George" in result
