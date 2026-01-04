import React, { useState } from 'react'
import './LabUsageHeatmap.css'

function LabUsageHeatmap({ labUsage, title = "🔬 Lab Usage Heatmap", type = "lab", metricKey = "perLab" }) {
    const [selectedLab, setSelectedLab] = useState(null)

    if (!labUsage || !labUsage.metrics) {
        return null
    }

    const { metrics, insights } = labUsage
    // Dynamically access the correct dictionary (perLab / perClassroom)
    const perRoomData = metrics[metricKey] || metrics.perLab || metrics.perClassroom

    if (!perRoomData) return null;

    const allLabNames = Object.keys(perRoomData)

    // HARD FILTER: Remove Ghost Rooms (SE, TE, BE, etc)
    // Regex matches: FE, SE, TE, BE, LY, Year X, Part X, Div A...
    // STRICTER PATTERN: Match exact year names or names starting with them
    const ghostPattern = /^(FE|SE|TE|BE|B\.E\.|LY|Year|Part|Div\s)/i;

    // Filter out bad names AND ensure we don't accidentally hide "Room SE" if that was the fix
    // "Room SE" does NOT match ^(SE|TE...) so it should pass.
    const labNames = allLabNames.filter(name => {
        const clean = name.trim();
        if (clean.length < 2) return false; // Ignore "A", "B"

        // If it starts with "Room", it's valid (our fix)
        if (clean.toLowerCase().startsWith("room")) return true;

        // Otherwise, block if it looks like a Year/Div
        if (ghostPattern.test(clean)) return false;

        return true;
    });

    if (labNames.length === 0) {
        return (
            <div className="lab-usage-heatmap">
                <h3>{title}</h3>
                <p style={{ color: '#6b7280', textAlign: 'center', padding: '40px' }}>
                    No {type} data available
                </p>
            </div>
        )
    }

    // Select first lab if none selected
    const currentLab = selectedLab || labNames[0]
    const labData = perRoomData[currentLab]

    if (!labData) return null;

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
            <h3>{title}</h3>

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
                    <span>Occupied ({type === 'lab' ? 'Practical' : 'Lecture'} Scheduled)</span>
                </div>
            </div>

            
        </div>
    )
}

export default LabUsageHeatmap
