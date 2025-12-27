import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import './Navbar.css'

function Navbar() {
    const [scrolled, setScrolled] = useState(false)
    const { isAuthenticated, logout } = useAuth()

    useEffect(() => {
        const handleScroll = () => {
            setScrolled(window.scrollY > 50)
        }

        window.addEventListener('scroll', handleScroll)
        return () => window.removeEventListener('scroll', handleScroll)
    }, [])

    const scrollToSection = (sectionId) => {
        const element = document.getElementById(sectionId)
        if (element) {
            element.scrollIntoView({ behavior: 'smooth' })
        }
    }

    const handleLogout = () => {
        logout()
    }

    return (
        <nav className={`navbar ${scrolled ? 'scrolled' : ''}`}>
            <div className="container navbar-content">
                <Link to="/" className="navbar-logo">
                    <span className="logo-icon">📅</span>
                    <span className="logo-text">Smart Timetable</span>
                </Link>

                {!isAuthenticated ? (
                    // Menu when NOT logged in
                    <ul className="navbar-menu">
                        <li><a onClick={() => scrollToSection('home')}>Home</a></li>
                        <li><a onClick={() => scrollToSection('features')}>Features</a></li>
                        <li><a onClick={() => scrollToSection('how-it-works')}>How It Works</a></li>
                        <li><Link to="/login" className="nav-link-primary">Login</Link></li>
                        <li><Link to="/signup" className="btn btn-primary btn-sm">Signup</Link></li>
                    </ul>
                ) : (
                    // Menu when logged in
                    <ul className="navbar-menu">
                        <li><Link to="/dashboard">Dashboard</Link></li>
                        <li><Link to="/generate">Generate Timetable</Link></li>
                        <li><Link to="/upload">Upload Timetable</Link></li>
                        <li><button onClick={handleLogout} className="btn btn-outline btn-sm logout-btn">Logout</button></li>
                    </ul>
                )}
            </div>
        </nav>
    )
}

export default Navbar
