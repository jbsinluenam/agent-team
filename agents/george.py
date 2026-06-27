import re
from core.notion import NotionClient

_client = None

_BOOKING_KEYWORDS = ["จอง", "ตั๋ว", "โรงแรม", "บิน", "flight", "hotel"]
_TRIP_KEYWORDS = ["เที่ยว", "ไป", "ทริป", "trip", "travel", "จะไป"]
_LOOKUP_KEYWORDS = ["ดู", "มีอะไร", "checklist", "รายการ", "สรุปทริป"]

_FLIGHT_KEYWORDS = ["ตั๋ว", "บิน", "flight", "airline"]
_HOTEL_KEYWORDS = ["โรงแรม", "hotel", "ที่พัก", "resort", "wyndham", "hilton", "marriott"]
_ACTIVITY_KEYWORDS = ["ทัวร์", "tour", "activity", "ดำน้ำ"]


def _get_client() -> NotionClient:
    global _client
    if _client is None:
        _client = NotionClient()
    return _client


def _reset_client() -> None:
    global _client
    _client = None


def _detect_intent(text: str) -> str:
    lower = text.lower()
    has_amount = bool(re.search(r"\d+", text))
    if any(k in lower for k in _BOOKING_KEYWORDS) and has_amount:
        return "booking"
    if any(k in lower for k in _LOOKUP_KEYWORDS):
        return "lookup"
    if any(k in lower for k in _TRIP_KEYWORDS):
        return "new_trip"
    return "unknown"


def _detect_booking_type(text: str) -> str:
    lower = text.lower()
    if any(k in lower for k in _FLIGHT_KEYWORDS):
        return "Flight"
    if any(k in lower for k in _HOTEL_KEYWORDS):
        return "Hotel"
    if any(k in lower for k in _ACTIVITY_KEYWORDS):
        return "Activity"
    return "Other"


def _extract_amount(text: str) -> float | None:
    match = re.search(r"(\d[\d,]*)", text)
    if match:
        return float(match.group(1).replace(",", ""))
    return None


def handle(text: str, client: NotionClient | None = None) -> str:
    if client is None:
        client = _get_client()
    intent = _detect_intent(text)
    if intent == "new_trip":
        return _new_trip(text, client)
    if intent == "booking":
        return _log_booking(text, client)
    if intent == "lookup":
        return _lookup(client)
    return "George: ไม่แน่ใจว่าต้องการอะไร ลองพิมพ์ เช่น 'จะไป Bali กรกฎาคม' หรือ 'จอง Wyndham Bali 12000'"


def _new_trip(text: str, client: NotionClient) -> str:
    client.create_trip(destination=text, status="Planning")
    return f"✅ George บันทึกทริปแล้ว\n📍 {text}\n🗂 Status: Planning"


def _log_booking(text: str, client: NotionClient) -> str:
    trips = client.list_trips()
    if not trips:
        return "George: ยังไม่มีทริปในระบบ ลองสร้างทริปก่อน เช่น 'จะไป Bali กรกฎาคม'"
    trip = trips[0]
    booking_type = _detect_booking_type(text)
    amount = _extract_amount(text)
    client.add_booking(
        trip_id=trip["id"],
        title=text,
        type=booking_type,
        amount=amount,
        status="Pending",
    )
    amount_str = f" {amount:,.0f} บาท" if amount else ""
    return (
        f"✅ George บันทึก booking แล้ว\n"
        f"📋 {text}\n"
        f"🏷 {booking_type}{amount_str}\n"
        f"✈️ ทริป: {trip['title']}"
    )


def _lookup(client: NotionClient) -> str:
    trips = client.list_trips()
    if not trips:
        return "George: ยังไม่มีทริปในระบบ"
    lines = ["📍 ทริปทั้งหมด:"]
    for t in trips:
        lines.append(f"  • {t['title']} ({t['status']})")
    return "\n".join(lines)
