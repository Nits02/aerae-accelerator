import { useState } from 'react'
import AssessmentForm from './components/AssessmentForm'
import Dashboard from './components/Dashboard'

function App() {
  const [jobId, setJobId] = useState<string | null>(null)

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
      <div className="w-full max-w-lg space-y-8">
        <AssessmentForm onJobCreated={setJobId} />
        {jobId && <Dashboard jobId={jobId} />}
      </div>
    </div>
  )
}

export default App
