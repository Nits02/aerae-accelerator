import { useEffect, useState, useRef } from "react";
import axios from "axios";
import {
  Loader2,
  CheckCircle,
  XCircle,
  GitBranch,
  FileText,
  AlertTriangle,
  Shield,
  BookOpen,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import Scorecard from "./Scorecard";

const API_BASE = "http://localhost:8000/api/v1/assess";
const POLL_INTERVAL = 3000;

interface DashboardProps {
  jobId: string;
}

type JobStatus = "Processing" | "Complete" | "Failed";

interface Risk {
  category: string;
  severity: string;
  reason: string;
}

interface CodeMetadata {
  files?: string[];
  files_count?: number;
  extensions?: Record<string, number>;
  secrets_found?: number;
  secret_scan_successful?: boolean;
  secret_findings?: unknown[];
}

interface PdfAnalysis {
  project_purpose?: string;
  data_types_used?: string[];
  potential_risks?: string[];
  source?: string;
  fallback_used?: boolean;
}

interface OpaResult {
  allow?: boolean;
  deny_reasons?: string[];
  opa_unavailable?: boolean;
}

interface JobResult {
  trust_score: number;
  decision?: "allow" | "deny";
  github_url?: string;
  code_metadata?: CodeMetadata;
  pdf_analysis?: PdfAnalysis;
  risks?: Risk[];
  policies_matched?: string[];
  opa_result?: OpaResult;
  [key: string]: unknown;
}

interface PollResponse {
  job_id: string;
  status: JobStatus;
  result?: JobResult;
}

/* ── Collapsible section ─────────────────────────────────── */
function Section({
  icon,
  title,
  defaultOpen = false,
  children,
}: {
  icon: React.ReactNode;
  title: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border border-gray-200 rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-2 px-4 py-3 bg-gray-50 hover:bg-gray-100 transition text-left"
      >
        {icon}
        <span className="flex-1 text-sm font-semibold text-gray-700">{title}</span>
        {open ? (
          <ChevronUp className="h-4 w-4 text-gray-400" />
        ) : (
          <ChevronDown className="h-4 w-4 text-gray-400" />
        )}
      </button>
      {open && <div className="px-4 py-3 text-sm text-gray-600 space-y-2">{children}</div>}
    </div>
  );
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
    <span className={`px-2 py-0.5 rounded-full text-xs font-semibold uppercase ${cls}`}>
      {severity}
    </span>
  );
}

/* ── Main Dashboard component ────────────────────────────── */
export default function Dashboard({ jobId }: DashboardProps) {
  const [status, setStatus] = useState<JobStatus>("Processing");
  const [result, setResult] = useState<JobResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    let cancelled = false;

    // ── MOCK: hardcoded response for testing (score = 45 → red) ──
    const MOCK_ENABLED = false;
    const MOCK_RESPONSE: PollResponse = {
      job_id: jobId,
      status: "Complete",
      result: { trust_score: 45, decision: "deny" },
    };

    async function poll() {
      try {
        let data: PollResponse;
        let httpStatus: number;

        if (MOCK_ENABLED) {
          data = MOCK_RESPONSE;
          httpStatus = 200;
        } else {
          const response = await axios.get<PollResponse>(
            `${API_BASE}/${jobId}`,
            { validateStatus: (s) => s === 200 || s === 202 },
          );
          data = response.data;
          httpStatus = response.status;
        }

        if (cancelled) return;

        if (httpStatus === 202) {
          setStatus("Processing");
          return; // keep polling
        }

        // 200 — Complete or Failed
        setStatus(data.status);

        if (data.status === "Complete" && data.result) {
          setResult(data.result);
        } else if (data.status === "Failed") {
          setError(
            (data.result as Record<string, string> | undefined)?.error ??
              "Assessment failed.",
          );
        }

        // stop polling once terminal state reached
        if (timerRef.current) clearInterval(timerRef.current);
      } catch (err: unknown) {
        if (cancelled) return;
        if (axios.isAxiosError(err)) {
          setError(err.response?.data?.detail ?? err.message);
        } else {
          setError("Unexpected error while polling.");
        }
        if (timerRef.current) clearInterval(timerRef.current);
      }
    }

    // initial immediate poll, then every POLL_INTERVAL ms
    poll();
    timerRef.current = setInterval(poll, POLL_INTERVAL);

    return () => {
      cancelled = true;
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [jobId]);

  /* ── Processing state ─────────────────────────────────── */
  if (status === "Processing") {
    return (
      <div className="flex flex-col items-center justify-center gap-4 p-10">
        <Loader2 className="h-10 w-10 text-indigo-500 animate-spin" />
        <p className="text-sm text-gray-600">
          Analysing… polling every {POLL_INTERVAL / 1000}s
        </p>
        <code className="text-xs text-gray-400">{jobId}</code>
      </div>
    );
  }

  /* ── Failed state ─────────────────────────────────────── */
  if (status === "Failed" || error) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-2xl bg-red-50 border border-red-200 p-8">
        <XCircle className="h-10 w-10 text-red-500" />
        <p className="text-sm font-medium text-red-700">Assessment Failed</p>
        <p className="text-xs text-red-600 max-w-md text-center">{error}</p>
      </div>
    );
  }

  /* ── Completed state ──────────────────────────────────── */
  const trustScore = result?.trust_score ?? 0;
  const opaAllow = result?.opa_result?.allow;
  const decision =
    result?.decision ??
    (opaAllow !== undefined ? (opaAllow ? "allow" : "deny") : trustScore > 50 ? "allow" : "deny");

  const codeMetadata = result?.code_metadata;
  const pdfAnalysis = result?.pdf_analysis;
  const risks = result?.risks ?? [];
  const policies = result?.policies_matched ?? [];
  const opaResult = result?.opa_result;

  return (
    <div className="w-full max-w-2xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-2">
        <CheckCircle className="h-5 w-5 text-green-600" />
        <h3 className="text-lg font-semibold text-gray-800">
          Assessment Complete
        </h3>
      </div>

      {/* Scorecard – trust score + policy decision */}
      <Scorecard score={trustScore} decision={decision} />

      {/* ── Risks ─────────────────────────────────────────── */}
      {risks.length > 0 && (
        <Section
          icon={<AlertTriangle className="h-4 w-4 text-yellow-500" />}
          title={`Identified Risks (${risks.length})`}
          defaultOpen
        >
          <div className="space-y-3">
            {risks.map((r, i) => (
              <div key={i} className="flex items-start gap-3 bg-white rounded-lg border border-gray-100 p-3">
                <SeverityBadge severity={r.severity} />
                <div className="flex-1">
                  <p className="font-medium text-gray-800 text-sm">{r.category}</p>
                  <p className="text-gray-500 text-xs mt-0.5">{r.reason}</p>
                </div>
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* ── OPA Policy Decision ───────────────────────────── */}
      {opaResult && (
        <Section
          icon={<Shield className="h-4 w-4 text-indigo-500" />}
          title="OPA Policy Evaluation"
          defaultOpen
        >
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="text-xs font-medium text-gray-500 uppercase">Decision:</span>
              <span
                className={`px-2 py-0.5 rounded-full text-xs font-bold uppercase ${
                  opaResult.allow ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
                }`}
              >
                {opaResult.allow ? "Allow" : "Deny"}
              </span>
              {opaResult.opa_unavailable && (
                <span className="text-xs text-amber-600 italic">(OPA server was unavailable)</span>
              )}
            </div>
            {(opaResult.deny_reasons ?? []).length > 0 && (
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase mb-1">Reasons:</p>
                <ul className="list-disc list-inside space-y-0.5 text-xs text-gray-600">
                  {opaResult.deny_reasons!.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </Section>
      )}

      {/* ── PDF Analysis ──────────────────────────────────── */}
      {pdfAnalysis && (
        <Section
          icon={<FileText className="h-4 w-4 text-blue-500" />}
          title="Document Analysis"
          defaultOpen
        >
          <div className="space-y-3">
            {pdfAnalysis.project_purpose && (
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase">Project Purpose</p>
                <p className="text-sm text-gray-700 mt-0.5">{pdfAnalysis.project_purpose}</p>
              </div>
            )}
            {(pdfAnalysis.data_types_used ?? []).length > 0 && (
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase">Data Types Used</p>
                <div className="flex flex-wrap gap-1.5 mt-1">
                  {pdfAnalysis.data_types_used!.map((dt, i) => (
                    <span key={i} className="bg-blue-50 text-blue-700 px-2 py-0.5 rounded text-xs">
                      {dt}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {(pdfAnalysis.potential_risks ?? []).length > 0 && (
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase">Potential Risks (from PDF)</p>
                <ul className="list-disc list-inside text-xs text-gray-600 mt-0.5 space-y-0.5">
                  {pdfAnalysis.potential_risks!.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              </div>
            )}
            {pdfAnalysis.source && (
              <p className="text-xs text-gray-400">
                Analysed by: <span className="font-medium">{pdfAnalysis.source}</span>
                {pdfAnalysis.fallback_used && " (fallback)"}
              </p>
            )}
          </div>
        </Section>
      )}

      {/* ── Code / Repository ─────────────────────────────── */}
      {codeMetadata && (
        <Section
          icon={<GitBranch className="h-4 w-4 text-gray-500" />}
          title="Repository Scan"
        >
          <div className="space-y-2">
            {result?.github_url && (
              <p className="text-xs">
                <span className="font-medium text-gray-500">URL:</span>{" "}
                <a
                  href={result.github_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-indigo-600 underline"
                >
                  {result.github_url}
                </a>
              </p>
            )}
            <div className="flex gap-4 text-xs">
              <span>
                <span className="font-medium text-gray-500">Files:</span>{" "}
                {codeMetadata.files_count ?? 0}
              </span>
              <span>
                <span className="font-medium text-gray-500">Secrets found:</span>{" "}
                <span
                  className={
                    (codeMetadata.secrets_found ?? 0) > 0 ? "text-red-600 font-bold" : "text-green-600"
                  }
                >
                  {codeMetadata.secrets_found ?? 0}
                </span>
              </span>
            </div>
            {codeMetadata.extensions && Object.keys(codeMetadata.extensions).length > 0 && (
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase mb-1">File Extensions</p>
                <div className="flex flex-wrap gap-1.5">
                  {Object.entries(codeMetadata.extensions).map(([ext, count]) => (
                    <span key={ext} className="bg-gray-100 text-gray-600 px-2 py-0.5 rounded text-xs">
                      {ext} ({count})
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </Section>
      )}

      {/* ── Matched Policies ──────────────────────────────── */}
      {policies.length > 0 && (
        <Section
          icon={<BookOpen className="h-4 w-4 text-purple-500" />}
          title={`Matched Policies (${policies.length})`}
        >
          <ul className="space-y-1.5">
            {policies.map((p, i) => (
              <li
                key={i}
                className="bg-purple-50 rounded-lg px-3 py-2 text-xs text-purple-800 border border-purple-100"
              >
                {p}
              </li>
            ))}
          </ul>
        </Section>
      )}

      {/* Job meta */}
      <div className="text-center text-xs text-gray-400">
        Job <code className="bg-gray-100 px-1.5 py-0.5 rounded">{jobId}</code>
      </div>
    </div>
  );
}
