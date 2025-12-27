import { createContext, useContext, useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

// ========================================
// 🚧 AUTH BYPASS FOR DEVELOPMENT MODE 🚧
// ========================================
// Set to false to bypass authentication during core feature development
// Set to true when ready to implement real authentication
// This allows direct access to all routes without login
export const isAuthEnabled = false
// ========================================

// TODO: Replace with real backend authentication
// This is a DUMMY authentication system for UI flow only
// No actual validation, no backend calls, no database

const AuthContext = createContext(null)

export const useAuth = () => {
    const context = useContext(AuthContext)
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider')
    }
    return context
}

export const AuthProvider = ({ children }) => {
    // AUTH BYPASS: When disabled, always treat user as authenticated
    const [isAuthenticated, setIsAuthenticated] = useState(!isAuthEnabled ? true : false)
    const [user, setUser] = useState(!isAuthEnabled ? { name: 'Dev User', email: 'dev@timetable.com' } : null)
    const navigate = useNavigate()

    // Load auth state from localStorage on mount
    useEffect(() => {
        // AUTH BYPASS: Skip localStorage check when auth is disabled
        if (!isAuthEnabled) {
            setIsAuthenticated(true)
            setUser({ name: 'Dev User', email: 'dev@timetable.com' })
            return
        }

        // Real auth logic (when isAuthEnabled = true)
        const storedAuth = localStorage.getItem('isAuthenticated')
        const storedUser = localStorage.getItem('user')

        if (storedAuth === 'true' && storedUser) {
            setIsAuthenticated(true)
            setUser(JSON.parse(storedUser))
        }
    }, [])

    // TODO: Replace with real backend login API call
    const login = (email, password) => {
        // DUMMY LOGIN - No validation, just set state
        const dummyUser = {
            name: email.split('@')[0], // Extract name from email
            email: email
        }

        setIsAuthenticated(true)
        setUser(dummyUser)

        // Persist to localStorage
        localStorage.setItem('isAuthenticated', 'true')
        localStorage.setItem('user', JSON.stringify(dummyUser))

        // Redirect to dashboard
        navigate('/dashboard')
    }

    // TODO: Replace with real backend signup API call
    const signup = (name, email, password) => {
        // DUMMY SIGNUP - Just store user info temporarily
        const dummyUser = {
            name: name,
            email: email
        }

        // For now, just show a success message and redirect to login
        // In real implementation, this would create user in database
        console.log('Dummy signup:', dummyUser)

        // Redirect to login page
        navigate('/login')
    }

    const logout = () => {
        setIsAuthenticated(false)
        setUser(null)

        // Clear localStorage
        localStorage.removeItem('isAuthenticated')
        localStorage.removeItem('user')

        // Redirect to landing page
        navigate('/')
    }

    const value = {
        isAuthenticated,
        user,
        login,
        signup,
        logout
    }

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
