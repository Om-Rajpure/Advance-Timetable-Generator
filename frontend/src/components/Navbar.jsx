import { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import '../styles/navbar.css' // Using the shared modern styles

function Navbar() {
    const [isScrolled, setIsScrolled] = useState(false)
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
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
    ]

    return (
        <>
            <nav className={`main-navbar ${isScrolled ? 'scrolled' : ''}`}>
                <div className="navbar-container">
                    {/* Brand */}
                    <Link to="/" className="navbar-brand">
                        <span className="brand-logo">🗓️</span>
                        <span className="brand-name">Smart Timetable</span>
                    </Link>

                    {/* Desktop Navigation */}
                    <div className="desktop-nav">
                        {navItems.map((item) => (
                            <button
                                key={item.id}
                                onClick={() => scrollToSection(item.id)}
                                className="nav-link"
                                style={{ background: 'none', border: 'none', cursor: 'pointer' }}
                            >
                                {item.label}
                            </button>
                        ))}
                    </div>

                    {/* Desktop Actions */}
                    <div className="desktop-actions">
                        {!user && (
                            <Link to="/login" className="btn-login">
                                Login
                            </Link>
                        )}
                        {/* Removed Signup button as requested */}
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
