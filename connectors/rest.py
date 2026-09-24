from typing import Iterator

import hashlib
import json

import httpx

from connectors.base import BaseConnector
from connectors.models import PaginationConfig
from connectors.exceptions import ConnectorConnectionError
from connectors.exceptions import ConnectorExtractionError
from messaging.event import FalconEvent, SourceInfo

class RestConnector(BaseConnector):
    """
    Falcon connecter for Rest API returing JSON data.
    """

    def __init__(self,config: dict):
        super().__init__(config)

        self.url = self.config["url"]
        self.timeout = self.config.get("timeout", 30)
        self.headers = self.config.get("headers", {})
        self.pagination = PaginationConfig(
        **self.config.get("pagination", {})
        )

    def connect(self) -> None:
        """
        Validate that the REST endpoint is configured.
        """

        if not self.url:
            raise ConnectorConnectionError(
                 "REST API URL is not configured"
            )

    def extract(self) -> Iterator[dict]:
        """
        Call the REST API and yield JSON records.
        Supports both single-request and page-based pagination.
        """

        if not self.pagination.enabled:
            yield from self._fetch_page()
            return

        if self.pagination.type != "page":
            raise ConnectorExtractionError(
                f"Unsupported pagination type: "
                f"{self.pagination.type}"
            )

        page = self.pagination.start_page
        pages_processed = 0

        while True:
            records = list(self._fetch_page(page))

            if not records:
                break

            yield from records

            pages_processed += 1

            if (
                self.pagination.max_pages is not None
                and pages_processed >= self.pagination.max_pages
            ):
                break

            if len(records) < self.pagination.page_size:
                break

            page += 1

    def _fetch_page(self, page: int | None = None) -> Iterator[dict]:
        """
        Fetch a single REST API page.
        """

        params = {}

        if self.pagination.enabled and page is not None:
            params[self.pagination.page_param] = page
            params[self.pagination.page_size_param] = (
                self.pagination.page_size
            )

        try:
            response = httpx.get(
                self.url,
                headers=self.headers,
                params=params,
                timeout=self.timeout,
            )

            response.raise_for_status()

        except httpx.HTTPError as exc:
            raise ConnectorExtractionError(
                f"REST API request failed: {exc}"
            ) from exc

        try:
            data = response.json()

        except ValueError as exc:
            raise ConnectorExtractionError(
                "REST API returned invalid JSON"
            ) from exc

        if isinstance(data, list):
            yield from data

        elif isinstance(data, dict):
            yield data

        else:
            raise ConnectorExtractionError(
                "REST API response must be a JSON object or array"
            )

    def to_event(self, record:dict) ->FalconEvent:

        """
        Convert a REST API record into a FalconEvent.
        """

        return FalconEvent(
            event_id=self._generate_event_id(record),
            run_id=self.config.get(
                "run_id",
                "rest-run",
            ),
            source=SourceInfo(
                type="REST_API",
                connector="rest_connector",
                system=self.config.get(
                    "system",
                    "rest-api",
                ),
            ),
            entity=self.config.get(
                "entity",
                "unknown",
            ),
            operation=self.config.get(
                "operation",
                "UPSERT",
            ),
            payload=record,
        )

    def close(self) -> None:
        """
        Nothing to close for the current HTTP implementation.
        """
        pass

    def _generate_event_id(self, record: dict) -> str:

        """
        Generate a deterministic event ID for a REST record.
        """

        record_id = (record.get("id") or record.get("customer_id"))

        if record_id is not None:
            return str(record_id)

        canonical_record = json.dumps(
            record,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )

        return hashlib.sha256(
            canonical_record.encode("utf-8")
        ).hexdigest()