import { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import '../styles/navbar.css'
import DeveloperProfile from './DeveloperProfile'

function Navbar() {
    const [isScrolled, setIsScrolled] = useState(false)
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
    const [showDevProfile, setShowDevProfile] = useState(false)
    const { user } = useAuth()
    const location = useLocation()

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

    const scrollToSection = (sectionId) => {
        setIsMobileMenuOpen(false)
        const element = document.getElementById(sectionId)
        if (element) {
            element.scrollIntoView({ behavior: 'smooth' })
        }
    }

    const toggleMenu = () => {
        setIsMobileMenuOpen(!isMobileMenuOpen)
    }

    // Navigation Items (Pre-login)
    const navItems = [
        { id: 'home', label: 'Home' },
        { id: 'features', label: 'Features' },
        { id: 'how-it-works', label: 'How It Works' },
        { id: 'attendance', label: 'Attendance', path: '/attendance' },
    ]

    return (
        <>
            <nav className={`main-navbar landing-navbar ${isScrolled ? 'scrolled' : ''}`}>
                <div className="navbar-container">
                    {/* Brand */}
                    <Link to="/" className="navbar-brand">
                        <span className="brand-logo">🗓️</span>
                        <span className="brand-name">Smart Timetable</span>
                    </Link>

                    {/* Desktop Navigation */}
                    <div className="desktop-nav">
                        {navItems.map((item) => (
                            item.path ? (
                                <Link
                                    key={item.id}
                                    to={item.path}
                                    className="nav-link"
                                    style={{ background: 'none', border: 'none', cursor: 'pointer', display: 'inline-block' }}
                                >
                                    {item.label}
                                </Link>
                            ) : (
                                <button
                                    key={item.id}
                                    onClick={() => scrollToSection(item.id)}
                                    className="nav-link"
                                    style={{ background: 'none', border: 'none', cursor: 'pointer' }}
                                >
                                    {item.label}
                                </button>
                            )
                        ))}
                    </div>

                    <div className="navbar-right-side" style={{ display: 'flex', alignItems: 'center', gap: '15px', marginLeft: 'auto' }}>
                        {/* Desktop Actions */}
                        <div className="desktop-actions" style={{ marginLeft: 0 }}>
                            {!user && (
                                <Link to="/login" className="btn-login">
                                    Login
                                </Link>
                            )}
                        </div>

                        {/* Developer Avatar (Visible on Desktop & Mobile) */}
                        <div
                            className="nav-dev-trigger"
                            onClick={() => setShowDevProfile(true)}
                            title="Developer Info"
                        >
                            <img
                                src="https://github.com/Om-Rajpure.png"
                                alt="Dev"
                                className="nav-dev-img"
                                onError={(e) => { e.target.src = "https://ui-avatars.com/api/?name=Om+Rajpure&background=6366f1&color=fff"; }}
                            />
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
                </div>
            </nav>

            {/* Developer Profile Modal */}
            <DeveloperProfile
                isOpen={showDevProfile}
                onClose={() => setShowDevProfile(false)}
            />

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
                        item.path ? (
                            <Link
                                key={item.id}
                                to={item.path}
                                className="drawer-link"
                                onClick={() => setIsMobileMenuOpen(false)}
                                style={{
                                    animationDelay: `${index * 0.05}s`,
                                    width: '100%',
                                    justifyContent: 'flex-start'
                                }}
                            >
                                {item.label}
                            </Link>
                        ) : (
                            <button
                                key={item.id}
                                onClick={() => scrollToSection(item.id)}
                                className="drawer-link"
                                style={{
                                    animationDelay: `${index * 0.05}s`,
                                    background: 'none',
                                    border: 'none',
                                    width: '100%',
                                    justifyContent: 'flex-start',
                                    cursor: 'pointer'
                                }}
                            >
                                {item.label}
                            </button>
                        )
                    ))}

                    <div className="drawer-divider" />

                    {!user && (
                        <Link to="/login" className="drawer-link" style={{ animationDelay: '0.2s' }}>
                            <span className="drawer-icon">🔐</span>
                            Login
                        </Link>
                    )}
                </div>
            </div>
        </>
    )
}

export default Navbar
