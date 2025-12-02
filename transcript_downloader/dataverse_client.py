"""Dataverse Web API client for Dynamics 365."""

from typing import Any
from urllib.parse import quote

import requests

from . import config


class DataverseClient:
    """Client for interacting with Dataverse Web API."""

    def __init__(
        self,
        access_token: str,
        organization_url: str = config.ORGANIZATION_URL,
        api_version: str = config.API_VERSION,
    ):
        """
        Initialize the Dataverse client.

        Args:
            access_token: OAuth2 access token for authentication.
            organization_url: Dynamics 365 organization URL.
            api_version: Dataverse Web API version.
        """
        self.access_token = access_token
        self.organization_url = organization_url.rstrip("/")
        self.api_version = api_version
        self.base_url = f"{self.organization_url}/api/data/{api_version}"

        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
                "OData-MaxVersion": "4.0",
                "OData-Version": "4.0",
                "Content-Type": "application/json; charset=utf-8",
                "Prefer": "odata.include-annotations=*",
            }
        )

    def execute_fetch_xml(self, entity_name: str, fetch_xml: str) -> list[dict[str, Any]]:
        """
        Execute a FetchXML query and return all results with pagination.

        Args:
            entity_name: The logical name of the entity (e.g., 'msdyn_ocliveworkitem').
            fetch_xml: The FetchXML query string.

        Returns:
            List of entity records.
        """
        all_records = []
        encoded_fetch = quote(fetch_xml)
        url = f"{self.base_url}/{entity_name}s?fetchXml={encoded_fetch}"

        while url:
            response = self._session.get(url)
            response.raise_for_status()
            data = response.json()

            records = data.get("value", [])
            all_records.extend(records)

            # Handle pagination
            url = data.get("@odata.nextLink")

        return all_records

    def get_entity(
        self,
        entity_name: str,
        entity_id: str,
        select: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Get a single entity by ID.

        Args:
            entity_name: The logical name of the entity.
            entity_id: The GUID of the entity.
            select: Optional list of fields to select.

        Returns:
            Entity record as dictionary.
        """
        url = f"{self.base_url}/{entity_name}s({entity_id})"

        if select:
            url += f"?$select={','.join(select)}"

        response = self._session.get(url)
        response.raise_for_status()
        return response.json()

    def query_entities(
        self,
        entity_name: str,
        filter_query: str | None = None,
        select: list[str] | None = None,
        order_by: str | None = None,
        top: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Query entities using OData query options.

        Args:
            entity_name: The logical name of the entity.
            filter_query: OData $filter query string.
            select: List of fields to select.
            order_by: OData $orderby clause.
            top: Maximum number of records to return.

        Returns:
            List of entity records.
        """
        url = f"{self.base_url}/{entity_name}s"
        params = []

        if filter_query:
            params.append(f"$filter={filter_query}")
        if select:
            params.append(f"$select={','.join(select)}")
        if order_by:
            params.append(f"$orderby={order_by}")
        if top:
            params.append(f"$top={top}")

        if params:
            url += "?" + "&".join(params)

        all_records = []

        while url:
            response = self._session.get(url)
            response.raise_for_status()
            data = response.json()

            records = data.get("value", [])
            all_records.extend(records)

            # Handle pagination (unless top is specified)
            if top:
                break
            url = data.get("@odata.nextLink")

        return all_records
