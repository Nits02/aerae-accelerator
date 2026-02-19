import { ShieldCheck, Ban } from "lucide-react";

/* ── Props ────────────────────────────────────────────────── */
export interface ScorecardProps {
  /** Final calculated trust score (0-100) */
  score: number;
  /** Allow / Deny decision returned from the OPA policy engine */
  decision: "allow" | "deny";
}

/* ── Colour helpers ───────────────────────────────────────── */
function scoreColor(score: number, blocked: boolean) {
  // When OPA blocks, force red regardless of score
  if (blocked)
    return { ring: "text-red-500", bg: "bg-red-50", label: "text-red-700" };
  if (score >= 80)
    return { ring: "text-emerald-500", bg: "bg-emerald-50", label: "text-emerald-700" };
  if (score >= 50)
    return { ring: "text-amber-500", bg: "bg-amber-50", label: "text-amber-700" };
  return { ring: "text-red-500", bg: "bg-red-50", label: "text-red-700" };
}

function scoreGrade(score: number, blocked: boolean) {
  if (blocked) return "Blocked";
  if (score >= 80) return "High Trust";
  if (score >= 50) return "Medium Trust";
  return "Low Trust";
}

/* ── Component ────────────────────────────────────────────── */
export default function Scorecard({ score, decision }: ScorecardProps) {
  const radius = 70;
  const stroke = 10;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  const isAllowed = decision === "allow";
  const blocked = !isAllowed;
  const { ring, bg, label } = scoreColor(score, blocked);

  return (
    <div className={`flex-1 min-w-[260px] flex flex-col items-center gap-6 rounded-2xl ${bg} p-8`}>
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
        {scoreGrade(score, blocked)}
      </span>

      {/* ── Policy-engine decision ─────────────────────────── */}
      {blocked ? (
        <div className="mt-2 flex items-center gap-2 rounded-full bg-red-600 px-5 py-2 text-sm font-bold uppercase tracking-wide text-white shadow-md animate-pulse">
          <Ban className="h-5 w-5" />
          Blocked
        </div>
      ) : (
        <div className="mt-2 flex items-center gap-2 rounded-full bg-emerald-100 text-emerald-800 px-5 py-2 text-sm font-bold uppercase tracking-wide">
          <ShieldCheck className="h-5 w-5" />
          Allow
        </div>
      )}
    </div>
  );
}
