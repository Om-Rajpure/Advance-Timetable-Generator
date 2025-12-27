import React from 'react'
import './ProgressTimeline.css'

/**
 * Progress Timeline Component
 * Displays visual step progression for the timetable generation workflow
 */
function ProgressTimeline({ workflowStatus }) {
    const steps = [
        { id: 'branch', label: 'Branch Setup', icon: '🎓' },
        { id: 'smart-input', label: 'Smart Input', icon: '🎯' },
        { id: 'generate', label: 'Generate', icon: '🚀' },
        { id: 'edit', label: 'Review', icon: '✏️' },
        { id: 'export', label: 'Export', icon: '📤' }
    ]

    const { currentStep, branchSetupCompleted, smartInputCompleted, timetableGenerated } = workflowStatus

    const getStepStatus = (index) => {
        if (index === 0) return branchSetupCompleted ? 'completed' : (currentStep === 0 ? 'current' : 'locked')
        if (index === 1) return smartInputCompleted ? 'completed' : (currentStep === 1 ? 'current' : 'locked')
        if (index === 2) return timetableGenerated ? 'completed' : (currentStep === 2 ? 'current' : 'locked')
        return 'locked' // Edit and Export are future steps
    }

    return (
        <div className="progress-timeline">
            <div className="timeline-container">
                {steps.map((step, index) => {
                    const status = getStepStatus(index)

                    return (
                        <React.Fragment key={step.id}>
                            {/* Step Circle */}
                            <div className={`timeline-step ${status}`}>
                                <div className="step-circle">
                                    {status === 'completed' ? (
                                        <span className="step-check">✓</span>
                                    ) : status === 'current' ? (
                                        <span className="step-icon-pulse">{step.icon}</span>
                                    ) : (
                                        <span className="step-icon-locked">🔒</span>
                                    )}
                                </div>
                                <div className="step-label">{step.label}</div>
                            </div>

                            {/* Connector Line */}
                            {index < steps.length - 1 && (
                                <div className={`timeline-connector ${status === 'completed' ? 'completed' : ''}`} />
                            )}
                        </React.Fragment>
                    )
                })}
            </div>
        </div>
    )
}

export default ProgressTimeline
