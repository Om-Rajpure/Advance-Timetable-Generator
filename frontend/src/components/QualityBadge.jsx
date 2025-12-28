import React from 'react';
import './QualityBadge.css';

function QualityBadge({ score, delta }) {
    const getGrade = (score) => {
        if (score >= 90) return { text: 'Excellent', color: 'green' };
        if (score >= 75) return { text: 'Good', color: 'blue' };
        if (score >= 60) return { text: 'Acceptable', color: 'orange' };
        return { text: 'Needs Improvement', color: 'red' };
    };

    if (score === null || score === undefined) {
        return null;
    }

    const grade = getGrade(score);

    return (
        <div className={`quality-badge quality-${grade.color}`}>
            <div className="badge-content">
                <div className="score-display">{Math.round(score)}/100</div>
                <div className="grade-text">{grade.text}</div>
            </div>
            {delta !== undefined && delta !== 0 && (
                <div className={`delta ${delta > 0 ? 'positive' : 'negative'}`}>
                    {delta > 0 ? `+${Math.round(delta)}` : Math.round(delta)}
                </div>
            )}
        </div>
    );
}

export default QualityBadge;
