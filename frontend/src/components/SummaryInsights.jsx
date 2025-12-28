import React from 'react'
import './SummaryInsights.css'

function SummaryInsights({ summary }) {
    if (!summary) {
        return (
            <div className="summary-insights">
                <div className="quality-header">
                    <h2>No analytics data available</h2>
                </div>
            </div>
        )
    }

    const { qualityScore, grade, stars, topIssues = [], topStrengths = [] } = summary

    // Generate star display
    const renderStars = () => {
        const starElements = []
        for (let i = 0; i < 5; i++) {
            starElements.push(
                <span key={i}>{i < stars ? '⭐' : '☆'}</span>
            )
        }
        return starElements
    }

    return (
        <div className="summary-insights">
            <div className="quality-header">
                <h2>Timetable Quality Assessment</h2>

                <div className="quality-score-display">
                    <div className="score-number">{qualityScore}</div>
                    <div className="score-details">
                        <div className="grade">{grade}</div>
                        <small>/100</small>
                    </div>
                </div>

                <div className="star-rating">
                    {renderStars()}
                </div>
            </div>

            <div className="insights-grid">
                <div className="insight-section">
                    <h3>
                        <span>✅</span>
                        <span>Strengths</span>
                    </h3>
                    <ul className="insight-list">
                        {topStrengths.length > 0 ? (
                            topStrengths.map((strength, idx) => (
                                <li key={idx}>{strength}</li>
                            ))
                        ) : (
                            <li className="no-insights">No notable strengths identified</li>
                        )}
                    </ul>
                </div>

                <div className="insight-section">
                    <h3>
                        <span>⚠️</span>
                        <span>Areas for Improvement</span>
                    </h3>
                    <ul className="insight-list">
                        {topIssues.length > 0 ? (
                            topIssues.map((issue, idx) => (
                                <li key={idx}>{issue}</li>
                            ))
                        ) : (
                            <li className="no-insights">No issues detected</li>
                        )}
                    </ul>
                </div>
            </div>
        </div>
    )
}

export default SummaryInsights
