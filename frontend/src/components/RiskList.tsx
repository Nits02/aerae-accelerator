import { BookOpen } from "lucide-react";

/* ── Types ───────────────────────────────────────────────── */
interface Risk {
  category: string;
  severity: string;
  reason: string;
}

export interface RiskListProps {
  risks: Risk[];
  policies_matched: string[];
}

/* ── Severity badge ──────────────────────────────────────── */
function SeverityBadge({ severity }: { severity: string }) {
  const s = severity.toLowerCase();
  const cls =
    s === "high"
      ? "bg-red-100 text-red-700"
      : s === "medium"
        ? "bg-yellow-100 text-yellow-700"
        : "bg-green-100 text-green-700";
  return (
    <span
      className={`px-2 py-0.5 rounded-full text-xs font-semibold uppercase ${cls}`}
    >
      {severity}
    </span>
  );
}

/* ── Keyword-based policy matcher ────────────────────────── */
/**
 * Naively matches a risk to relevant policies by checking whether
 * any significant word from the risk category or reason appears in
 * the policy text.  Returns at most 2 matching snippets.
 */
function matchPolicies(risk: Risk, policies: string[]): string[] {
  const words = `${risk.category} ${risk.reason}`
    .toLowerCase()
    .split(/\W+/)
    .filter((w) => w.length > 3); // skip short/common words

  const scored = policies
    .map((p) => {
      const pLower = p.toLowerCase();
      const hits = words.filter((w) => pLower.includes(w)).length;
      return { text: p, hits };
    })
    .filter((s) => s.hits > 0)
    .sort((a, b) => b.hits - a.hits);

  return scored.slice(0, 2).map((s) => s.text);
}

/* ── Component ───────────────────────────────────────────── */
export default function RiskList({ risks, policies_matched }: RiskListProps) {
  if (risks.length === 0) return null;

  return (
    <div className="space-y-3">
      {risks.map((r, i) => {
        const grounded = matchPolicies(r, policies_matched);

        return (
          <div
            key={i}
            className="bg-white rounded-lg border border-gray-100 p-3 space-y-2"
          >
            {/* Top row: severity + category + reason */}
            <div className="flex items-start gap-3">
              <SeverityBadge severity={r.severity} />
              <div className="flex-1">
                <p className="font-medium text-gray-800 text-sm">
                  {r.category}
                </p>
                <p className="text-gray-500 text-xs mt-0.5">{r.reason}</p>
              </div>
            </div>

            {/* Grounded Policy Context (blockquote style) */}
            {grounded.length > 0 && (
              <div className="ml-[42px] rounded-md bg-gray-50 border-l-4 border-gray-300 px-3 py-2">
                <div className="flex items-center gap-1.5 mb-1">
                  <BookOpen className="h-3.5 w-3.5 text-purple-500" />
                  <span className="text-[11px] font-semibold uppercase tracking-wide text-gray-500">
                    Grounded Policy Context
                  </span>
                </div>
                <p className="text-[11px] text-gray-500 mb-1.5">
                  This risk was flagged because it violated one of the retrieved
                  AI ethics guidelines:
                </p>
                <ul className="space-y-1">
                  {grounded.map((policy, j) => (
                    <li
                      key={j}
                      className="text-xs text-purple-800 bg-purple-50 rounded px-2 py-1.5 border border-purple-100 leading-relaxed"
                    >
                      "{policy}"
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Fallback when no policies could be matched */}
            {grounded.length === 0 && policies_matched.length > 0 && (
              <div className="ml-[42px] rounded-md bg-gray-50 border-l-4 border-gray-200 px-3 py-2">
                <p className="text-[11px] text-gray-400 italic">
                  No specific policy snippet could be linked to this risk. The
                  LLM flagged it based on general ethical reasoning.
                </p>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
