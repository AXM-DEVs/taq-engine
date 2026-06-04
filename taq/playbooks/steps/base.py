from abc import ABC, abstractmethod
from typing import Any


class StepResult:
    def __init__(self, success: bool, data: Any = None, error: str | None = None):
        self.success = success
        self.data = data
        self.error = error

    def to_dict(self) -> dict:
        return {"success": self.success, "data": self.data, "error": self.error}


class BaseStep(ABC):
    def __init__(self, step_id: str, config: dict):
        self.id = step_id
        self.config = config

    @abstractmethod
    async def execute(self, context: dict, results: dict) -> StepResult:
        ...
