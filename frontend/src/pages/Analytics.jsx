import React from 'react'
import './ModulePage.css'

function Analytics() {
    return (
        <div className="module-page">
            <div className="module-header">
                <h1 className="module-title">📊 Analytics Dashboard</h1>
                <p className="module-description">
                    View teacher workload, lab utilization, and timetable statistics
                </p>
            </div>

            <div className="module-content">
                <div className="info-card">
                    <h3>📈 Available Analytics</h3>
                    <ul>
                        <li>Teacher workload distribution and hour analysis</li>
                        <li>Lab and classroom utilization rates</li>
                        <li>Clash detection and conflict reports</li>
                        <li>Subject-wise hour allocation</li>
                        <li>Peak hour and free period analysis</li>
                        <li>Branch-wise timetable comparison</li>
                    </ul>
                </div>

                <div className="coming-soon-card">
                    <div className="coming-soon-icon">📈</div>
                    <h2>Coming Soon</h2>
                    <p>Advanced analytics and visualization tools are being developed.</p>
                    <p className="tech-note">
                        <strong>Planned features:</strong> Interactive charts, exportable reports,
                        real-time clash detection heatmaps, and teacher workload optimization suggestions.
                    </p>
                </div>
            </div>
        </div>
    )
}

export default Analytics
