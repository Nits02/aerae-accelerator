import { BrowserRouter, Routes, Route } from 'react-router-dom'
import AssessmentForm from './components/AssessmentForm'
import DashboardPage from './components/DashboardPage'

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
        <div className="w-full max-w-lg space-y-8">
          <Routes>
            <Route path="/" element={<AssessmentForm />} />
            <Route path="/dashboard/:id" element={<DashboardPage />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  )
}

export default App
