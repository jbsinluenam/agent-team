import os
from notion_client import Client


class NotionClient:
    def __init__(self, token: str | None = None, ideas_db_id: str | None = None):
        self._ideas_db_id = ideas_db_id or os.environ["NOTION_IDEAS_DB_ID"]
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
