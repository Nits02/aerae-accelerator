import { Receipt } from "lucide-react";

/* ── Types ───────────────────────────────────────────────── */
interface Risk {
  category: string;
  severity: string;
  reason: string;
}

export interface ScoreBreakdownProps {
  risks: Risk[];
  secrets_count: number;
}

/* ── Deduction constants (mirror backend scoring.py) ────── */
const DEDUCTION_HIGH = 25;
const DEDUCTION_MEDIUM = 10;
const DEDUCTION_PER_SECRET = 15;
const BASE_SCORE = 100;

/* ── Ledger row helper ───────────────────────────────────── */
function LedgerRow({
  label,
  value,
  isDeduction = false,
  bold = false,
}: {
  label: string;
  value: string;
  isDeduction?: boolean;
  bold?: boolean;
}) {
  return (
    <div
      className={`flex items-baseline justify-between gap-2 ${
        bold ? "font-bold text-gray-900" : "text-gray-600"
      }`}
    >
      {/* Label + dotted leader */}
      <span className="truncate text-sm">{label}</span>
      <span
        className="flex-1 border-b border-dotted border-gray-300 mx-1 min-w-[20px]"
        aria-hidden
      />
      {/* Value */}
      <span
        className={`text-sm whitespace-nowrap tabular-nums ${
          isDeduction ? "text-red-500 font-semibold" : ""
        } ${bold ? "text-base" : ""}`}
      >
        {value}
      </span>
    </div>
  );
}

/* ── Component ───────────────────────────────────────────── */
export default function ScoreBreakdown({
  risks,
  secrets_count,
}: ScoreBreakdownProps) {
  /* Build deduction rows */
  const deductions: { label: string; amount: number }[] = [];

  risks.forEach((r) => {
    const sev = r.severity.toLowerCase();
    if (sev === "high") {
      deductions.push({
        label: `High Severity Risk: ${r.category}`,
        amount: DEDUCTION_HIGH,
      });
    } else if (sev === "medium") {
      deductions.push({
        label: `Medium Severity Risk: ${r.category}`,
        amount: DEDUCTION_MEDIUM,
      });
    }
  });

  if (secrets_count > 0) {
    deductions.push({
      label: `Hardcoded Secrets Found (${secrets_count})`,
      amount: secrets_count * DEDUCTION_PER_SECRET,
    });
  }

  const totalDeduction = deductions.reduce((sum, d) => sum + d.amount, 0);
  const finalScore = Math.max(BASE_SCORE - totalDeduction, 0);

  return (
    <div className="flex-1 min-w-[260px] rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <Receipt className="h-4 w-4 text-gray-400" />
        <h4 className="text-xs font-semibold uppercase tracking-wider text-gray-400">
          Score Breakdown
        </h4>
      </div>

      <div className="space-y-2.5">
        {/* Base score */}
        <LedgerRow label="Base Trust Score" value="100" />

        {/* Deductions */}
        {deductions.map((d, i) => (
          <LedgerRow
            key={i}
            label={d.label}
            value={`-${d.amount}`}
            isDeduction
          />
        ))}

        {deductions.length === 0 && (
          <p className="text-xs text-gray-400 italic">No deductions applied.</p>
        )}

        {/* Divider */}
        <div className="border-t-2 border-gray-800 my-1" />

        {/* Final score */}
        <LedgerRow
          label="Final Calculated Score"
          value={String(finalScore)}
          bold
        />
      </div>
    </div>
  );
}
