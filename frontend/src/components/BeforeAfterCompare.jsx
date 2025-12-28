import React from 'react';
import './BeforeAfterCompare.css';

const BeforeAfterCompare = ({ report }) => {
    if (!report) return null;

    const { qualityComparison, resourceComparison } = report;

    const getArrow = (delta) => {
        if (delta > 0) return '↑';
        if (delta < 0) return '↓';
        return '→';
    };

    const getChangeClass = (delta) => {
        if (delta > 0) return 'positive';
        if (delta < 0) return 'negative';
        return 'neutral';
    };

    const comparisonMetrics = [
        {
            label: 'Overall Quality Score',
            before: `${qualityComparison.before.score.toFixed(1)} (${qualityComparison.before.grade})`,
            after: `${qualityComparison.after.score.toFixed(1)} (${qualityComparison.after.grade})`,
            delta: qualityComparison.delta,
            unit: 'points'
        },
        {
            label: 'Teacher Utilization',
            before: resourceComparison.teacherUtilization.before,
            after: resourceComparison.teacherUtilization.after,
            delta: resourceComparison.teacherUtilization.delta,
            unit: ''
        },
        {
            label: 'Lab Utilization',
            before: resourceComparison.labUtilization.before,
            after: resourceComparison.labUtilization.after,
            delta: resourceComparison.labUtilization.delta,
            unit: ''
        }
    ];

    return (
        <div className="before-after-compare">
            <h3>📊 Before vs After Comparison</h3>

            <div className="comparison-table">
                <div className="comparison-header">
                    <div className="metric-column">Metric</div>
                    <div className="value-column">Original</div>
                    <div className="value-column">Simulated</div>
                    <div className="change-column">Change</div>
                </div>

                {comparisonMetrics.map((metric, idx) => (
                    <div key={idx} className="comparison-row">
                        <div className="metric-column">
                            <strong>{metric.label}</strong>
                        </div>
                        <div className="value-column">{metric.before}</div>
                        <div className="value-column">{metric.after}</div>
                        <div className={`change-column ${getChangeClass(metric.delta)}`}>
                            <span className="arrow">{getArrow(metric.delta)}</span>
                            <span className="delta-value">
                                {Math.abs(metric.delta).toFixed(1)}{metric.unit ? ` ${metric.unit}` : ''}
                            </span>
                        </div>
                    </div>
                ))}
            </div>

            {/* Quality Breakdown */}
            {qualityComparison.before.breakdown && (
                <details className="breakdown-details">
                    <summary>🔍 View Detailed Quality Breakdown</summary>
                    <div className="breakdown-content">
                        <div className="breakdown-column">
                            <h4>Original</h4>
                            <ul>
                                {Object.entries(qualityComparison.before.breakdown).map(([key, value]) => (
                                    <li key={key}>
                                        <span className="breakdown-label">{key}:</span>
                                        <span className="breakdown-value">{value.toFixed(1)}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                        <div className="breakdown-column">
                            <h4>Simulated</h4>
                            <ul>
                                {Object.entries(qualityComparison.after.breakdown).map(([key, value]) => (
                                    <li key={key}>
                                        <span className="breakdown-label">{key}:</span>
                                        <span className="breakdown-value">{value.toFixed(1)}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    </div>
                </details>
            )}
        </div>
    );
};

export default BeforeAfterCompare;
