import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import './Auth.css'

function Signup() {
    const [formData, setFormData] = useState({
        name: '',
        email: '',
        college: '',
        password: '',
        confirmPassword: ''
    })
    const { signup } = useAuth()

    const handleChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        })
    }

    const handleSubmit = (e) => {
        e.preventDefault()
        if (formData.password !== formData.confirmPassword) {
            alert('Passwords do not match')
            return
        }
        // TODO: Replace with real backend signup
        signup(formData.name, formData.email, formData.password)
    }

    return (
        <div className="auth-page">
            <div className="auth-container">
                <div className="auth-header">
                    <Link to="/" className="auth-logo">
                        <span className="logo-icon">📅</span>
                        <span className="logo-text">Smart Timetable</span>
                    </Link>
                </div>

                <div className="auth-card">
                    {/* Demo Notice */}
                    <div className="demo-notice">
                        ℹ️ Signup is currently for demo purpose only. You'll be redirected to login.
                    </div>

                    <h2 className="auth-title">Get Started Free</h2>
                    <p className="auth-subtitle">Create your account in seconds</p>

                    <form onSubmit={handleSubmit} className="auth-form">
                        <div className="form-group">
                            <label htmlFor="name">Full Name</label>
                            <input
                                type="text"
                                id="name"
                                name="name"
                                value={formData.name}
                                onChange={handleChange}
                                placeholder="John Doe"
                                required
                            />
                        </div>

                        <div className="form-group">
                            <label htmlFor="email">Email Address</label>
                            <input
                                type="email"
                                id="email"
                                name="email"
                                value={formData.email}
                                onChange={handleChange}
                                placeholder="you@college.edu"
                                required
                            />
                        </div>

                        <div className="form-group">
                            <label htmlFor="college">College Name</label>
                            <input
                                type="text"
                                id="college"
                                name="college"
                                value={formData.college}
                                onChange={handleChange}
                                placeholder="Your College Name"
                                required
                            />
                        </div>

                        <div className="form-group">
                            <label htmlFor="password">Password</label>
                            <input
                                type="password"
                                id="password"
                                name="password"
                                value={formData.password}
                                onChange={handleChange}
                                placeholder="••••••••"
                                required
                            />
                        </div>

                        <div className="form-group">
                            <label htmlFor="confirmPassword">Confirm Password</label>
                            <input
                                type="password"
                                id="confirmPassword"
                                name="confirmPassword"
                                value={formData.confirmPassword}
                                onChange={handleChange}
                                placeholder="••••••••"
                                required
                            />
                        </div>

                        <button type="submit" className="btn btn-primary btn-full">
                            Create Account
                        </button>
                    </form>

                    <p className="auth-footer">
                        Already have an account? <Link to="/login">Login here</Link>
                    </p>
                </div>

                <div className="auth-back">
                    <Link to="/">← Back to Home</Link>
                </div>
            </div>
        </div>
    )
}

export default Signup
