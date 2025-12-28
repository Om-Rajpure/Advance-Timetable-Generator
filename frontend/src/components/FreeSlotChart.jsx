import React from 'react'
import './FreeSlotChart.css'

function FreeSlotChart({ freeSlots }) {
    if (!freeSlots || !freeSlots.metrics) {
        return null
    }

    const { metrics, insights } = freeSlots
    const { freeSlotsPerDay, totalFreeSlots, totalOccupiedSlots, freePercentage, bestDaysForAdditions } = metrics

    // Calculate max for scaling bars
    const maxFreeSlots = Math.max(...Object.values(freeSlotsPerDay), 1)

    // Simple pie chart using conic gradient
    const occupiedPercent = 100 - freePercentage
    const pieStyle = {
        background: `conic-gradient(
            #ef4444 0deg ${occupiedPercent * 3.6}deg,
            #10b981 ${occupiedPercent * 3.6}deg 360deg
        )`
    }

    return (
        <div className="free-slot-chart">
            <h3>🕒 Free Slot Analysis</h3>

            <div className="capacity-overview">
                <div className="capacity-card">
                    <div className="capacity-number">{totalOccupiedSlots}</div>
                    <div className="capacity-label">Occupied</div>
                </div>
                <div className="capacity-card primary">
                    <div className="capacity-number">{totalFreeSlots}</div>
                    <div className="capacity-label">Free Slots</div>
                </div>
                <div className="capacity-card">
                    <div className="capacity-number">{freePercentage}%</div>
                    <div className="capacity-label">Available</div>
                </div>
            </div>

            <div className="chart-section">
                <div className="chart-subtitle">Capacity Distribution</div>
                <div className="pie-chart-container">
                    <div className="pie-chart">
                        <div className="pie-slice" style={pieStyle}></div>
                    </div>
                    <div className="pie-legend">
                        <div className="pie-legend-item">
                            <div className="pie-legend-color" style={{ background: '#ef4444' }}></div>
                            <span className="pie-legend-label">Occupied</span>
                            <span className="pie-legend-value">{occupiedPercent.toFixed(1)}%</span>
                        </div>
                        <div className="pie-legend-item">
                            <div className="pie-legend-color" style={{ background: '#10b981' }}></div>
                            <span className="pie-legend-label">Free</span>
                            <span className="pie-legend-value">{freePercentage}%</span>
                        </div>
                    </div>
                </div>
            </div>

            <div className="chart-section">
                <div className="chart-subtitle">Free Slots by Day</div>
                <div className="day-bars">
                    {Object.entries(freeSlotsPerDay).map(([day, count]) => {
                        const width = (count / maxFreeSlots) * 100
                        return (
                            <div key={day} className="day-bar-row">
                                <div className="day-label">{day}</div>
                                <div className="day-bar-container">
                                    <div
                                        className="day-bar-fill"
                                        style={{ width: `${Math.max(width, 10)}%` }}
                                    >
                                        {count} slots
                                    </div>
                                </div>
                            </div>
                        )
                    })}
                </div>
            </div>

            {bestDaysForAdditions && bestDaysForAdditions.length > 0 && (
                <div className="best-days-section">
                    <div className="chart-subtitle">Best Days for Adding Classes</div>
                    <div className="best-days-grid">
                        {bestDaysForAdditions.slice(0, 3).map((dayData, idx) => (
                            <div key={dayData.day} className="best-day-card">
                                <div className="day-name">
                                    {idx === 0 ? '🥇' : idx === 1 ? '🥈' : '🥉'} {dayData.day}
                                </div>
                                <div className="day-slots">
                                    {dayData.freeSlots}
                                </div>
                                <div className="day-suffix">free slots</div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {insights && insights.length > 0 && (
                <div className="chart-section" style={{ marginTop: '24px' }}>
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

export default FreeSlotChart
