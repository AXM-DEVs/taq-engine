from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ConnectorResult:
    def __init__(self, success: bool, data: Any = None, error: str | None = None):
        self.success = success
        self.data = data
        self.error = error

    def to_dict(self) -> dict:
        return {"success": self.success, "data": self.data, "error": self.error}


class BaseConnector(ABC):
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    async def health(self) -> dict:
        ...

    @abstractmethod
    async def call(self, action: str, params: dict) -> ConnectorResult:
        ...
