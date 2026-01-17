import { useNavigate } from 'react-router-dom'
import './AcademicToolsSection.css'

function AcademicToolsSection() {
    const navigate = useNavigate()

    return (
        <section className="academic-tools-section">
            <div className="section-container">
                <div className="tools-header">
                    <h2 className="tools-title">Academic Utilities</h2>
                    <p className="tools-description">
                        Smart, lightweight tools designed to simplify daily classroom operations.
                    </p>
                </div>

                <div className="tools-grid">
                    {/* Take Attendance Card */}
                    <div
                        className="tool-card"
                        onClick={() => navigate('/attendance')}
                        role="button"
                        tabIndex={0}
                    >
                        <div className="icon-container">
                            <span className="tool-icon">📋</span>
                        </div>
                        <h3 className="card-title">Smart Attendance</h3>
                        <p className="card-description">
                            Effortlessly mark attendance and export clean, formatted summaries instantly.
                        </p>

                        <div className="process-flow">
                            <div className="process-step">
                                <span className="step-icon">🏫</span>
                                <span className="step-label">Select</span>
                            </div>
                            <span className="step-arrow">➜</span>
                            <div className="process-step">
                                <span className="step-icon">👆</span>
                                <span className="step-label">Tap</span>
                            </div>
                            <span className="step-arrow">➜</span>
                            <div className="process-step">
                                <span className="step-icon">📤</span>
                                <span className="step-label">Share</span>
                            </div>
                        </div>

                        <div className="card-footer">
                            <span className="action-arrow">→</span>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    )
}

export default AcademicToolsSection
