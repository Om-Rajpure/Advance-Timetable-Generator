import React, { useState } from 'react'
import './LabUsageHeatmap.css'

function LabUsageHeatmap({ labUsage }) {
    const [selectedLab, setSelectedLab] = useState(null)

    if (!labUsage || !labUsage.metrics) {
        return null
    }

    const { metrics, insights } = labUsage
    const { perLab } = metrics

    const labNames = Object.keys(perLab)
    if (labNames.length === 0) {
        return (
            <div className="lab-usage-heatmap">
                <h3>🔬 Lab Usage Heatmap</h3>
                <p style={{ color: '#6b7280', textAlign: 'center', padding: '40px' }}>
                    No lab data available
                </p>
            </div>
        )
    }

    // Select first lab if none selected
    const currentLab = selectedLab || labNames[0]
    const labData = perLab[currentLab]

    const days = Object.keys(labData.heatmap)
    const timeSlots = Object.keys(labData.heatmap[days[0]] || {})

    // Get utilization badge class
    const getUtilizationClass = (percent) => {
        if (percent < 30) return 'low'
        if (percent < 70) return 'medium'
        return 'high'
    }

    return (
        <div className="lab-usage-heatmap">
            <h3>🔬 Lab Usage Heatmap</h3>

            <div className="lab-tabs">
                {labNames.map(lab => (
                    <button
                        key={lab}
                        className={`lab-tab ${currentLab === lab ? 'active' : ''}`}
                        onClick={() => setSelectedLab(lab)}
                    >
                        {lab}
                    </button>
                ))}
            </div>

            <div className="lab-info">
                <div className="lab-info-item">
                    <span className="lab-info-label">Utilization:</span>
                    <span className={`utilization-badge ${getUtilizationClass(labData.utilizationPercent)}`}>
                        {labData.utilizationPercent}%
                    </span>
                </div>
                <div className="lab-info-item">
                    <span className="lab-info-label">Idle Slots:</span>
                    <span className="lab-info-value">{labData.idleSlots}</span>
                </div>
            </div>

            <div className="heatmap-grid">
                <table>
                    <thead>
                        <tr>
                            <th>Time</th>
                            {days.map(day => (
                                <th key={day}>{day.substring(0, 3)}</th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {timeSlots.map(time => (
                            <tr key={time}>
                                <td className="time-label">{time}</td>
                                {days.map(day => {
                                    const value = labData.heatmap[day][time]
                                    const isOccupied = value === 1.0
                                    return (
                                        <td key={day}>
                                            <div
                                                className={`grid-cell ${isOccupied ? 'occupied' : 'free'}`}
                                                title={`${currentLab} - ${day} ${time}: ${isOccupied ? 'Occupied' : 'Free'}`}
                                            >
                                                {isOccupied ? '●' : '○'}
                                            </div>
                                        </td>
                                    )
                                })}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            <div className="legend">
                <div className="legend-item">
                    <div className="legend-color free"></div>
                    <span>Free (Available)</span>
                </div>
                <div className="legend-item">
                    <div className="legend-color occupied"></div>
                    <span>Occupied (Practical Scheduled)</span>
                </div>
            </div>

            {insights && insights.length > 0 && (
                <div style={{ marginTop: '20px' }}>
                    <div className="chart-subtitle">Insights</div>
                    <ul className="insights-list">
                        {insights.map((insight, idx) => (
                            <li key={idx}>{insight}</li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    )
}

export default LabUsageHeatmap
