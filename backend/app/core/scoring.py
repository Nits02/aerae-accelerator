def calculate_trust_score(risks: list[dict], secrets: int) -> int:
    score = 100
    for risk in risks:
        severity = risk.get("severity", "").capitalize()
        if severity == "High":
            score -= 25
        elif severity == "Medium":
            score -= 10
    score -= 15 * secrets
    return max(score, 0)
