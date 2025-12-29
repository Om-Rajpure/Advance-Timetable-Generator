import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDashboardState } from '../hooks/useDashboardState'
import { useDraftAutoSave } from '../hooks/useDraftAutoSave'
import Stepper from '../components/Stepper'
import Step1BranchIdentity from '../components/wizardSteps/Step1BranchIdentity'
import Step2AcademicYears from '../components/wizardSteps/Step2AcademicYears'
import Step3Divisions from '../components/wizardSteps/Step3Divisions'
import Step4WorkingDays from '../components/wizardSteps/Step4WorkingDays'
import Step5Recess from '../components/wizardSteps/Step5Recess'
import Step6Rooms from '../components/wizardSteps/Step6Rooms'
import Step7Review from '../components/wizardSteps/Step7Review'
import '../styles/branchSetup.css'

const WIZARD_STEPS = [
    { label: 'Branch Identity', icon: '🎓' },
    { label: 'Academic Years', icon: '📚' },
    { label: 'Divisions', icon: '🏛️' },
    { label: 'Schedule', icon: '📅' },
    { label: 'Recess', icon: '☕' },
    { label: 'Facilities', icon: '🏫' },
    { label: 'Review', icon: '✅' }
]

function BranchSetup() {
    const navigate = useNavigate()
    const { updateBranch, completeBranchSetup } = useDashboardState()
    const [currentStep, setCurrentStep] = useState(0)
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [showSuccess, setShowSuccess] = useState(false)

    const [formData, setFormData] = useState({
        branchName: '',
        academicYears: ['SE', 'TE', 'BE'],
        divisions: {
            SE: ['A', 'B', 'C'],
            TE: ['A', 'B', 'C'],
            BE: ['A', 'B', 'C']
        },
        workingDays: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
        startTime: '8:00 AM',
        endTime: '5:00 PM',
        lectureDuration: 60,
        recessEnabled: true,
        recessStart: '12:00 PM',
        recessDuration: 60,
        classrooms: {},
        sharedLabs: []
    })

    const [errors, setErrors] = useState({})

    // Draft auto-save functionality
    const { lastSaved, showSavedIndicator, clearDraft } = useDraftAutoSave(formData, setFormData)

    // Keyboard shortcuts
    useEffect(() => {
        const handleKeyDown = (e) => {
            // Ctrl/Cmd + Left Arrow = Back
            if ((e.ctrlKey || e.metaKey) && e.key === 'ArrowLeft' && currentStep > 0) {
                e.preventDefault()
                handleBack()
            }
            // Ctrl/Cmd + Right Arrow = Next
            if ((e.ctrlKey || e.metaKey) && e.key === 'ArrowRight' && currentStep < WIZARD_STEPS.length - 1) {
                e.preventDefault()
                if (validateCurrentStep()) {
                    handleNext()
                }
            }
        }

        window.addEventListener('keydown', handleKeyDown)
        return () => window.removeEventListener('keydown', handleKeyDown)
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [currentStep])

    // Handle form data changes
    const handleChange = (field, value) => {
        setFormData({ ...formData, [field]: value })
    }

    // Validate current step (pure function - no state updates)
    const validateCurrentStep = () => {
        switch (currentStep) {
            case 0: // Branch Identity
                if (!formData.branchName || formData.branchName.trim().length < 3) {
                    return false
                }
                return !errors.branchName

            case 1: // Academic Years
                if (formData.academicYears.length === 0) {
                    return false
                }
                return true

            case 2: // Divisions
                // Check that all selected years have divisions
                for (const year of formData.academicYears) {
                    if (!formData.divisions[year] || formData.divisions[year].length === 0) {
                        return false
                    }
                }
                return true

            case 3: // Working Days & Time
                if (formData.workingDays.length === 0) {
                    return false
                }
                if (errors.timeRange) {
                    return false
                }
                return true

            case 4: // Recess
                return true // Recess is optional

            case 5: // Rooms
                // Check that all years have at least one classroom
                for (const year of formData.academicYears) {
                    if (!formData.classrooms[year] || formData.classrooms[year].length === 0) {
                        return false
                    }
                }
                return true

            case 6: // Review
                return true

            default:
                return true
        }
    }

    // Handle next button
    const handleNext = () => {
        // Validate and set errors if needed
        const isValid = validateCurrentStep()

        if (!isValid) {
            // Set appropriate error messages
            if (currentStep === 0 && (!formData.branchName || formData.branchName.trim().length < 3)) {
                setErrors({ ...errors, branchName: 'Branch name must be at least 3 characters' })
            } else if (currentStep === 1 && formData.academicYears.length === 0) {
                setErrors({ ...errors, academicYears: 'Please select at least one academic year' })
            } else if (currentStep === 3 && formData.workingDays.length === 0) {
                setErrors({ ...errors, workingDays: 'At least one working day must be selected' })
            }
            return
        }

        setCurrentStep(Math.min(currentStep + 1, WIZARD_STEPS.length - 1))
        window.scrollTo({ top: 0, behavior: 'smooth' })
    }

    // Handle back button
    const handleBack = () => {
        setCurrentStep(Math.max(currentStep - 1, 0))
        window.scrollTo({ top: 0, behavior: 'smooth' })
    }

    // Handle cancel
    const handleCancel = () => {
        if (window.confirm('Are you sure you want to cancel? Your progress will be lost.')) {
            navigate('/dashboard')
        }
    }

    // Handle edit from review
    const handleEditStep = (stepIndex) => {
        setCurrentStep(stepIndex)
        window.scrollTo({ top: 0, behavior: 'smooth' })
    }

    // Handle final submission
    const handleSubmit = async () => {
        console.log('🚀 Branch Setup: handleSubmit called')

        if (!validateCurrentStep()) {
            console.log('❌ Branch Setup: Validation failed')
            return
        }

        setIsSubmitting(true)
        console.log('📤 Branch Setup: Submitting to API...', formData)

        try {
            // Submit to backend API
            const response = await fetch('http://localhost:5000/api/branch/setup', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            })

            console.log('📥 Branch Setup: API response status:', response.status)

            if (!response.ok) {
                throw new Error('Failed to save branch configuration')
            }

            const data = await response.json()
            console.log('✅ Branch Setup: API success', data)

            // Clear draft since submission was successful
            clearDraft()

            // Update dashboard state
            const branchInfo = {
                name: formData.branchName,
                years: formData.academicYears.length,
                divisions: Object.values(formData.divisions).reduce((sum, divs) => sum + divs.length, 0)
            }
            console.log('💾 Branch Setup: Updating branch info', branchInfo)
            updateBranch(branchInfo)

            // Mark branch setup as completed
            console.log('⏰ ABOUT TO CALL completeBranchSetup()')
            completeBranchSetup()
            console.log('✨ AFTER calling completeBranchSetup()')

            // Verify it was set
            const wasSet = localStorage.getItem('branchSetupCompleted')
            console.log('🔍 Branch Setup: localStorage check after completion:', wasSet)

            if (wasSet !== 'true') {
                console.error('🚨 CRITICAL: localStorage was NOT set correctly!')
            }

            // Show success animation
            setShowSuccess(true)

            // Navigate to Smart Input Module after 2 seconds
            setTimeout(() => {
                console.log('🔄 Branch Setup: Navigating to Smart Input')
                navigate('/smart-input')
            }, 2000)

        } catch (error) {
            console.error('💥 Branch Setup: Error saving branch:', error)
            alert('Failed to save branch configuration. Please try again.')
        } finally {
            setIsSubmitting(false)
        }
    }

    // Render current step component
    const renderStepComponent = () => {
        const stepProps = {
            formData,
            onChange: handleChange,
            errors,
            setErrors
        }

        switch (currentStep) {
            case 0:
                return <Step1BranchIdentity {...stepProps} />
            case 1:
                return <Step2AcademicYears {...stepProps} />
            case 2:
                return <Step3Divisions {...stepProps} />
            case 3:
                return <Step4WorkingDays {...stepProps} />
            case 4:
                return <Step5Recess {...stepProps} />
            case 5:
                return <Step6Rooms {...stepProps} />
            case 6:
                return <Step7Review {...stepProps} onEditStep={handleEditStep} />
            default:
                return null
        }
    }

    // Render success state
    if (showSuccess) {
        return (
            <div className="wizard-page">
                <div className="wizard-container">
                    <div className="wizard-card">
                        <div className="success-animation">
                            <div className="success-icon">🎉</div>
                            <h2 className="success-title">Branch Setup Complete!</h2>
                            <p className="success-message">
                                Your branch <strong>{formData.branchName}</strong> has been successfully configured.
                            </p>
                            <p className="success-message" style={{ marginTop: 'var(--spacing-4)', fontSize: 'var(--font-size-base)' }}>
                                Redirecting to dashboard...
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        )
    }

    const isLastStep = currentStep === WIZARD_STEPS.length - 1
    const isStepValid = validateCurrentStep()

    return (
        <div className="wizard-page">
            <div className="wizard-container">
                {/* Header */}
                <div className="wizard-header">
                    <h1 className="wizard-title">Branch Setup</h1>
                    <p className="wizard-subtitle">
                        Configure your branch structure in a few simple steps
                    </p>
                    {showSavedIndicator && (
                        <div style={{
                            marginTop: 'var(--spacing-2)',
                            padding: 'var(--spacing-2) var(--spacing-4)',
                            background: 'var(--color-success)',
                            color: 'white',
                            borderRadius: 'var(--radius-md)',
                            fontSize: 'var(--font-size-sm)',
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: 'var(--spacing-2)',
                            animation: 'fadeIn 0.3s ease-out'
                        }}>
                            <span>✓</span>
                            Draft saved
                        </div>
                    )}
                </div>

                {/* Main Wizard Card */}
                <div className="wizard-card">
                    {/* Stepper */}
                    <div className="wizard-card-header">
                        <Stepper currentStep={currentStep} steps={WIZARD_STEPS} />
                    </div>

                    {/* Step Content */}
                    <div className="wizard-card-body">
                        {renderStepComponent()}
                    </div>

                    {/* Footer Navigation */}
                    <div className="wizard-footer">
                        <div className="wizard-footer-left">
                            <button
                                className="btn-wizard btn-wizard-cancel"
                                onClick={handleCancel}
                            >
                                Cancel
                            </button>
                        </div>

                        <div className="wizard-footer-right">
                            {currentStep > 0 && (
                                <button
                                    className="btn-wizard btn-wizard-back"
                                    onClick={handleBack}
                                >
                                    ← Back
                                </button>
                            )}

                            {!isLastStep ? (
                                <button
                                    className="btn-wizard btn-wizard-next"
                                    onClick={handleNext}
                                    disabled={!isStepValid}
                                >
                                    Next →
                                </button>
                            ) : (
                                <button
                                    className={`btn-wizard btn-wizard-submit ${isSubmitting ? 'loading' : ''}`}
                                    onClick={handleSubmit}
                                    disabled={isSubmitting || !isStepValid}
                                >
                                    {isSubmitting ? 'Saving...' : 'Confirm & Save ✓'}
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default BranchSetup
