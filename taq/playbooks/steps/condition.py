from taq.playbooks.steps.base import BaseStep, StepResult


class ConditionStep(BaseStep):
    async def execute(self, context: dict, results: dict) -> StepResult:
        condition = self.config.get("if", "")
        passed = self._evaluate(condition, context, results)
        return StepResult(success=True, data={"passed": passed})

    def _evaluate(self, condition: str, context: dict, results: dict) -> bool:
        condition = condition.strip()
        if "==" in condition:
            parts = condition.split("==")
            return self._resolve(parts[0].strip(), context, results) == self._resolve(parts[1].strip(), context, results)
        if "!=" in condition:
            parts = condition.split("!=")
            return self._resolve(parts[0].strip(), context, results) != self._resolve(parts[1].strip(), context, results)
        if ">" in condition:
            parts = condition.split(">")
            try: return float(self._resolve(parts[0].strip(), context, results)) > float(self._resolve(parts[1].strip(), context, results))
            except: return False
        if "<" in condition:
            parts = condition.split("<")
            try: return float(self._resolve(parts[0].strip(), context, results)) < float(self._resolve(parts[1].strip(), context, results))
            except: return False
        resolved = self._resolve(condition, context, results)
        if isinstance(resolved, bool): return resolved
        return resolved.lower() in ("true", "yes", "1") if isinstance(resolved, str) else bool(resolved)

    def _resolve(self, path: str, context: dict, results: dict) -> str:
        parts = path.strip().split(".")
        current = results if parts[0] == "results" else context
        start = 1 if parts[0] in ("results", "context") else 0
        for p in parts[start:]:
            if isinstance(current, dict):
                current = current.get(p, "")
            else:
                return ""
        return str(current)
