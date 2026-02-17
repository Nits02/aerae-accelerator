import { useEffect, useState, useRef } from "react";
import axios from "axios";
import { Loader2, CheckCircle, XCircle } from "lucide-react";
import Scorecard from "./Scorecard";

const API_BASE = "http://localhost:8000/api/v1/assess";
const POLL_INTERVAL = 3000;

interface DashboardProps {
  jobId: string;
}

type JobStatus = "Processing" | "Complete" | "Failed";

interface JobResult {
  trust_score: number;
  decision?: "allow" | "deny";
  [key: string]: unknown;
}

interface PollResponse {
  job_id: string;
  status: JobStatus;
  result?: JobResult;
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
    const MOCK_ENABLED = true;
    const MOCK_RESPONSE: PollResponse = {
      job_id: jobId,
      status: "Complete",
      result: { trust_score: 45, decision: "deny" },
    };

    async function poll() {
      try {
        // Use mock data when MOCK_ENABLED is true
        const data: PollResponse = MOCK_ENABLED
          ? MOCK_RESPONSE
          : (await axios.get<PollResponse>(
              `${API_BASE}/${jobId}`,
              { validateStatus: (s) => s === 200 || s === 202 },
            )).data;

        const httpStatus: number = MOCK_ENABLED ? 200 : 200;

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
  const decision = result?.decision ?? (trustScore > 50 ? "allow" : "deny");

  return (
    <div className="w-full max-w-md mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-2">
        <CheckCircle className="h-5 w-5 text-green-600" />
        <h3 className="text-lg font-semibold text-gray-800">
          Assessment Complete
        </h3>
      </div>

      {/* Scorecard – trust score + policy decision */}
      <Scorecard score={trustScore} decision={decision} />

      {/* Job meta */}
      <div className="text-center text-xs text-gray-400">
        Job <code className="bg-gray-100 px-1.5 py-0.5 rounded">{jobId}</code>
      </div>
    </div>
  );
}
