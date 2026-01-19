import { createContext, useContext, useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { API_BASE_URL } from '../config'

// Real auth logic
const AuthContext = createContext(null)

export const useAuth = () => {
    const context = useContext(AuthContext)
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider')
    }
    return context
}

export const AuthProvider = ({ children }) => {
    const [isAuthenticated, setIsAuthenticated] = useState(false)
    const [user, setUser] = useState(null)
    const [token, setToken] = useState(localStorage.getItem('token'))
    const [loading, setLoading] = useState(true)
    const navigate = useNavigate()

    const API_URL = `${API_BASE_URL}/api/auth`

    // Load auth state from localStorage on mount and verify token
    useEffect(() => {
        const verifyToken = async () => {
            const storedToken = localStorage.getItem('token')
            if (!storedToken) {
                setLoading(false)
                return
            }

            // Sync state if needed
            setToken(storedToken)

            try {
                const response = await fetch(`${API_URL}/verify`, {
                    headers: {
                        'Authorization': `Bearer ${storedToken}`
                    }
                })

                if (response.ok) {
                    const data = await response.json()
                    setIsAuthenticated(true)
                    setUser(data.user)
                } else {
                    // Invalid token
                    logout()
                }
            } catch (error) {
                console.error('Auth verification failed:', error)
                logout()
            } finally {
                setLoading(false)
            }
        }

        verifyToken()
    }, [])

    const login = async (username, password) => {
        try {
            const response = await fetch(`${API_URL}/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password })
            })

            const data = await response.json()

            if (response.ok) {
                setIsAuthenticated(true)
                setUser(data.user)
                setToken(data.token) // Update State
                localStorage.setItem('token', data.token)
                return { success: true }
            } else {
                return { success: false, error: data.error || 'Login failed' }
            }
        } catch (error) {
            console.error('Login error:', error)
            return { success: false, error: 'Network error. Please try again.' }
        }
    }

    const signup = async (name, email, password) => {
        try {
            const response = await fetch(`${API_URL}/signup`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    username: email, // Use email as username
                    password,
                    role: 'user' // Default role
                })
            })

            const data = await response.json()

            if (response.ok) {
                // Auto login after signup
                if (data.token) {
                    setIsAuthenticated(true)
                    setUser(data.user)
                    setToken(data.token) // Update State
                    localStorage.setItem('token', data.token)
                }

                return { success: true }
            } else {
                return { success: false, error: data.error || 'Signup failed' }
            }
        } catch (error) {
            console.error('Signup error:', error)
            return { success: false, error: 'Network error. Please try again.' }
        }
    }

    const logout = () => {
        setIsAuthenticated(false)
        setUser(null)
        setToken(null) // Update State

        // Clear all sensitive local state
        localStorage.removeItem('token')

        // Clear Dashboard & Workflow State
        localStorage.removeItem('selectedBranch')
        localStorage.removeItem('branchConfig')
        localStorage.removeItem('currentBranchId')
        localStorage.removeItem('currentBranchData')
        localStorage.removeItem('branchSetupCompleted')
        localStorage.removeItem('smartInputCompleted')
        localStorage.removeItem('timetableGenerated')
        localStorage.removeItem('timetableStatus')
        localStorage.removeItem('hasTimetable')

        // Optional: Safe clear for this domain
        localStorage.clear()
        navigate('/')
    }

    const value = {
        isAuthenticated,
        user,
        token, // Expose Token
        loading,
        login,
        signup,
        logout
    }

    return <AuthContext.Provider value={value}>{!loading && children}</AuthContext.Provider>
}
