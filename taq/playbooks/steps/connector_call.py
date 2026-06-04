from __future__ import annotations

from typing import Any

from taq.playbooks.steps.base import BaseStep, StepResult
from taq.connectors.registry import connector_registry
from taq.utils.logger import get_logger

logger = get_logger(__name__)


class ConnectorCallStep(BaseStep):
    async def execute(self, context: dict, results: dict) -> StepResult:
        connector_name = self.config.get("connector", "")
        action = self.config.get("action", "")
        raw_params = self.config.get("params", {})
        params = self._interpolate(raw_params, context)

        logger.info(f"ConnectorCall: {connector_name}.{action}", extra={"step_id": self.id})
        try:
            result = await connector_registry.call(connector_name, action, params)
            return result
        except Exception as e:
            logger.error(f"ConnectorCall failed: {e}", extra={"step_id": self.id})
            return StepResult(success=False, error=str(e))

    def _interpolate(self, value: Any, context: dict) -> Any:
        if isinstance(value, str):
            if "{{" in value:
                import re
                def rep(m):
                    expr = m.group(1).strip()
                    parts = expr.split(".")
                    c = context
                    for p in parts:
                        if isinstance(c, dict):
                            c = c.get(p, "")
                        else:
                            return ""
                    return str(c)
                return re.sub(r"\{\{(.*?)\}\}", rep, value)
            return value
        elif isinstance(value, dict):
            return {k: self._interpolate(v, context) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._interpolate(v, context) for v in value]
        return value
