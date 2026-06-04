from taq.playbooks.steps.base import BaseStep, StepResult
from taq.utils.logger import get_logger

logger = get_logger(__name__)


class NotifyStep(BaseStep):
    async def execute(self, context: dict, results: dict) -> StepResult:
        channel = self.config.get("channel", "log")
        msg = self._interpolate(self.config.get("message", ""), context, results)
        if channel == "log":
            logger.info(f"Notify: {msg}")
            return StepResult(success=True, data={"channel": "log", "message": msg})
        if channel == "webhook":
            url = self.config.get("webhook_url", "")
            if not url:
                logger.info(f"Notify: {msg}")
                return StepResult(success=True, data={"channel": "log", "message": msg})
            import httpx
            try:
                async with httpx.AsyncClient(timeout=10) as c:
                    await c.post(url, json={"text": msg})
                return StepResult(success=True, data={"channel": "webhook", "sent": True})
            except Exception as e:
                return StepResult(success=False, error=str(e))
        logger.info(f"Notify ({channel}): {msg}")
        return StepResult(success=True, data={"channel": channel, "message": msg})

    def _interpolate(self, t: str, ctx: dict, results: dict) -> str:
        if "{{" not in t:
            return t
        import re
        def rep(m):
            expr = m.group(1).strip()
            parts = expr.split(".")
            if parts[0] in results:
                c = results[parts[0]]
                for p in parts[1:]:
                    if isinstance(c, dict):
                        c = c.get(p, "")
                    else:
                        return ""
                return str(c)
            c = ctx
            for p in parts:
                if isinstance(c, dict):
                    c = c.get(p, "")
                else:
                    return ""
            return str(c)
        return re.sub(r"\{\{(.*?)\}\}", rep, t)
