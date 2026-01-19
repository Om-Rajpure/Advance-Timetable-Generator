import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './auth/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import WorkflowGuard from './components/WorkflowGuard'
import AdminRoute from './components/AdminRoute'

// Layouts
import UserLayout from './layouts/UserLayout'
import AdminLayout from './layouts/AdminLayout'

// Pages
import LandingPage from './pages/LandingPage'
import LoginPage from './pages/Login'
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
import Attendance from './pages/Attendance'

// Admin Pages
import AdminHome from './pages/admin/AdminHome'
import AdminUsers from './pages/admin/AdminUsers'
import AdminTimetables from './pages/admin/AdminTimetables'

function App() {
  return (
    <Router future={{ v7_startTransition: true }}>
      <AuthProvider>
        <Routes>
          {/* USER APPLICATION */}
          <Route element={<UserLayout />}>
            {/* Public */}
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/attendance" element={<Attendance />} />

            {/* Protected User Routes */}
            <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
            <Route path="/branch-setup" element={<ProtectedRoute><BranchSetup /></ProtectedRoute>} />
            <Route path="/smart-input" element={<ProtectedRoute><WorkflowGuard requiredStep="branchSetup"><SmartInput /></WorkflowGuard></ProtectedRoute>} />
            <Route path="/analytics" element={<ProtectedRoute><Analytics /></ProtectedRoute>} />
            <Route path="/export" element={<ProtectedRoute><Export /></ProtectedRoute>} />
            <Route path="/history" element={<ProtectedRoute><History /></ProtectedRoute>} />
            <Route path="/upload" element={<ProtectedRoute><TimetableUpload /></ProtectedRoute>} />

            {/* Timetable Editing Routes */}
            <Route path="/timetable" element={<ProtectedRoute><EditableTimetable /></ProtectedRoute>} />
            <Route path="/edit-timetable" element={<ProtectedRoute><EditableTimetable /></ProtectedRoute>} />
            <Route path="/test-edit" element={<ProtectedRoute><TestEditPage /></ProtectedRoute>} />
            <Route path="/what-if-simulation" element={<ProtectedRoute><WhatIfSimulation /></ProtectedRoute>} />
          </Route>

          {/* ADMIN APPLICATION (Isolated) */}
          <Route path="/admin" element={<AdminRoute><AdminLayout /></AdminRoute>}>
            <Route index element={<AdminHome />} />
            <Route path="users" element={<AdminUsers />} />
            <Route path="timetables" element={<AdminTimetables />} />

            {/* Admin Fallback */}
            <Route path="*" element={<Navigate to="/admin" replace />} />
          </Route>

          {/* Global Fallback */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </Router>
  )
}

export default App
