import { CheckCircle2, XCircle, ShieldAlert } from "lucide-react";

/* ── Types ───────────────────────────────────────────────── */
interface Risk {
  category: string;
  severity: string;
  reason: string;
}

interface OpaResult {
  allow?: boolean;
  deny_reasons?: string[];
  opa_unavailable?: boolean;
}

export interface OpaGateDetailProps {
  opaResult: OpaResult;
  risks: Risk[];
  secrets_count: number;
}

/* ── Checklist row ───────────────────────────────────────── */
function RuleRow({
  label,
  passed,
  detail,
}: {
  label: string;
  passed: boolean;
  detail: string;
}) {
  return (
    <div className="flex items-start gap-2.5 rounded-lg border p-3 bg-white">
      {passed ? (
        <CheckCircle2 className="h-5 w-5 text-green-500 shrink-0 mt-0.5" />
      ) : (
        <XCircle className="h-5 w-5 text-red-500 shrink-0 mt-0.5" />
      )}
      <div className="flex-1 min-w-0">
        <p
          className={`text-sm font-medium ${
            passed ? "text-green-700" : "text-red-700"
          }`}
        >
          {label}
        </p>
        <p className="text-xs text-gray-500 mt-0.5">{detail}</p>
      </div>
      <span
        className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-bold uppercase ${
          passed
            ? "bg-green-100 text-green-700"
            : "bg-red-100 text-red-700"
        }`}
      >
        {passed ? "Pass" : "Fail"}
      </span>
    </div>
  );
}

/* ── Component ───────────────────────────────────────────── */
export default function OpaGateDetail({
  opaResult,
  risks,
  secrets_count,
}: OpaGateDetailProps) {
  const hasHighRisk = risks.some(
    (r) => r.severity.toLowerCase() === "high",
  );
  const hasSecrets = secrets_count > 0;

  return (
    <div className="space-y-4">
      {/* ── Decision badge row ─────────────────────────────── */}
      <div className="flex items-center gap-2">
        <span className="text-xs font-medium text-gray-500 uppercase">
          Decision:
        </span>
        <span
          className={`px-2 py-0.5 rounded-full text-xs font-bold uppercase ${
            opaResult.allow
              ? "bg-green-100 text-green-700"
              : "bg-red-100 text-red-700"
          }`}
        >
          {opaResult.allow ? "Allow" : "Deny"}
        </span>
        {opaResult.opa_unavailable && (
          <span className="text-xs text-amber-600 italic">
            (OPA server was unavailable)
          </span>
        )}
      </div>

      {/* ── Deny reasons (if any) ─────────────────────────── */}
      {(opaResult.deny_reasons ?? []).length > 0 && (
        <div>
          <p className="text-xs font-medium text-gray-500 uppercase mb-1">
            Deny Reasons:
          </p>
          <ul className="list-disc list-inside space-y-0.5 text-xs text-gray-600">
            {opaResult.deny_reasons!.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        </div>
      )}

      {/* ── Rego rule checklist ────────────────────────────── */}
      <div>
        <div className="flex items-center gap-1.5 mb-2">
          <ShieldAlert className="h-3.5 w-3.5 text-indigo-500" />
          <span className="text-[11px] font-semibold uppercase tracking-wide text-gray-500">
            Rego Rule Checklist
          </span>
        </div>

        <div className="space-y-2">
          <RuleRow
            label="Zero Hardcoded Secrets"
            passed={!hasSecrets}
            detail={
              hasSecrets
                ? `${secrets_count} secret(s) detected in repository scan.`
                : "No hardcoded secrets were found in the scanned repository."
            }
          />
          <RuleRow
            label="No High-Severity Risks"
            passed={!hasHighRisk}
            detail={
              hasHighRisk
                ? `${risks.filter((r) => r.severity.toLowerCase() === "high").length} high-severity risk(s) identified by the LLM.`
                : "No high-severity risks were flagged during analysis."
            }
          />
        </div>
      </div>

      {/* ── Explainer text ─────────────────────────────────── */}
      <p className="text-[11px] leading-relaxed text-gray-400 border-t border-gray-100 pt-3">
        The Open Policy Agent (OPA) engine acts as a deterministic gatekeeper.
        It evaluates the LLM's structured output against immutable rules
        written in Rego to ensure human-defined safety thresholds are never
        bypassed.
      </p>
    </div>
  );
}
