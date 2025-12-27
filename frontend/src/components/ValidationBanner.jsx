import React from 'react'

function ValidationBanner({ errors = [], warnings = [], onErrorClick }) {
    if (errors.length === 0 && warnings.length === 0) {
        return null
    }

    const [expanded, setExpanded] = React.useState(errors.length > 0)

    const totalIssues = errors.length + warnings.length
    const hasErrors = errors.length > 0

    return (
        <div className={`validation-banner ${hasErrors ? 'has-errors' : 'has-warnings-only'}`}>
            <div className="validation-summary" onClick={() => setExpanded(!expanded)}>
                <div className="validation-summary-left">
                    <div className={`validation-icon ${hasErrors ? 'error' : 'warning'}`}>
                        {hasErrors ? '⚠️' : '⚡'}
                    </div>
                    <div className="validation-text">
                        <div className="validation-title">
                            {hasErrors ? `${errors.length} Error${errors.length !== 1 ? 's' : ''}` : 'Validation Warnings'}
                            {warnings.length > 0 && hasErrors && `, ${warnings.length} Warning${warnings.length !== 1 ? 's' : ''}`}
                            {warnings.length > 0 && !hasErrors && `: ${warnings.length} issue${warnings.length !== 1 ? 's' : ''} found`}
                        </div>
                        <div className="validation-subtitle">
                            {hasErrors ? 'Please fix errors before proceeding' : 'Review warnings to ensure data quality'}
                        </div>
                    </div>
                </div>
                <button className="validation-toggle" type="button">
                    {expanded ? '▼' : '▶'}
                </button>
            </div>

            {expanded && (
                <div className="validation-details">
                    {errors.length > 0 && (
                        <div className="validation-section">
                            <h4 className="validation-section-title error-title">Errors (Blocking)</h4>
                            <ul className="validation-list">
                                {errors.map((error, index) => (
                                    <li
                                        key={index}
                                        className="validation-item error-item"
                                        onClick={() => onErrorClick && onErrorClick(error)}
                                    >
                                        <span className="validation-item-icon">❌</span>
                                        <span className="validation-item-message">{error.message}</span>
                                        {error.field && (
                                            <span className="validation-item-field">({error.field})</span>
                                        )}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}

                    {warnings.length > 0 && (
                        <div className="validation-section">
                            <h4 className="validation-section-title warning-title">Warnings (Non-blocking)</h4>
                            <ul className="validation-list">
                                {warnings.map((warning, index) => (
                                    <li
                                        key={index}
                                        className="validation-item warning-item"
                                        onClick={() => onErrorClick && onErrorClick(warning)}
                                    >
                                        <span className="validation-item-icon">⚠️</span>
                                        <span className="validation-item-message">{warning.message}</span>
                                        {warning.field && (
                                            <span className="validation-item-field">({warning.field})</span>
                                        )}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}

export default ValidationBanner
