#!/usr/bin/env bash
# ────────────────────────────────────────────────────────────────
# eval_gates.sh – Evaluate OPA ethical-gate policies
#
# Usage:
#   ./policies/eval_gates.sh                     # run both mock inputs
#   ./policies/eval_gates.sh <input.json>        # run a single input
# ────────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REGO_FILE="${SCRIPT_DIR}/risk_gates.rego"

# ── Colours ──────────────────────────────────────────────────
GREEN='\033[0;32m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'  # No Colour

# ── Helper: evaluate a single input file ─────────────────────
eval_input() {
    local input_file="$1"
    local label
    label="$(basename "$input_file")"

    echo -e "\n${CYAN}━━━ Evaluating: ${label} ━━━${NC}"

    result=$(opa eval \
        --data "$REGO_FILE" \
        --input "$input_file" \
        --format pretty \
        'data.ethical_gates')

    echo "$result"

    # Extract allow value (macOS-compatible)
    allow=$(echo "$result" | grep -o '"allow": *[a-z]*' | head -1 | grep -o 'true\|false' || echo "unknown")

    if [[ "$allow" == "true" ]]; then
        echo -e "${GREEN}✔ PASS — project is allowed through the ethical gate${NC}"
    elif [[ "$allow" == "false" ]]; then
        echo -e "${RED}✘ FAIL — project is blocked by the ethical gate${NC}"
    else
        echo -e "${RED}⚠ Could not determine allow status${NC}"
    fi

    echo ""
    return 0
}

# ── Main ─────────────────────────────────────────────────────
echo -e "${CYAN}╔══════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║   AERAE Ethical-Gate Policy Evaluation       ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════╝${NC}"

if [[ $# -ge 1 ]]; then
    # Evaluate user-supplied input file(s)
    for f in "$@"; do
        eval_input "$f"
    done
else
    # Default: run both mock inputs
    echo -e "\nRunning both mock inputs…"
    eval_input "${SCRIPT_DIR}/mock_input_pass.json"
    eval_input "${SCRIPT_DIR}/mock_input_fail.json"
fi

echo -e "${CYAN}Done.${NC}"
