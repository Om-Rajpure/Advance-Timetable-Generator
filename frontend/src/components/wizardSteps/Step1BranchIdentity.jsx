import React, { useState, useEffect, useCallback } from 'react'
import '../../styles/formComponents.css'

function Step1BranchIdentity({ formData, onChange, errors, setErrors }) {
    const [checkingName, setCheckingName] = useState(false)
    const [charCount, setCharCount] = useState(formData.branchName?.length || 0)
    const [isDuplicate, setIsDuplicate] = useState(false)

    // Debounced API call to check if branch name exists
    const checkBranchNameAvailability = useCallback(async (name) => {
        // Only check if name is valid according to basic rules and not already marked as duplicate
        if (!name || name.trim().length < 3 || errors.branchName) {
            setCheckingName(false);
            return;
        }

        setCheckingName(true)
        setIsDuplicate(false) // Reset duplicate status before checking
        try {
            const response = await fetch('http://localhost:5000/api/branch/validate-name', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name })
            })
            const data = await response.json()

            if (!data.available) {
                setIsDuplicate(true)
                setErrors(prevErrors => ({ ...prevErrors, branchName: 'This branch name already exists' }))
            } else {
                setIsDuplicate(false)
                // Clear duplicate error if it was previously set and now available
                if (errors.branchName === 'This branch name already exists') {
                    setErrors(prevErrors => ({ ...prevErrors, branchName: null }))
                }
            }
        } catch (error) {
            console.error('Error checking branch name:', error)
            // Optionally set an error for API failure
            // setErrors(prevErrors => ({ ...prevErrors, branchName: 'Failed to check availability' }))
        } finally {
            setCheckingName(false)
        }
    }, [errors.branchName, setErrors]) // Depend on errors.branchName to correctly clear it

    // Debounce the API call
    useEffect(() => {
        // Don't check if there's a basic validation error already
        if (errors.branchName && errors.branchName !== 'This branch name already exists') {
            setCheckingName(false);
            return;
        }

        const timer = setTimeout(() => {
            if (formData.branchName && formData.branchName.length >= 3) {
                checkBranchNameAvailability(formData.branchName)
            } else {
                setCheckingName(false); // Stop checking if name is too short
                setIsDuplicate(false); // Reset duplicate status
                if (errors.branchName === 'This branch name already exists') {
                    setErrors(prevErrors => ({ ...prevErrors, branchName: null }))
                }
            }
        }, 500) // Wait 500ms after user stops typing

        return () => {
            clearTimeout(timer)
            setCheckingName(false); // Clear checking status on unmount or re-render
        }
    }, [formData.branchName, checkBranchNameAvailability, errors.branchName, setErrors])

    // Validate branch name
    const validateBranchName = (name) => {
        if (!name || name.trim().length === 0) {
            return 'Branch name is required'
        }
        if (name.length < 3) {
            return 'Branch name must be at least 3 characters'
        }
        if (name.length > 50) {
            return 'Branch name must not exceed 50 characters'
        }
        if (!/^[a-zA-Z\s\-]+$/.test(name)) {
            return 'Branch name can only contain letters, spaces, and hyphens'
        }
        return null
    }

    // Auto-capitalize first letter of each word
    const handleNameChange = (e) => {
        let value = e.target.value

        // Auto-capitalize
        value = value.replace(/\b\w/g, (char) => char.toUpperCase())

        setCharCount(value.length)
        onChange('branchName', value)

        // Validate
        const error = validateBranchName(value)
        setErrors({ ...errors, branchName: error })
    }

    const isValid = formData.branchName && !errors.branchName

    return (
        <div className="step-content">
            <h2 className="step-title">
                <span>🎓</span>
                Branch Identity
            </h2>
            <p className="step-description">
                Let's start by naming your branch. This will be the primary identifier for your academic branch.
            </p>

            <div className="form-field">
                <label className="form-label">
                    Branch Name
                </label>
                <input
                    type="text"
                    className={`input - text ${errors.branchName ? 'error' : isValid ? 'success' : ''} `}
                    placeholder="e.g., Computer Engineering, Artificial Intelligence"
                    value={formData.branchName || ''}
                    onChange={handleNameChange}
                    maxLength={50}
                    autoFocus
                />
                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '8px' }}>
                    {errors.branchName && (
                        <div className="input-error">
                            <span>⚠️</span>
                            {errors.branchName}
                        </div>
                    )}
                    {checkingName && !errors.branchName && (
                        <div style={{ color: 'var(--color-gray-600)', fontSize: 'var(--font-size-sm)' }}>
                            <span>🔍</span>
                            Checking availability...
                        </div>
                    )}
                    {isValid && !isDuplicate && !checkingName && (
                        <div className="input-success">
                            <span>✓</span>
                            Looks good!
                        </div>
                    )}
                    <div className="form-hint" style={{ marginLeft: 'auto' }}>
                        {charCount}/50
                    </div>
                </div>
            </div>

            <div style={{
                marginTop: 'var(--spacing-8)',
                padding: 'var(--spacing-4)',
                background: 'var(--color-gray-50)',
                borderRadius: 'var(--radius-lg)'
            }}>
                <h4 style={{ marginBottom: 'var(--spacing-2)', color: 'var(--color-gray-700)' }}>
                    💡 Examples
                </h4>
                <ul style={{
                    marginLeft: 'var(--spacing-6)',
                    color: 'var(--color-gray-600)',
                    lineHeight: 1.8
                }}>
                    <li>Computer Engineering</li>
                    <li>Artificial Intelligence</li>
                    <li>Electronics and Communication</li>
                    <li>Mechanical Engineering</li>
                    <li>Information Technology</li>
                </ul>
            </div>
        </div>
    )
}

export default Step1BranchIdentity
