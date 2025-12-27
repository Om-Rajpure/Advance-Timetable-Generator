import React from 'react'
import './ModulePage.css'

function Export() {
    return (
        <div className="module-page">
            <div className="module-header">
                <h1 className="module-title">📥 Export Timetable</h1>
                <p className="module-description">
                    Download timetables in multiple formats for distribution
                </p>
            </div>

            <div className="module-content">
                <div className="info-card">
                    <h3>💾 Export Options</h3>
                    <ul>
                        <li>Export as PDF (branch-wise, teacher-wise, section-wise)</li>
                        <li>Export as Excel/CSV for further processing</li>
                        <li>Generate printable teacher schedules</li>
                        <li>Export classroom allocation sheets</li>
                        <li>Bulk export for all branches</li>
                        <li>Custom format templates</li>
                    </ul>
                </div>

                <div className="coming-soon-card">
                    <div className="coming-soon-icon">📤</div>
                    <h2>Coming Soon</h2>
                    <p>Multi-format export functionality is being implemented.</p>
                    <p className="tech-note">
                        <strong>Planned features:</strong> PDF generation with custom branding,
                        Excel templates with formulas, automated email distribution, and QR code integration.
                    </p>
                </div>
            </div>
        </div>
    )
}

export default Export
