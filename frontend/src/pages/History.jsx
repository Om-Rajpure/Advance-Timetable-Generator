import React from 'react'
import './ModulePage.css'

function History() {
    return (
        <div className="module-page">
            <div className="module-header">
                <h1 className="module-title">📜 Timetable History</h1>
                <p className="module-description">
                    View, restore, and compare previous timetable versions
                </p>
            </div>

            <div className="module-content">
                <div className="info-card">
                    <h3>🕐 History Features</h3>
                    <ul>
                        <li>View all generated timetable versions</li>
                        <li>Compare changes between versions</li>
                        <li>Restore previous timetable configurations</li>
                        <li>Track edit history and modifications</li>
                        <li>Filter by date, branch, and semester</li>
                        <li>Export historical data for auditing</li>
                    </ul>
                </div>

                <div className="coming-soon-card">
                    <div className="coming-soon-icon">🕑</div>
                    <h2>Coming Soon</h2>
                    <p>Version control and history tracking system is under development.</p>
                    <p className="tech-note">
                        <strong>Planned features:</strong> Timeline view, version comparison tool,
                        one-click restoration, and detailed change logs with user attribution.
                    </p>
                </div>
            </div>
        </div>
    )
}

export default History
