def calculate_trust_score(risks: list[dict], secrets: int) -> int:
    score = 100
    for risk in risks:
        severity = risk.get("severity", "").lower().strip()
        if severity == "critical":
            score -= 50
        elif severity == "high":
            score -= 25
        elif severity == "medium":
            score -= 10
        elif severity == "low":
            score -= 0
    score -= 15 * secrets
    return max(score, 0)
