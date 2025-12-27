import { NavLink, useLocation } from 'react-router-dom'
import { useAuth, isAuthEnabled } from '../auth/AuthContext'
import '../styles/navbar.css'

function MainNavbar() {
    const { logout, user } = useAuth()
    const location = useLocation()

    // AUTH BYPASS: When auth is disabled, only hide on landing page
    // When auth is enabled, hide on all public pages
    const publicPaths = !isAuthEnabled ? ['/'] : ['/', '/login', '/signup']
    if (publicPaths.includes(location.pathname)) {
        return null
    }

    const handleLogout = () => {
        logout()
    }

    return (
        <nav className="main-navbar">
            <div className="navbar-container">
                {/* Left: Logo/Brand */}
                <div className="navbar-brand">
                    <span className="brand-icon">🗓️</span>
                    <span className="brand-text">Smart Timetable</span>
                </div>

                {/* Center: Navigation Links */}
                <div className="navbar-links">
                    <NavLink
                        to="/dashboard"
                        className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}
                    >
                        Dashboard
                    </NavLink>
                    <NavLink
                        to="/branch-setup"
                        className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}
                    >
                        Branch Setup
                    </NavLink>
                    <NavLink
                        to="/generate"
                        className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}
                    >
                        Generate Timetable
                    </NavLink>
                    <NavLink
                        to="/upload"
                        className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}
                    >
                        Upload Timetable
                    </NavLink>
                    <NavLink
                        to="/edit"
                        className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}
                    >
                        Edit Timetable
                    </NavLink>
                    <NavLink
                        to="/analytics"
                        className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}
                    >
                        Analytics
                    </NavLink>
                    <NavLink
                        to="/history"
                        className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}
                    >
                        History
                    </NavLink>
                    <NavLink
                        to="/export"
                        className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}
                    >
                        Export
                    </NavLink>
                </div>

                {/* Right: User Info & Logout */}
                <div className="navbar-actions">
                    <span className="user-info">👤 {user?.name || 'User'}</span>
                    {/* AUTH BYPASS: Hide logout button when auth is disabled */}
                    {isAuthEnabled && (
                        <button onClick={handleLogout} className="logout-button">
                            Logout
                        </button>
                    )}
                </div>
            </div>
        </nav>
    )
}

export default MainNavbar
