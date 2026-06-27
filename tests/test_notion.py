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


def test_create_trip_creates_page_with_status():
    with patch("core.notion.Client") as MockClient:
        mock_notion = MagicMock()
        MockClient.return_value = mock_notion
        mock_notion.pages.create.return_value = {"id": "trip-123"}

        from core.notion import NotionClient
        client = NotionClient(token="t", ideas_db_id="i", trips_db_id="trips-db", bookings_db_id="bk-db")
        trip_id = client.create_trip(destination="Bali", status="Planning")

        assert trip_id == "trip-123"
        props = mock_notion.pages.create.call_args[1]["properties"]
        assert props["Status"]["select"]["name"] == "Planning"
        assert props["Destination"]["rich_text"][0]["text"]["content"] == "Bali"


def test_create_trip_returns_page_id():
    with patch("core.notion.Client") as MockClient:
        mock_notion = MagicMock()
        MockClient.return_value = mock_notion
        mock_notion.pages.create.return_value = {"id": "xyz-456"}

        from core.notion import NotionClient
        client = NotionClient(token="t", ideas_db_id="i", trips_db_id="trips-db", bookings_db_id="bk-db")
        result = client.create_trip(destination="Tokyo")

        assert result == "xyz-456"


def test_add_booking_links_to_trip():
    with patch("core.notion.Client") as MockClient:
        mock_notion = MagicMock()
        MockClient.return_value = mock_notion
        mock_notion.pages.create.return_value = {"id": "bk-789"}

        from core.notion import NotionClient
        client = NotionClient(token="t", ideas_db_id="i", trips_db_id="trips-db", bookings_db_id="bk-db")
        bk_id = client.add_booking(trip_id="trip-123", title="Wyndham Bali", type="Hotel", amount=12000.0, status="Pending")

        assert bk_id == "bk-789"
        props = mock_notion.pages.create.call_args[1]["properties"]
        assert props["Trip"]["relation"] == [{"id": "trip-123"}]
        assert props["Type"]["select"]["name"] == "Hotel"
        assert props["Amount"]["number"] == 12000.0


def test_list_trips_returns_list():
    with patch("core.notion.Client") as MockClient:
        mock_notion = MagicMock()
        MockClient.return_value = mock_notion
        mock_notion.databases.query.return_value = {
            "results": [
                {
                    "id": "t1",
                    "properties": {
                        "Title": {"title": [{"plain_text": "Bali Jul 2026"}]},
                        "Destination": {"rich_text": [{"plain_text": "Bali"}]},
                        "Status": {"select": {"name": "Planning"}},
                    },
                }
            ]
        }

        from core.notion import NotionClient
        client = NotionClient(token="t", ideas_db_id="i", trips_db_id="trips-db", bookings_db_id="bk-db")
        trips = client.list_trips()

        assert len(trips) == 1
        assert trips[0]["id"] == "t1"
        assert trips[0]["title"] == "Bali Jul 2026"
        assert trips[0]["status"] == "Planning"


def test_list_trips_empty_returns_empty_list():
    with patch("core.notion.Client") as MockClient:
        mock_notion = MagicMock()
        MockClient.return_value = mock_notion
        mock_notion.databases.query.return_value = {"results": []}

        from core.notion import NotionClient
        client = NotionClient(token="t", ideas_db_id="i", trips_db_id="trips-db", bookings_db_id="bk-db")
        trips = client.list_trips()

        assert trips == []


def test_get_trip_returns_none_when_not_found():
    with patch("core.notion.Client") as MockClient:
        mock_notion = MagicMock()
        MockClient.return_value = mock_notion
        mock_notion.databases.query.return_value = {"results": []}

        from core.notion import NotionClient
        client = NotionClient(token="t", ideas_db_id="i", trips_db_id="trips-db", bookings_db_id="bk-db")
        result = client.get_trip("Nowhere")

        assert result is None


def test_get_trip_by_uuid_calls_pages_retrieve():
    with patch("core.notion.Client") as MockClient:
        mock_notion = MagicMock()
        MockClient.return_value = mock_notion
        mock_notion.pages.retrieve.return_value = {
            "id": "12345678-1234-1234-1234-123456789abc",
            "properties": {
                "Title": {"title": [{"plain_text": "Bali Jul 2026"}]},
                "Destination": {"rich_text": [{"plain_text": "Bali"}]},
                "Status": {"select": {"name": "Planning"}},
                "Budget": {"number": None},
                "Travelers": {"number": None},
            },
        }
        mock_notion.databases.query.return_value = {"results": []}

        from core.notion import NotionClient
        client = NotionClient(token="t", ideas_db_id="i", trips_db_id="trips-db", bookings_db_id="bk-db")
        trip = client.get_trip("12345678-1234-1234-1234-123456789abc")

        mock_notion.pages.retrieve.assert_called_once_with(page_id="12345678-1234-1234-1234-123456789abc")
        assert trip is not None
        assert trip["title"] == "Bali Jul 2026"
        assert trip["bookings"] == []


def test_get_trip_returns_trip_with_bookings():
    with patch("core.notion.Client") as MockClient:
        mock_notion = MagicMock()
        MockClient.return_value = mock_notion

        def query_side_effect(**kwargs):
            db_id = kwargs.get("database_id", "")
            if db_id == "trips-db":
                return {
                    "results": [{
                        "id": "trip-1",
                        "properties": {
                            "Title": {"title": [{"plain_text": "Bali Jul 2026"}]},
                            "Destination": {"rich_text": [{"plain_text": "Bali"}]},
                            "Status": {"select": {"name": "Planning"}},
                            "Budget": {"number": 50000},
                            "Travelers": {"number": 2},
                        },
                    }]
                }
            return {
                "results": [{
                    "properties": {
                        "Title": {"title": [{"plain_text": "Wyndham Bali"}]},
                        "Type": {"select": {"name": "Hotel"}},
                        "Amount": {"number": 12000},
                        "Status": {"select": {"name": "Confirmed"}},
                    }
                }]
            }

        mock_notion.databases.query.side_effect = query_side_effect

        from core.notion import NotionClient
        client = NotionClient(token="t", ideas_db_id="i", trips_db_id="trips-db", bookings_db_id="bk-db")
        trip = client.get_trip("Bali")

        assert trip is not None
        assert trip["title"] == "Bali Jul 2026"
        assert trip["budget"] == 50000
        assert len(trip["bookings"]) == 1
        assert trip["bookings"][0]["title"] == "Wyndham Bali"
