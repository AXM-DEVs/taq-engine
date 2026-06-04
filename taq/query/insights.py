from taq.query.llm_client import llm_client
from taq.utils.logger import get_logger

logger = get_logger(__name__)


async def generate_insights(data: dict) -> list[dict]:
    insights = []
    status = data.get("status", "")
    if status == "completed":
        insights.append({"type": "completion", "title": "Completed", "summary": f"Investigation of {data.get('seed_value', '')} finished.", "severity": "info"})
    elif status == "failed":
        insights.append({"type": "failure", "title": "Failed", "summary": (data.get("errors") or ["Unknown"])[0], "severity": "error"})
    for sid, sr in data.get("results", {}).items():
        if not isinstance(sr, dict) or not sr.get("success"):
            continue
        d = sr.get("data", {})
        if isinstance(d, dict) and "value" in d:
            v = d["value"]
            insights.append({"type": "metric", "title": f"Score ({sid})", "summary": f"Value: {v:.2f}", "severity": "high" if isinstance(v, (int, float)) and v > 0.5 else "low"})
        elif isinstance(d, dict) and d.get("result"):
            r = d["result"]
            if isinstance(r, list):
                insights.append({"type": "data", "title": f"Extracted ({sid})", "summary": f"{len(r)} items", "severity": "low"})
    return insights

async def generate_narrative(data: dict) -> str:
    try:
        seed = data.get("seed_value", "unknown")
        n = len(data.get("results", {}))
        return await llm_client.generate(f"Summarize this OSINT investigation in Spanish:\nSeed: {seed}\nStatus: {data.get('status')}\nSteps: {n}")
    except Exception as e:
        logger.warning(f"Narrative failed: {e}")
        return f"Investigation of {data.get('seed_value', '')} completed with {n} steps."
