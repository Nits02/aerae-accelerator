import { useParams, Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import Dashboard from "./Dashboard";

/**
 * Route wrapper for /dashboard/:id
 * Extracts the job ID from the URL and passes it to Dashboard.
 */
export default function DashboardPage() {
  const { id } = useParams<{ id: string }>();

  if (!id) {
    return (
      <div className="text-center text-sm text-red-600">
        No job ID provided.{" "}
        <Link to="/" className="text-indigo-600 underline">
          Go back
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Link
        to="/"
        className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-indigo-600 transition"
      >
        <ArrowLeft className="h-4 w-4" />
        New Assessment
      </Link>

      <Dashboard jobId={id} />
    </div>
  );
}
