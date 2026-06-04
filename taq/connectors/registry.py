from __future__ import annotations

from typing import Optional

from taq.connectors.base import BaseConnector, ConnectorResult
from taq.core.exceptions import ConnectorNotFoundError
from taq.storage.models import UserTier, UserModel


class ConnectorRegistry:
    def __init__(self):
        self._connectors: dict[str, BaseConnector] = {}

    def register(self, connector: BaseConnector):
        self._connectors[connector.name()] = connector

    def get(self, name: str) -> Optional[BaseConnector]:
        return self._connectors.get(name)

    def list(self) -> list[str]:
        return list(self._connectors.keys())

    async def call(self, connector_name: str, action: str, params: dict, user: Optional[UserModel] = None) -> ConnectorResult:
        connector = self.get(connector_name)
        if not connector:
            raise ConnectorNotFoundError(f"Connector '{connector_name}' not found. Available: {', '.join(self.list())}")
        # Determine if connector is premium: naming convention - if name does NOT end with '_free' and is not in FREE_CONNECTORS set
        FREE_CONNECTORS = {'dns_resolver', 'whois', 'shodan_free', 'abuseipdb_free', 'vt_free'}
        is_premium = connector.name() not in FREE_CONNECTORS
        if user is not None and user.tier == UserTier.FREE and is_premium:
            return ConnectorResult(False, error=f"Connector '{connector_name}' is not available for free tier users.")
        return await connector.call(action, params)

    async def health(self, connector_name: str, user: Optional[UserModel] = None) -> dict:
        connector = self.get(connector_name)
        if not connector:
            raise ConnectorNotFoundError(f"Connector '{connector_name}' not found")
        # Optionally, we could also restrict health checks for premium connectors, but health is lightweight.
        return await connector.health()


connector_registry = ConnectorRegistry()
