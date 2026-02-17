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


def test_critical_severity():
    risks = [{"severity": "critical"}]
    # 100 - 50 = 50
    assert calculate_trust_score(risks=risks, secrets=0) == 50


def test_low_severity_no_penalty():
    risks = [{"severity": "low"}]
    # 100 - 0 = 100
    assert calculate_trust_score(risks=risks, secrets=0) == 100


def test_case_insensitive_matching():
    risks = [{"severity": "  HIGH  "}, {"severity": "mEdIuM"}]
    # 100 - 25 - 10 = 65
    assert calculate_trust_score(risks=risks, secrets=0) == 65


def test_mixed_case_all_severities():
    risks = [
        {"severity": " cRiTiCal "},
        {"severity": "HIGH"},
        {"severity": "medium"},
    ]
    # 100 - 50 (critical) - 25 (high) - 10 (medium) = 15
    assert calculate_trust_score(risks=risks, secrets=0) == 15
