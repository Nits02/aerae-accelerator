import { FileSearch, Database, BrainCircuit, ShieldCheck } from "lucide-react";
import type { LucideIcon } from "lucide-react";

/* ── Pipeline stage definition ───────────────────────────── */
interface Stage {
  icon: LucideIcon;
  label: string;
  subtext: string;
}

const STAGES: Stage[] = [
  {
    icon: FileSearch,
    label: "Ingestion & Scanning",
    subtext: "Parsed PDF via AI & Scanned Git for secrets.",
  },
  {
    icon: Database,
    label: "Policy Retrieval (RAG)",
    subtext: "Vectorized context and fetched relevant ethics policies.",
  },
  {
    icon: BrainCircuit,
    label: "LLM Risk Analysis",
    subtext: "GPT-4o evaluated context against policies.",
  },
  {
    icon: ShieldCheck,
    label: "OPA Policy Gate",
    subtext: "Deterministic rules evaluated the final risk payload.",
  },
];

/* ── Colour palette based on score & decision ────────────── */
function themeClasses(score: number, blocked: boolean) {
  if (blocked)
    return {
      iconBg: "bg-red-50",
      iconBorder: "border-red-400",
      iconText: "text-red-600",
      connector: "from-red-400 to-red-300",
      footer: "text-red-500",
      footerMsg: "⛔ Pipeline blocked by OPA policy gate",
    };
  if (score >= 80)
    return {
      iconBg: "bg-emerald-50",
      iconBorder: "border-emerald-400",
      iconText: "text-emerald-600",
      connector: "from-emerald-400 to-emerald-300",
      footer: "text-emerald-500",
      footerMsg: "✓ All stages completed successfully",
    };
  if (score >= 50)
    return {
      iconBg: "bg-amber-50",
      iconBorder: "border-amber-400",
      iconText: "text-amber-600",
      connector: "from-amber-400 to-amber-300",
      footer: "text-amber-500",
      footerMsg: "⚠ All stages completed — review recommended",
    };
  return {
    iconBg: "bg-red-50",
    iconBorder: "border-red-400",
    iconText: "text-red-600",
    connector: "from-red-400 to-red-300",
    footer: "text-red-500",
    footerMsg: "✗ All stages completed — significant risks detected",
  };
}

/* ── Props ────────────────────────────────────────────────── */
export interface PipelineStepperProps {
  /** Trust score (0-100) used to colour the pipeline */
  score: number;
  /** OPA decision — "deny" forces a red/blocked palette */
  decision: "allow" | "deny";
}

/* ── Component ───────────────────────────────────────────── */
export default function PipelineStepper({ score, decision }: PipelineStepperProps) {
  const blocked = decision === "deny";
  const theme = themeClasses(score, blocked);

  return (
    <div className="w-full rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
      {/* Title */}
      <h4 className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-5 text-center">
        AI Pipeline — How Your Assessment Was Produced
      </h4>

      {/* Horizontal stepper */}
      <div className="flex items-start justify-between gap-0">
        {STAGES.map((stage, idx) => {
          const Icon = stage.icon;
          const isLast = idx === STAGES.length - 1;

          return (
            <div key={stage.label} className="flex items-start flex-1 min-w-0">
              {/* Stage circle + text */}
              <div className="flex flex-col items-center text-center w-full">
                {/* Icon circle */}
                <div
                  className={`flex items-center justify-center h-12 w-12 rounded-full border-2 shadow-sm ${theme.iconBg} ${theme.iconBorder} ${theme.iconText}`}
                >
                  <Icon className="h-5 w-5" />
                </div>

                {/* Label */}
                <p className="mt-2 text-xs font-semibold text-gray-700 leading-tight">
                  {stage.label}
                </p>

                {/* Subtext */}
                <p className="mt-0.5 text-[11px] leading-snug text-gray-400 max-w-[140px]">
                  {stage.subtext}
                </p>
              </div>

              {/* Connector line (skip after last stage) */}
              {!isLast && (
                <div className="flex items-center mt-5 -mx-1 flex-shrink-0" aria-hidden>
                  <div
                    className={`h-0.5 w-8 rounded-full sm:w-12 bg-gradient-to-r ${theme.connector}`}
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Footer indicator */}
      <p className={`mt-5 text-center text-[11px] font-medium tracking-wide uppercase ${theme.footer}`}>
        {theme.footerMsg}
      </p>
    </div>
  );
}
