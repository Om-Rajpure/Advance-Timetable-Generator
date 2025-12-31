import React, { useState } from 'react'
import '../../styles/formComponents.css'

const BRANCH_EXAMPLES = [
    'Computer Engineering',
    'Artificial Intelligence',
    'Information Technology',
    'Electronics and Communication',
    'Mechanical Engineering',
    'Civil Engineering'
]

function Step1BranchIdentity({ formData, onChange, errors, setErrors }) {
    const [charCount, setCharCount] = useState(formData.branchName?.length || 0)
    const [touched, setTouched] = useState(false)

    // Validate branch name
    const validateBranchName = (name) => {
        if (!name || name.trim().length === 0) {
            return 'Branch name is required'
        }
        if (name.length > 50) {
            return 'Branch name must not exceed 50 characters'
        }
        return null
    }

    const handleNameChange = (e) => {
        const value = e.target.value
        setCharCount(value.length)
        onChange('branchName', value)

        if (touched) {
            const error = validateBranchName(value)
            setErrors({ ...errors, branchName: error })
        }
    }

    const handleBlur = () => {
        setTouched(true)
        const error = validateBranchName(formData.branchName)
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
                Enter the name of your branch. You can choose from the examples or type a custom name.
            </p>

            <div className="form-field">
                <label className="form-label">
                    Branch Name
                </label>
                <div style={{ position: 'relative' }}>
                    <input
                        type="text"
                        list="branch-examples"
                        className={`input-text ${errors.branchName ? 'error' : isValid ? 'success' : ''}`}
                        placeholder="e.g., Computer Engineering"
                        value={formData.branchName || ''}
                        onChange={handleNameChange}
                        onBlur={handleBlur}
                        maxLength={50}
                        autoFocus
                    />
                    <datalist id="branch-examples">
                        {BRANCH_EXAMPLES.map((example, index) => (
                            <option key={index} value={example} />
                        ))}
                    </datalist>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '8px' }}>
                    <div>
                        {errors.branchName && (
                            <div className="input-error" style={{ marginBottom: 0 }}>
                                <span>⚠️</span>
                                {errors.branchName}
                            </div>
                        )}
                        {!errors.branchName && (
                            <div style={{ color: 'var(--color-gray-500)', fontSize: 'var(--font-size-sm)' }}>
                                You can enter any branch name. Examples are shown for reference only.
                            </div>
                        )}
                    </div>
                    <div className="form-hint" style={{ marginLeft: '16px', whiteSpace: 'nowrap' }}>
                        {charCount}/50
                    </div>
                </div>
            </div>
        </div>
    )
}

export default Step1BranchIdentity
