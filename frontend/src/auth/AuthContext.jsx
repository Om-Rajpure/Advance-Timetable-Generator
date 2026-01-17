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
    const [loading, setLoading] = useState(true)
    const navigate = useNavigate()



    const API_URL = `${API_BASE_URL}/api/auth`

    // Load auth state from localStorage on mount and verify token
    useEffect(() => {
        const verifyToken = async () => {
            const token = localStorage.getItem('token')
            if (!token) {
                setLoading(false)
                return
            }

            try {
                const response = await fetch(`${API_URL}/verify`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
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
                localStorage.setItem('token', data.token)
                // navigate('/dashboard') // Handled by component
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
                    localStorage.setItem('token', data.token)
                }

                // navigate('/login') // Handled by component
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
        localStorage.removeItem('token')
        navigate('/')
    }

    const value = {
        isAuthenticated,
        user,
        loading,
        login,
        signup,
        logout
    }

    return <AuthContext.Provider value={value}>{!loading && children}</AuthContext.Provider>
}
