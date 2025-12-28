import React from 'react';
import './ImpactSummary.css';

const ImpactSummary = ({ report }) => {
    if (!report) return null;

    const { feasible, affectedSlots, conflicts, qualityComparison, recommendations } = report;

    const getCriticalRecommendations = () => {
        return recommendations.filter(r => r.priority === 'critical' || r.priority === 'high');
    };

    return (
        <div className="impact-summary">
            {/* Feasibility Badge */}
            <div className={`feasibility-badge ${feasible ? 'feasible' : 'not-feasible'}`}>
                <span className="badge-icon">{feasible ? '✅' : '❌'}</span>
                <span className="badge-text">
                    {feasible ? 'Simulation Feasible' : 'Not Feasible'}
                </span>
            </div>

            {/* Key Metrics */}
            <div className="key-metrics">
                <div className="metric-card">
                    <div className="metric-icon">📋</div>
                    <div className="metric-content">
                        <div className="metric-value">{affectedSlots?.length || 0}</div>
                        <div className="metric-label">Slots Affected</div>
                    </div>
                </div>

                <div className="metric-card">
                    <div className="metric-icon">⚠️</div>
                    <div className="metric-content">
                        <div className="metric-value">
                            {conflicts.hardViolations?.length || 0}
                        </div>
                        <div className="metric-label">Hard Violations</div>
                    </div>
                </div>

                <div className="metric-card">
                    <div className="metric-icon">📊</div>
                    <div className="metric-content">
                        <div className="metric-value score-change">
                            {qualityComparison.delta > 0 ? '+' : ''}
                            {qualityComparison.delta?.toFixed(1) || 0}
                        </div>
                        <div className="metric-label">Quality Change</div>
                    </div>
                </div>
            </div>

            {/* Critical Recommendations */}
            {getCriticalRecommendations().length > 0 && (
                <div className="recommendations-section">
                    <h3>⚡ Critical Insights</h3>
                    <ul className="recommendations-list">
                        {getCriticalRecommendations().map((rec, idx) => (
                            <li key={idx} className={`recommendation-item ${rec.type}`}>
                                {rec.message}
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            {/* Conflict Details (Expandable) */}
            {conflicts.hardViolations?.length > 0 && (
                <details className="conflict-details">
                    <summary>🔍 View Constraint Violations ({conflicts.hardViolations.length})</summary>
                    <ul className="conflict-list">
                        {conflicts.hardViolations.map((violation, idx) => (
                            <li key={idx} className="conflict-item">
                                <strong>{violation.constraint}:</strong> {violation.message}
                            </li>
                        ))}
                    </ul>
                </details>
            )}
        </div>
    );
};

export default ImpactSummary;
