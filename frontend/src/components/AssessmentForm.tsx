import { useState, useRef, type FormEvent, type ChangeEvent } from "react";
import axios from "axios";
import { Upload, Github, Play, CheckCircle, AlertCircle } from "lucide-react";

const API_URL = "http://localhost:8000/api/v1/assess";

interface AssessmentFormProps {
  onJobCreated?: (jobId: string) => void;
}

export default function AssessmentForm({ onJobCreated }: AssessmentFormProps) {
  const [githubUrl, setGithubUrl] = useState("");
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] ?? null;
    setPdfFile(file);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setJobId(null);

    if (!githubUrl.trim()) {
      setError("Please enter a GitHub repository URL.");
      return;
    }
    if (!pdfFile) {
      setError("Please upload a PDF document.");
      return;
    }

    setLoading(true);
    try {
      // ── MOCK: skip real API call for testing ──
      const MOCK_ENABLED = true;

      let jobIdResult: string;
      if (MOCK_ENABLED) {
        await new Promise((r) => setTimeout(r, 500)); // simulate latency
        jobIdResult = "mock-job-" + crypto.randomUUID().slice(0, 8);
      } else {
        const formData = new FormData();
        formData.append("github_url", githubUrl.trim());
        formData.append("file", pdfFile);

        const { data } = await axios.post<{ job_id: string; status: string }>(
          API_URL,
          formData,
          { headers: { "Content-Type": "multipart/form-data" } }
        );
        jobIdResult = data.job_id;
      }

      setJobId(jobIdResult);
      onJobCreated?.(jobIdResult);
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.detail ?? err.message);
      } else {
        setError("An unexpected error occurred.");
      }
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setGithubUrl("");
    setPdfFile(null);
    setJobId(null);
    setError(null);
    onJobCreated?.(null as unknown as string);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  return (
    <div className="w-full bg-white rounded-2xl shadow-lg border border-gray-200 overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-indigo-600 to-violet-600 px-6 py-5">
          <h2 className="text-xl font-semibold text-white tracking-tight">
            AERAE Assessment
          </h2>
          <p className="text-indigo-200 text-sm mt-1">
            Provide a GitHub repo and architecture PDF to begin.
          </p>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {/* GitHub URL */}
          <div>
            <label
              htmlFor="github-url"
              className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-1.5"
            >
              <Github className="h-4 w-4 text-gray-500" />
              GitHub Repository URL
            </label>
            <input
              id="github-url"
              type="url"
              placeholder="https://github.com/owner/repo"
              value={githubUrl}
              onChange={(e) => setGithubUrl(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm
                         placeholder:text-gray-400 focus:border-indigo-500 focus:ring-2
                         focus:ring-indigo-200 outline-none transition"
            />
          </div>

          {/* PDF Upload */}
          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-1.5">
              <Upload className="h-4 w-4 text-gray-500" />
              Architecture PDF
            </label>
            <div
              onClick={() => fileInputRef.current?.click()}
              className="flex items-center justify-center gap-2 cursor-pointer rounded-lg
                         border-2 border-dashed border-gray-300 bg-gray-50 px-4 py-6
                         hover:border-indigo-400 hover:bg-indigo-50 transition"
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf"
                onChange={handleFileChange}
                className="hidden"
              />
              {pdfFile ? (
                <span className="text-sm text-indigo-700 font-medium truncate max-w-xs">
                  {pdfFile.name}
                </span>
              ) : (
                <span className="text-sm text-gray-500">
                  Click to select a PDF file
                </span>
              )}
            </div>
          </div>

          {/* Error */}
          {error && (
            <div className="flex items-start gap-2 rounded-lg bg-red-50 border border-red-200 px-4 py-3">
              <AlertCircle className="h-5 w-5 text-red-500 shrink-0 mt-0.5" />
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          {/* Success */}
          {jobId && (
            <div className="flex items-start gap-2 rounded-lg bg-green-50 border border-green-200 px-4 py-3">
              <CheckCircle className="h-5 w-5 text-green-600 shrink-0 mt-0.5" />
              <div className="text-sm">
                <p className="text-green-800 font-medium">Assessment started!</p>
                <p className="text-green-700 mt-0.5">
                  Job ID:{" "}
                  <code className="bg-green-100 px-1.5 py-0.5 rounded text-xs font-mono">
                    {jobId}
                  </code>
                </p>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center gap-3 pt-2">
            <button
              type="submit"
              disabled={loading}
              className="flex-1 flex items-center justify-center gap-2 rounded-lg
                         bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white
                         hover:bg-indigo-700 focus:ring-2 focus:ring-indigo-300
                         disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              {loading ? (
                <>
                  <span className="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Running…
                </>
              ) : (
                <>
                  <Play className="h-4 w-4" />
                  Run Assessment
                </>
              )}
            </button>

            {jobId && (
              <button
                type="button"
                onClick={resetForm}
                className="rounded-lg border border-gray-300 px-4 py-2.5 text-sm
                           font-medium text-gray-700 hover:bg-gray-100 transition"
              >
                New
              </button>
            )}
          </div>
        </form>
    </div>
  );
}
