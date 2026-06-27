from unittest.mock import MagicMock, patch


def test_add_idea_creates_page_with_correct_properties():
    with patch("core.notion.Client") as MockClient:
        mock_notion = MagicMock()
        MockClient.return_value = mock_notion
        mock_notion.pages.create.return_value = {"url": "https://notion.so/abc123"}

        from core.notion import NotionClient
        client = NotionClient(token="fake-token", ideas_db_id="fake-db-id")
        url = client.add_idea(title="Test idea", tags=["film", "life"], source="observation")

        assert url == "https://notion.so/abc123"
        create_kwargs = mock_notion.pages.create.call_args[1]
        assert create_kwargs["parent"] == {"database_id": "fake-db-id"}
        props = create_kwargs["properties"]
        assert props["Title"]["title"][0]["text"]["content"] == "Test idea"
        assert {"name": "film"} in props["Tags"]["multi_select"]
        assert {"name": "life"} in props["Tags"]["multi_select"]
        assert props["Source"]["select"]["name"] == "observation"
        assert props["Status"]["select"]["name"] == "raw"


def test_add_idea_with_empty_tags():
    with patch("core.notion.Client") as MockClient:
        mock_notion = MagicMock()
        MockClient.return_value = mock_notion
        mock_notion.pages.create.return_value = {"url": "https://notion.so/abc123"}

        from core.notion import NotionClient
        client = NotionClient(token="fake-token", ideas_db_id="fake-db-id")
        client.add_idea(title="Simple idea", tags=[], source="random")

        props = mock_notion.pages.create.call_args[1]["properties"]
        assert props["Tags"]["multi_select"] == []


def test_add_idea_returns_page_url():
    with patch("core.notion.Client") as MockClient:
        mock_notion = MagicMock()
        MockClient.return_value = mock_notion
        mock_notion.pages.create.return_value = {"url": "https://notion.so/xyz789"}

        from core.notion import NotionClient
        client = NotionClient(token="fake-token", ideas_db_id="fake-db-id")
        url = client.add_idea(title="Another idea", tags=["random"], source="conversation")

        assert url == "https://notion.so/xyz789"
