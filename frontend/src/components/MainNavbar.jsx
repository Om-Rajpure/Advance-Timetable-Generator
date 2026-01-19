import { useState, useEffect } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import '../styles/navbar.css'

function MainNavbar() {
    const { logout, user } = useAuth()
    const location = useLocation()
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
    const [isScrolled, setIsScrolled] = useState(false)

    // Handle Scroll Effect
    useEffect(() => {
        const handleScroll = () => {
            setIsScrolled(window.scrollY > 20)
        }
        window.addEventListener('scroll', handleScroll)
        return () => window.removeEventListener('scroll', handleScroll)
    }, [])

    // Close mobile menu on route change
    useEffect(() => {
        setIsMobileMenuOpen(false)
    }, [location.pathname])

    // AUTH BYPASS: Hide on landing page if auth disabled
    const isAuthEnabled = true;
    const publicPaths = ['/', '/login', '/signup', '/attendance']
    if (publicPaths.includes(location.pathname)) {
        return null
    }

    const handleLogout = () => {
        logout()
        setIsMobileMenuOpen(false)
    }

    const toggleMenu = () => {
        setIsMobileMenuOpen(!isMobileMenuOpen)
    }

    // Nav Items Configuration
    const navItems = [
        { path: '/dashboard', label: 'Dashboard', icon: '📊' },
        { path: '/branch-setup', label: 'Branch Setup', icon: '⚙️' },
        { path: '/smart-input', label: 'Smart Input', icon: '🧠' }, // Assuming this is "Generate Timetable" flow
        { path: '/upload', label: 'Upload Timetable', icon: '📤' },
        { path: '/analytics', label: 'Analytics', icon: '📈' },
        { path: '/history', label: 'History', icon: 'clock' },
    ]

    // Only add Admin link if user is admin
    if (user && user.role === 'admin') {
        navItems.push({ path: '/admin', label: 'Admin Panel', icon: '🛡️' })
    }

    return (
        <>
            <nav className={`main-navbar ${isScrolled ? 'scrolled' : ''}`}>
                <div className="navbar-container">
                    {/* Brand */}
                    <div className="navbar-brand">
                        <span className="brand-logo">🗓️</span>
                        <span className="brand-name">Smart Timetable</span>
                    </div>

                    {/* Desktop Navigation */}
                    <div className="desktop-nav">
                        {navItems.map((item) => (
                            <NavLink
                                key={item.path}
                                to={item.path}
                                className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
                            >
                                {item.label}
                            </NavLink>
                        ))}
                    </div>

                    {/* Desktop Actions */}
                    <div className="desktop-actions">
                        {isAuthEnabled && (
                            <button onClick={handleLogout} className="btn-logout">
                                Logout
                            </button>
                        )}
                    </div>

                    {/* Mobile Toggle */}
                    <button
                        className={`mobile-toggle ${isMobileMenuOpen ? 'open' : ''}`}
                        onClick={toggleMenu}
                        aria-label="Toggle menu"
                    >
                        <span className="bar top"></span>
                        <span className="bar middle"></span>
                        <span className="bar bottom"></span>
                    </button>
                </div>
            </nav>

            {/* Mobile Drawer Overlay */}
            <div
                className={`mobile-overlay ${isMobileMenuOpen ? 'visible' : ''}`}
                onClick={() => setIsMobileMenuOpen(false)}
            />

            {/* Mobile Drawer */}
            <div className={`mobile-drawer ${isMobileMenuOpen ? 'open' : ''}`}>
                <div className="drawer-header">
                    <span className="drawer-title">Menu</span>
                    <button className="drawer-close" onClick={() => setIsMobileMenuOpen(false)}>×</button>
                </div>
                <div className="drawer-items">
                    {navItems.map((item, index) => (
                        <NavLink
                            key={item.path}
                            to={item.path}
                            className={({ isActive }) => `drawer-link ${isActive ? 'active' : ''}`}
                            style={{ animationDelay: `${index * 0.05}s` }} // Stagger animation
                        >
                            <span className="drawer-icon">{item.icon === 'clock' ? '🕰️' : item.icon}</span>
                            {item.label}
                        </NavLink>
                    ))}

                    <div className="drawer-divider" />

                    {isAuthEnabled && (
                        <button onClick={handleLogout} className="drawer-logout">
                            <span className="drawer-icon">🚪</span>
                            Logout
                        </button>
                    )}
                </div>
            </div>
        </>
    )
}

export default MainNavbar
