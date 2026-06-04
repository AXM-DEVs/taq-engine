from __future__ import annotations

import asyncio
from typing import Any

from taq.playbooks.registry import playbook_registry
from taq.playbooks.steps.base import StepResult
from taq.playbooks.steps.connector_call import ConnectorCallStep
from taq.playbooks.steps.transform import TransformStep
from taq.playbooks.steps.condition import ConditionStep
from taq.playbooks.steps.notify import NotifyStep
from taq.core.exceptions import PlaybookNotFoundError, StepExecutionError
from taq.utils.logger import get_logger

logger = get_logger(__name__)

_STEP_MAP = {
    "connector_call": ConnectorCallStep,
    "transform": TransformStep,
    "condition": ConditionStep,
    "notify": NotifyStep,
}


class PlaybookExecutor:
    def __init__(self, max_retries: int = 2):
        self.max_retries = max_retries

    async def execute(self, playbook_id_or_name: str, investigation: Any) -> dict[str, Any]:
        pb = playbook_registry.get(playbook_id_or_name) or playbook_registry.get_by_name(playbook_id_or_name)
        if not pb:
            raise PlaybookNotFoundError(f"Playbook '{playbook_id_or_name}' not found")

        results: dict = {}
        context = {"seed": {"type": investigation.seed_type, "value": investigation.seed_value}}
        logger.info(f"Executing '{pb.name}' for {investigation.seed_value}")

        i = 0
        while i < len(pb.steps):
            step_def = pb.steps[i]
            sid = step_def.get("id", f"step_{i}")
            stype = step_def.get("type", "unknown")

            parallel_group = step_def.get("parallel", False)
            if isinstance(parallel_group, list):
                parallel_results = await self._run_parallel(parallel_group, context, results)
                results.update(parallel_results)
                context.update(parallel_results)
                i += 1
                continue

            condition = step_def.get("condition")
            if condition and isinstance(condition, dict):
                cs = ConditionStep("_cond", {"if": condition.get("if", "")})
                cr = await cs.execute(context, results)
                if not cr.data.get("passed", False):
                    results[sid] = {"skipped": True}
                    i += 1
                    continue

            sr = await self._run(sid, stype, step_def, context, results)
            results[sid] = sr.to_dict()
            context[sid] = sr.to_dict()
            i += 1

        return results

    async def _run_parallel(self, steps: list[dict], ctx: dict, results: dict) -> dict[str, Any]:
        async def run_one(sd: dict) -> tuple[str, dict]:
            sid = sd.get("id", "parallel_unknown")
            stype = sd.get("type", "unknown")
            sr = await self._run(sid, stype, sd, ctx, results)
            return sid, sr.to_dict()
        outcomes = await asyncio.gather(*[run_one(s) for s in steps], return_exceptions=True)
        parallel_results = {}
        for o in outcomes:
            if isinstance(o, tuple):
                parallel_results[o[0]] = o[1]
            elif isinstance(o, Exception):
                logger.warning(f"Parallel step failed: {o}")
        return parallel_results

    async def _run(self, sid: str, stype: str, step: dict, ctx: dict, results: dict) -> StepResult:
        if stype == "scoring.compute":
            return await self._run_scoring(step, ctx, results)
        cls = _STEP_MAP.get(stype)
        if not cls:
            raise StepExecutionError(f"Unknown step type: '{stype}'")
        inst = cls(sid, step)
        for attempt in range(self.max_retries + 1):
            try:
                r = await inst.execute(ctx, results)
                if r.success:
                    logger.info(f"Step '{sid}' OK")
                else:
                    logger.warning(f"Step '{sid}' failed: {r.error}")
                return r
            except Exception as e:
                if attempt < self.max_retries:
                    logger.warning(f"Step '{sid}' retry {attempt+1}: {e}")
                else:
                    raise StepExecutionError(f"Step '{sid}' failed: {e}")
        raise StepExecutionError(f"Step '{sid}' failed")

    async def _run_scoring(self, step: dict, ctx: dict, results: dict) -> StepResult:
        from taq.scoring.score import compute_threat_score
        inputs = step.get("inputs", [])
        factors = {}
        for inp in inputs:
            r = results.get(inp, {})
            factors[inp] = 0.5 if r.get("success", False) else 0.0
        score = await compute_threat_score(entity_id=ctx.get("seed", {}).get("value", ""), overrides=factors)
        return StepResult(success=True, data=score)
