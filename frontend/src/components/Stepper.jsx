import React from 'react'
import '../styles/stepper.css'

function Stepper({ currentStep, steps }) {
    return (
        <div className="stepper">
            {steps.map((step, index) => (
                <React.Fragment key={index}>
                    <div className={`stepper-step ${index < currentStep ? 'completed' :
                            index === currentStep ? 'active' :
                                'upcoming'
                        }`}>
                        <div className="stepper-circle">
                            {index < currentStep ? (
                                <span className="checkmark">✓</span>
                            ) : (
                                <span className="step-number">{index + 1}</span>
                            )}
                        </div>
                        <div className="stepper-label">
                            <span className="step-icon">{step.icon}</span>
                            <span className="step-text">{step.label}</span>
                        </div>
                    </div>
                    {index < steps.length - 1 && (
                        <div className={`stepper-line ${index < currentStep ? 'completed' : ''}`} />
                    )}
                </React.Fragment>
            ))}
        </div>
    )
}

export default Stepper
