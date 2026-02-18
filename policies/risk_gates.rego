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
    lower(risk.severity) == "critical"
    msg := sprintf("Blocked: critical-severity risk found — %s: %s", [risk.category, risk.reason])
}

deny_reasons contains msg if {
    some risk in input.risks
    lower(risk.severity) == "high"
    msg := sprintf("Blocked: high-severity risk found — %s: %s", [risk.category, risk.reason])
}

# ── EU AI Act: Prohibited use cases ──────────────────────────
prohibited_use_cases := {"social_scoring", "real_time_biometric", "subliminal_manipulation"}

deny_reasons contains msg if {
    some use_case in prohibited_use_cases
    lower(input.pdf_analysis.project_purpose) == use_case
    msg := sprintf("Blocked: Project purpose '%v' is a prohibited AI practice under the EU AI Act.", [use_case])
}

# ── Human-in-the-loop required for high-severity risks ──────
deny_reasons contains msg if {
    some risk in input.risks
    lower(risk.severity) == "high"
    not input.pdf_analysis.human_in_the_loop
    msg := "Blocked: High-severity risks detected without a documented human-in-the-loop oversight mechanism."
}

# ── Biometric data cannot be deployed to public cloud ────────
deny_reasons contains msg if {
    some dtype in input.pdf_analysis.data_types_used
    lower(dtype) == "biometric_data"
    input.code_metadata.deployment_target == "public_cloud"
    msg := "Blocked: Systems processing biometric data cannot be deployed to public-facing unvetted cloud environments."
}
