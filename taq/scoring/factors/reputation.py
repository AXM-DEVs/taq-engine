REPUTATION = {
    "spamhaus": -0.4, "spamcop": -0.3, "malwarebytes": -0.5,
    "vt_malicious": -0.6, "abuseipdb_malicious": -0.5,
    "phishtank": -0.5, "openphish": -0.4,
}

def score_reputation(blacklisted: bool = False, lists_matched: list[str] | None = None, vt_malicious_score: int | None = None) -> float:
    score = 0.5
    if blacklisted:
        score -= 0.3
    if lists_matched:
        for lst in lists_matched:
            if lst in REPUTATION:
                score += REPUTATION[lst]
    if vt_malicious_score is not None:
        if vt_malicious_score >= 10: score -= 0.4
        elif vt_malicious_score >= 5: score -= 0.2
        elif vt_malicious_score >= 1: score -= 0.1
    return max(0.0, min(1.0, score))
