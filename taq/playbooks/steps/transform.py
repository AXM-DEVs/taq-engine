from taq.playbooks.steps.base import BaseStep, StepResult
from taq.utils.logger import get_logger

logger = get_logger(__name__)


class TransformStep(BaseStep):
    async def execute(self, context: dict, results: dict) -> StepResult:
        script = self.config.get("script", "")
        input_step = self.config.get("input")
        input_data = None
        if input_step:
            input_data = results.get(input_step, {})
            if hasattr(input_data, "data"):
                input_data = input_data.data
            elif isinstance(input_data, dict):
                input_data = input_data.get("data", input_data)
        result = self._run(script, input_data, context)
        return StepResult(success=True, data=result)

    def _run(self, script: str | None, input_data: dict | None, context: dict) -> dict:
        if script == "extract_username_from_email":
            email = context.get("seed", {}).get("value", "")
            return {"result": email.split("@")[0] if "@" in email else email}
        if script == "extract_domain_from_email":
            email = context.get("seed", {}).get("value", "")
            return {"result": email.split("@")[1] if "@" in email else email}
        if script == "extract_ips":
            import re
            text = str(input_data or {})
            return {"result": re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", text)}
        if script == "extract_urls":
            import re
            text = str(input_data or {})
            return {"result": re.findall(r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*", text)}
        logger.warning(f"Unknown transform script: {script}")
        return {"result": None}
