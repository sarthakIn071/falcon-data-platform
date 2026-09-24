from unittest.mock import patch

from connectors.rest import RestConnector


def test_rest_connector_pagination():
    connector = RestConnector(
        config={
            "url": "https://example.com/customers",
            "pagination": {
                "enabled": True,
                "type": "page",
                "page_param": "page",
                "page_size_param": "limit",
                "page_size": 2,
                "start_page": 1,
            },
        }
    )

    responses = [
        [
            {"id": 1, "name": "John"},
            {"id": 2, "name": "Sarah"},
        ],
        [
            {"id": 3, "name": "Mike"},
        ],
    ]

    def mock_get(url, **kwargs):
        page = kwargs["params"]["page"]

        class MockResponse:
            def raise_for_status(self):
                pass

            def json(self):
                return responses[page - 1]

        return MockResponse()

    with patch(
        "connectors.rest.httpx.get",
        side_effect=mock_get,
    ):
        records = list(connector.extract())

    assert len(records) == 3

    assert records[0]["id"] == 1
    assert records[1]["id"] == 2
    assert records[2]["id"] == 3