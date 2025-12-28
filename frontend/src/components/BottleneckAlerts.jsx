import React from 'react'
import './BottleneckAlerts.css'

function BottleneckAlerts({ bottlenecks }) {
    if (!bottlenecks || !bottlenecks.issues) {
        return null
    }

    const { issues, counts } = bottlenecks

    // Get icon based on severity
    const getIcon = (severity) => {
        switch (severity) {
            case 'critical':
                return '🚨'
            case 'warning':
                return '⚠️'
            case 'info':
                return 'ℹ️'
            default:
                return '📌'
        }
    }

    if (issues.length === 0) {
        return (
            <div className="bottleneck-alerts">
                <div className="no-bottlenecks">
                    <div className="no-bottlenecks-icon">✅</div>
                    <h3>No Bottlenecks Detected</h3>
                    <p>Your timetable has no structural issues or constraints</p>
                </div>
            </div>
        )
    }

    return (
        <div className="bottleneck-alerts">
            <h2>
                🔍 Bottleneck Analysis
                <span style={{ marginLeft: '12px', fontSize: '14px', fontWeight: '400', color: '#6b7280' }}>
                    {counts.critical > 0 && `${counts.critical} Critical • `}
                    {counts.warning > 0 && `${counts.warning} Warnings`}
                </span>
            </h2>

            <div className="alerts-container">
                {issues.map((issue, idx) => (
                    <div key={idx} className={`alert-card ${issue.severity}`}>
                        <div className="alert-header">
                            <div className="alert-icon">
                                {getIcon(issue.severity)}
                            </div>
                            <div className="alert-content">
                                <h3>{issue.title}</h3>
                                <p>{issue.description}</p>
                                <span className={`alert-badge ${issue.severity}`}>
                                    {issue.severity}
                                </span>

                                {issue.affectedEntities && issue.affectedEntities.length > 0 && (
                                    <div className="affected-entities">
                                        <div className="affected-entities-label">Affected:</div>
                                        <div className="entity-tags">
                                            {issue.affectedEntities.map((entity, i) => (
                                                <span key={i} className="entity-tag">{entity}</span>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    )
}

export default BottleneckAlerts
