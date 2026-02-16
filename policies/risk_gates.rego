package ethical_gates

# ── Default decision ─────────────────────────────────────────
default allow := false

# ── Gate: allow only when every check passes ─────────────────
allow if {
    count(deny_reasons) == 0
}

# ── Deny reasons ─────────────────────────────────────────────
deny_reasons contains msg if {
    input.secrets_count > 0
    msg := sprintf("Blocked: %d hardcoded secret(s) detected in the repository", [input.secrets_count])
}

deny_reasons contains msg if {
    some risk in input.risks
    lower(risk.severity) == "high"
    msg := sprintf("Blocked: high-severity risk found — %s: %s", [risk.category, risk.reason])
}
