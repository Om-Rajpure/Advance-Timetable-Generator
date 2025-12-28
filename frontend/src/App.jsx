import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './auth/AuthContext'
import ProtectedRoute from './auth/ProtectedRoute'
import WorkflowGuard from './components/WorkflowGuard'
import MainNavbar from './components/MainNavbar'
import DevBanner from './components/DevBanner'

// Pages
import LandingPage from './pages/LandingPage'
import Login from './pages/Login'
import Signup from './pages/Signup'
import Dashboard from './pages/Dashboard'
import BranchSetup from './pages/BranchSetup'
import SmartInput from './pages/SmartInput'
import Analytics from './pages/Analytics'
import Export from './pages/Export'
import History from './pages/History'
import TimetableUpload from './pages/TimetableUpload'
import EditableTimetable from './pages/EditableTimetable'
import TestEditPage from './pages/TestEditPage'
import WhatIfSimulation from './pages/WhatIfSimulation'

function App() {
  return (
    <Router>
      <AuthProvider>
        <DevBanner />
        <MainNavbar />

        <Routes>
          {/* Public Routes */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />

          {/* Protected Routes */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />

          <Route
            path="/branch-setup"
            element={
              <ProtectedRoute>
                <BranchSetup />
              </ProtectedRoute>
            }
          />

          <Route
            path="/smart-input"
            element={
              <ProtectedRoute>
                <WorkflowGuard requiredStep="branchSetup">
                  <SmartInput />
                </WorkflowGuard>
              </ProtectedRoute>
            }
          />

          <Route
            path="/analytics"
            element={
              <ProtectedRoute>
                <Analytics />
              </ProtectedRoute>
            }
          />

          <Route
            path="/export"
            element={
              <ProtectedRoute>
                <Export />
              </ProtectedRoute>
            }
          />

          <Route
            path="/history"
            element={
              <ProtectedRoute>
                <History />
              </ProtectedRoute>
            }
          />

          <Route
            path="/upload"
            element={
              <ProtectedRoute>
                <TimetableUpload />
              </ProtectedRoute>
            }
          />

          <Route
            path="/edit-timetable"
            element={
              <ProtectedRoute>
                <EditableTimetable />
              </ProtectedRoute>
            }
          />

          <Route
            path="/test-edit"
            element={
              <ProtectedRoute>
                <TestEditPage />
              </ProtectedRoute>
            }
          />

          <Route
            path="/what-if-simulation"
            element={
              <ProtectedRoute>
                <WhatIfSimulation />
              </ProtectedRoute>
            }
          />

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </Router>
  )
}

export default App
