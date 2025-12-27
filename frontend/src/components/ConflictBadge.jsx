import React, { useState } from 'react'
import PropTypes from 'prop-types'
import { getConflictColor } from '../utils/conflictDetector'

function ConflictBadge({ conflicts = [], severity = 'error', onClick = null }) {
    const [showDetails, setShowDetails] = useState(false)

    if (!conflicts || conflicts.length === 0) {
        return null
    }

    const filteredConflicts = severity
        ? conflicts.filter(c => c.severity === severity)
        : conflicts

    if (filteredConflicts.length === 0) {
        return null
    }

    const count = filteredConflicts.length
    const color = getConflictColor(severity)

    const getIcon = () => {
        switch (severity) {
            case 'error':
                return '❌'
            case 'warning':
                return '⚠️'
            default:
                return 'ℹ️'
        }
    }

    const handleClick = () => {
        if (onClick) {
            onClick(filteredConflicts)
        } else {
            setShowDetails(!showDetails)
        }
    }

    return (
        <div className="conflict-badge-container">
            <div
                className={`conflict-badge ${severity}`}
                style={{ borderColor: color }}
                onClick={handleClick}
                title={`${count} ${severity} conflict${count > 1 ? 's' : ''}`}
            >
                <span className="conflict-icon">{getIcon()}</span>
                <span className="conflict-count" style={{ color }}>{count}</span>
            </div>

            {showDetails && !onClick && (
                <div className="conflict-details-popup">
                    <div className="conflict-details-header">
                        <h4>{severity.charAt(0).toUpperCase() + severity.slice(1)} Conflicts ({count})</h4>
                        <button
                            className="close-btn"
                            onClick={(e) => {
                                e.stopPropagation()
                                setShowDetails(false)
                            }}
                        >
                            ✕
                        </button>
                    </div>
                    <ul className="conflict-list">
                        {filteredConflicts.map((conflict, index) => (
                            <li key={conflict.id || index} className="conflict-item">
                                <div className="conflict-message">{conflict.message}</div>
                                {conflict.details && (
                                    <div className="conflict-sub-details">
                                        {Object.entries(conflict.details).map(([key, value]) => (
                                            <span key={key} className="detail-tag">
                                                {key}: {Array.isArray(value) ? value.join(', ') : value}
                                            </span>
                                        ))}
                                    </div>
                                )}
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    )
}

ConflictBadge.propTypes = {
    conflicts: PropTypes.arrayOf(PropTypes.shape({
        id: PropTypes.string,
        type: PropTypes.string.isRequired,
        severity: PropTypes.string.isRequired,
        message: PropTypes.string.isRequired,
        details: PropTypes.object,
        affectedSlots: PropTypes.arrayOf(PropTypes.string)
    })),
    severity: PropTypes.oneOf(['error', 'warning', 'info']),
    onClick: PropTypes.func
}

export default ConflictBadge
