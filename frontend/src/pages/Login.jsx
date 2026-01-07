import { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import './Auth.css'

function AuthPage() {
    const [isLogin, setIsLogin] = useState(true)
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState('')

    // Hooks for interaction and redirection
    const navigate = useNavigate()
    const location = useLocation()
    const from = location.state?.from?.pathname || "/dashboard"

    // Form States
    const [username, setUsername] = useState('')
    const [password, setPassword] = useState('')

    const { login, signup } = useAuth()

    const handleSubmit = async (e) => {
        e.preventDefault()
        setError('')
        setIsLoading(true)

        // Artificial delay for smooth UX (optional)
        // await new Promise(resolve => setTimeout(resolve, 800))

        try {
            let result
            if (isLogin) {
                result = await login(username, password)
            } else {
                // For signup, we use username as email since backend expects email format for username sometimes
                // But simplified UI just asks for Username. 
                // To keep it simple but working with backend that might expect email:
                // We'll just pass username as both name and username/email
                result = await signup(username, username, password)
            }

            if (result.success) {
                // Smart Redirect
                navigate(from, { replace: true })
            } else {
                setError(result.error)
            }
        } catch (err) {
            setError('An unexpected error occurred')
        } finally {
            setIsLoading(false)
        }
    }

    const toggleMode = () => {
        setError('')
        setIsLogin(!isLogin)
        // Optional: Reset form?
        // setUsername('')
        // setPassword('')
    }

    return (
        <div className="auth-page">
            <div className="auth-container">
                <div className="auth-header">
                    <div className="auth-logo">
                        <span className="logo-icon">📅</span>
                        <span className="logo-text">Smart Timetable</span>
                    </div>
                </div>

                <div className="auth-card">
                    <div className="auth-content-wrapper" key={isLogin ? 'login' : 'signup'}>
                        <h2 className="auth-title">
                            {isLogin ? 'Welcome Back' : 'Create Account'}
                        </h2>
                        <p className="auth-subtitle">
                            {isLogin
                                ? 'Login to manage your timetables'
                                : 'Get started with smart scheduling'}
                        </p>

                        {error && (
                            <div className="auth-error">
                                <span>⚠️</span> {error}
                            </div>
                        )}

                        <form onSubmit={handleSubmit} className="auth-form">
                            <div className="form-group">
                                <label htmlFor="username">Username</label>
                                <input
                                    type="text"
                                    id="username"
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    placeholder="Enter your username"
                                    required
                                    autoFocus
                                />
                            </div>

                            <div className="form-group">
                                <label htmlFor="password">Password</label>
                                <input
                                    type="password"
                                    id="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    placeholder="••••••••"
                                    required
                                />
                            </div>

                            <button
                                type="submit"
                                className="btn-auth"
                                disabled={isLoading}
                            >
                                {isLoading ? (
                                    <div className="spinner"></div>
                                ) : (
                                    isLogin ? 'Sign In' : 'Sign Up'
                                )}
                            </button>
                        </form>
                    </div>

                    <div className="auth-toggle">
                        {isLogin ? "Don't have an account? " : "Already have an account? "}
                        <button type="button" onClick={toggleMode}>
                            {isLogin ? 'Sign up' : 'Log in'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default AuthPage
