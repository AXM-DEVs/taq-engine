from datetime import datetime, timezone

FRESHNESS = {"hours": 1.0, "day": 0.95, "days_3": 0.85, "week": 0.7, "month": 0.5, "months_3": 0.3, "year": 0.15, "older": 0.05}

def score_freshness(timestamp_str: str | None = None, days_old: int | None = None) -> float:
    if days_old is not None:
        return _by_days(days_old)
    if timestamp_str:
        try:
            ts = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            return _by_days((datetime.now(timezone.utc) - ts).days)
        except: return 0.3
    return 0.5

def _by_days(d: int) -> float:
    if d < 0: return 1.0
    if d < 1: return FRESHNESS["hours"]
    if d < 2: return FRESHNESS["day"]
    if d < 3: return FRESHNESS["days_3"]
    if d < 7: return FRESHNESS["week"]
    if d < 30: return FRESHNESS["month"]
    if d < 90: return FRESHNESS["months_3"]
    if d < 365: return FRESHNESS["year"]
    return FRESHNESS["older"]
