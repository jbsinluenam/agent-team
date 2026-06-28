import os
import re
from notion_client import Client

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


class NotionClient:
    def __init__(
        self,
        token: str | None = None,
        ideas_db_id: str | None = None,
        trips_db_id: str | None = None,
        bookings_db_id: str | None = None,
        mood_log_db_id: str | None = None,
    ):
        self._ideas_db_id = ideas_db_id or os.environ["NOTION_IDEAS_DB_ID"]
        self._trips_db_id = trips_db_id or os.environ.get("NOTION_TRIPS_DB_ID", "")
        self._bookings_db_id = bookings_db_id or os.environ.get("NOTION_BOOKINGS_DB_ID", "")
        self._mood_log_db_id = mood_log_db_id or os.environ.get("NOTION_MOOD_LOG_DB_ID", "")
        self._client = Client(auth=token or os.environ["NOTION_TOKEN"])

    def add_idea(self, title: str, tags: list[str], source: str) -> str:
        page = self._client.pages.create(
            parent={"database_id": self._ideas_db_id},
            properties={
                "Title": {"title": [{"text": {"content": title}}]},
                "Tags": {"multi_select": [{"name": t} for t in tags]},
                "Source": {"select": {"name": source}},
                "Status": {"select": {"name": "raw"}},
            },
        )
        return page.get("url", "")

    def create_trip(
        self,
        destination: str,
        status: str = "Planning",
        start: str | None = None,
        end: str | None = None,
        budget: float | None = None,
        travelers: int | None = None,
    ) -> str:
        properties: dict = {
            "Title": {"title": [{"text": {"content": destination}}]},
            "Destination": {"rich_text": [{"text": {"content": destination}}]},
            "Status": {"select": {"name": status}},
        }
        if start and end:
            properties["Start / End"] = {"date": {"start": start, "end": end}}
        elif start:
            properties["Start / End"] = {"date": {"start": start}}
        if budget is not None:
            properties["Budget"] = {"number": budget}
        if travelers is not None:
            properties["Travelers"] = {"number": travelers}

        page = self._client.pages.create(
            parent={"database_id": self._trips_db_id},
            properties=properties,
        )
        return page.get("id", "")

    def add_booking(
        self,
        trip_id: str,
        title: str,
        type: str = "Other",
        date: str | None = None,
        amount: float | None = None,
        status: str = "Pending",
        note: str = "",
    ) -> str:
        properties: dict = {
            "Title": {"title": [{"text": {"content": title}}]},
            "Trip": {"relation": [{"id": trip_id}]},
            "Type": {"select": {"name": type}},
            "Status": {"select": {"name": status}},
        }
        if date:
            properties["Date"] = {"date": {"start": date}}
        if amount is not None:
            properties["Amount"] = {"number": amount}
        if note:
            properties["Note"] = {"rich_text": [{"text": {"content": note}}]}

        page = self._client.pages.create(
            parent={"database_id": self._bookings_db_id},
            properties=properties,
        )
        return page.get("id", "")

    def get_trip(self, name_or_id: str) -> dict | None:
        if _UUID_RE.match(name_or_id):
            page = self._client.pages.retrieve(page_id=name_or_id)
            if not page:
                return None
            pages = [page]
            trip_id = page["id"]
        else:
            results = self._client.databases.query(
                database_id=self._trips_db_id,
                filter={"property": "Title", "title": {"contains": name_or_id}},
            )
            if not results["results"]:
                return None
            pages = results["results"]
            trip_id = pages[0]["id"]

        page = pages[0]
        props = page["properties"]

        bookings_result = self._client.databases.query(
            database_id=self._bookings_db_id,
            filter={"property": "Trip", "relation": {"contains": trip_id}},
        )

        def _text(prop) -> str:
            items = prop.get("rich_text") or prop.get("title") or []
            return items[0]["plain_text"] if items else ""

        return {
            "id": trip_id,
            "title": _text(props.get("Title", {})),
            "destination": _text(props.get("Destination", {})),
            "status": (props.get("Status") or {}).get("select", {}).get("name", ""),
            "budget": (props.get("Budget") or {}).get("number"),
            "travelers": (props.get("Travelers") or {}).get("number"),
            "bookings": [
                {
                    "title": _text(b["properties"].get("Title", {})),
                    "type": (b["properties"].get("Type") or {}).get("select", {}).get("name", ""),
                    "amount": (b["properties"].get("Amount") or {}).get("number"),
                    "status": (b["properties"].get("Status") or {}).get("select", {}).get("name", ""),
                }
                for b in bookings_result["results"]
            ],
        }

    def list_trips(self, status: str | None = None) -> list[dict]:
        kwargs: dict = {"database_id": self._trips_db_id}
        if status:
            kwargs["filter"] = {"property": "Status", "select": {"equals": status}}

        results = self._client.databases.query(**kwargs)

        def _text(prop) -> str:
            items = prop.get("rich_text") or prop.get("title") or []
            return items[0]["plain_text"] if items else ""

        return [
            {
                "id": page["id"],
                "title": _text(page["properties"].get("Title", {})),
                "destination": _text(page["properties"].get("Destination", {})),
                "status": (page["properties"].get("Status") or {}).get("select", {}).get("name", ""),
            }
            for page in results["results"]
        ]

    def log_mood(
        self,
        entry: str,
        response: str,
        tags: list[str],
        mood: str,
        date: str,
    ) -> str:
        title = f"{date} {entry[:30]}"
        page = self._client.pages.create(
            parent={"database_id": self._mood_log_db_id},
            properties={
                "Title": {"title": [{"text": {"content": title}}]},
                "Entry": {"rich_text": [{"text": {"content": entry}}]},
                "Response": {"rich_text": [{"text": {"content": response}}]},
                "Tags": {"multi_select": [{"name": t} for t in tags]},
                "Mood": {"select": {"name": mood}},
                "Date": {"date": {"start": date}},
            },
        )
        return page.get("id", "")

    def recall_moods(self, topic: str, limit: int = 10) -> list[dict]:
        results = self._client.databases.query(
            database_id=self._mood_log_db_id,
            filter={"property": "Tags", "multi_select": {"contains": topic}},
            page_size=limit,
        )

        def _text(prop) -> str:
            items = prop.get("rich_text") or prop.get("title") or []
            return items[0]["plain_text"] if items else ""

        return [
            {
                "date": (page["properties"].get("Date") or {}).get("date", {}).get("start", ""),
                "entry": _text(page["properties"].get("Entry", {})),
                "tags": [o["name"] for o in (page["properties"].get("Tags") or {}).get("multi_select", [])],
                "mood": (page["properties"].get("Mood") or {}).get("select", {}).get("name", ""),
            }
            for page in results["results"]
        ]
