import { ShieldCheck, ShieldX } from "lucide-react";

/* ── Props ────────────────────────────────────────────────── */
export interface ScorecardProps {
  /** Final calculated trust score (0-100) */
  score: number;
  /** Allow / Deny decision returned from the OPA policy engine */
  decision: "allow" | "deny";
}

/* ── Colour helpers ───────────────────────────────────────── */
function scoreColor(score: number) {
  if (score > 80)
    return { ring: "text-green-500", bg: "bg-green-50", label: "text-green-700" };
  if (score > 50)
    return { ring: "text-yellow-500", bg: "bg-yellow-50", label: "text-yellow-700" };
  return { ring: "text-red-500", bg: "bg-red-50", label: "text-red-700" };
}

function scoreGrade(score: number) {
  if (score > 80) return "High Trust";
  if (score > 50) return "Medium Trust";
  return "Low Trust";
}

/* ── Component ────────────────────────────────────────────── */
export default function Scorecard({ score, decision }: ScorecardProps) {
  const radius = 70;
  const stroke = 10;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  const { ring, bg, label } = scoreColor(score);

  const isAllowed = decision === "allow";

  return (
    <div className={`flex flex-col items-center gap-6 rounded-2xl ${bg} p-8`}>
      {/* ── Circular trust-score gauge ──────────────────────── */}
      <svg width="180" height="180" className="-rotate-90">
        {/* track */}
        <circle
          cx="90"
          cy="90"
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={stroke}
          className="text-gray-200"
        />
        {/* progress arc */}
        <circle
          cx="90"
          cy="90"
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className={`${ring} transition-all duration-700 ease-out`}
        />
      </svg>

      {/* centred score text (overlaid on the SVG) */}
      <div className="-mt-[152px] mb-[60px] flex flex-col items-center">
        <span className={`text-5xl font-bold ${label}`}>{score}</span>
        <span className="text-sm text-gray-500 mt-1">/ 100</span>
      </div>

      {/* trust grade */}
      <span
        className={`text-sm font-semibold uppercase tracking-wider ${label}`}
      >
        {scoreGrade(score)}
      </span>

      {/* ── Policy-engine decision ─────────────────────────── */}
      <div
        className={`mt-2 flex items-center gap-2 rounded-full px-5 py-2 text-sm font-bold uppercase tracking-wide ${
          isAllowed
            ? "bg-green-100 text-green-800"
            : "bg-red-100 text-red-800"
        }`}
      >
        {isAllowed ? (
          <ShieldCheck className="h-5 w-5" />
        ) : (
          <ShieldX className="h-5 w-5" />
        )}
        {isAllowed ? "Allow" : "Deny"}
      </div>
    </div>
  );
}
