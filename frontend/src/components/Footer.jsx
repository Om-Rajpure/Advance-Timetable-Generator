import { Link } from 'react-router-dom'
import './Footer.css'

function Footer() {
    const currentYear = new Date().getFullYear()

    return (
        <footer className="footer">
            <div className="container footer-content">
                <div className="footer-left">
                    <div className="footer-logo">
                        <span className="logo-icon">📅</span>
                        <span className="logo-text">Smart Timetable</span>
                    </div>
                    <p className="footer-description">
                        Intelligent branch-level timetable generation for colleges.
                        Eliminate clashes, optimize schedules, save time.
                    </p>
                </div>

                <div className="footer-links">
                    <div className="footer-column">
                        <h4>Product</h4>
                        <ul>
                            <li><a href="/#features">Features</a></li>
                            <li><a href="/#how-it-works">How It Works</a></li>
                        </ul>
                    </div>

                    <div className="footer-column">
                        <h4>Account</h4>
                        <ul>
                            <li><Link to="/login">Login</Link></li>
                            <li><Link to="/signup">Signup</Link></li>
                        </ul>
                    </div>
                </div>
            </div>

            <div className="footer-bottom">
                <div className="container">
                    <p>© {currentYear} Smart Timetable Generator. Built with ❤️ for better education.</p>
                </div>
            </div>
        </footer>
    )
}

export default Footer
