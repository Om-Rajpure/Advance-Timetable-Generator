import { Navigate, useLocation } from 'react-router-dom'
import { useAuth, isAuthEnabled } from './AuthContext'

// TODO: Replace with real backend authentication check
// This component guards protected routes and redirects to login if not authenticated

const ProtectedRoute = ({ children }) => {
    const { isAuthenticated } = useAuth()
    const location = useLocation()

    // ========================================
    // 🚧 AUTH BYPASS FOR DEVELOPMENT MODE 🚧
    // ========================================
    // When authentication is disabled, allow all access
    if (!isAuthEnabled) {
        return children
    }
    // ========================================

    // Real authentication check (when isAuthEnabled = true)
    if (!isAuthenticated) {
        // Redirect to login, but save the attempted URL for redirecting back after login
        return <Navigate to="/login" state={{ from: location.pathname }} replace />
    }

    return children
}

export default ProtectedRoute
