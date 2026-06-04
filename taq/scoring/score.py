from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from taq.scoring.factors.freshness import score_freshness
from taq.scoring.factors.source_reliability import score_source
from taq.scoring.factors.correlation import score_correlation
from taq.scoring.factors.reputation import score_reputation

TYPES = {
    "threat": {"weights": {"freshness": 0.15, "source_reliability": 0.15, "correlation": 0.25, "reputation": 0.35, "base": 0.10}, "base": 0.3},
    "confidence": {"weights": {"freshness": 0.10, "source_reliability": 0.35, "correlation": 0.30, "reputation": 0.15, "base": 0.10}, "base": 0.5},
    "priority": {"weights": {"freshness": 0.25, "source_reliability": 0.10, "correlation": 0.20, "reputation": 0.20, "base": 0.25}, "base": 0.5},
}

async def compute_threat_score(entity_id: str, score_type: str = "threat", investigation_id: str | None = None, overrides: dict | None = None, freshness_days: int | None = None, source_name: str | None = None, entity_count: int = 0, blacklisted: bool = False) -> dict:
    cfg = TYPES.get(score_type, TYPES["threat"])
    raw = {
        "freshness": score_freshness(days_old=freshness_days) if freshness_days is not None else 0.5,
        "source_reliability": score_source(source_name),
        "correlation": score_correlation(entity_count),
        "reputation": score_reputation(blacklisted=blacklisted),
        "base": cfg["base"],
    }
    if overrides:
        raw.update(overrides)
    value = sum(raw[k] * cfg["weights"][k] for k in cfg["weights"])
    return {
        "id": uuid.uuid4().hex[:12],
        "investigation_id": investigation_id or "",
        "entity_id": entity_id,
        "score_type": score_type,
        "value": round(max(0.0, min(1.0, value)), 4),
        "factors": raw,
        "weights": cfg["weights"],
        "computed_at": datetime.utcnow().isoformat(),
    }
