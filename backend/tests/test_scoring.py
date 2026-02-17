from app.core.scoring import calculate_trust_score


def test_perfect_score():
    assert calculate_trust_score(risks=[], secrets=0) == 100


def test_mixed_score():
    risks = [{"severity": "Medium"}]
    # 100 - 10 (medium) - 15 (1 secret) = 75
    assert calculate_trust_score(risks=risks, secrets=1) == 75


def test_floor_at_zero():
    risks = [{"severity": "High"} for _ in range(5)]
    # 100 - 5*25 = -25, clamped to 0
    assert calculate_trust_score(risks=risks, secrets=0) == 0
