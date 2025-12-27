import { useAuth } from '../auth/AuthContext'
import { useNavigate } from 'react-router-dom'
import { useDashboardState } from '../hooks/useDashboardState'
import './Dashboard.css'

function Dashboard() {
    const { user } = useAuth()
    const navigate = useNavigate()
    const { getBranchInfo, getTimetableStatus, hasActiveTimetable } = useDashboardState()

    const branchInfo = getBranchInfo()
    const statusInfo = getTimetableStatus()
    const canEdit = hasActiveTimetable()

    // Smart navigation for Generate button
    const handleGenerate = () => {
        if (!branchInfo.exists) {
            navigate('/branch-setup')
        } else {
            navigate('/generate')
        }
    }

    const handleUpload = () => {
        navigate('/upload')
    }

    const handleEdit = () => {
        if (canEdit) {
            navigate('/edit')
        }
    }

    return (
        <div className="dashboard-page">
            {/* Welcome Header */}
            <div className="dashboard-header">
                <div className="container">
                    <h1 className="dashboard-title">
                        Welcome back, <span className="user-name">{user?.name || 'User'}</span>! 👋
                    </h1>
                    <p className="dashboard-subtitle">
                        Your central control panel for timetable management
                    </p>
                </div>
            </div>

            <div className="dashboard-content">
                <div className="container">
                    {/* Status Cards Section */}
                    <div className="status-section">
                        {/* Branch Status Card */}
                        <div className="status-card branch-card">
                            <div className="card-icon-header">
                                <div className="card-icon branch-icon">
                                    <span>🎓</span>
                                </div>
                                <h3 className="card-title">Selected Branch</h3>
                            </div>

                            {branchInfo.exists ? (
                                <div className="branch-info">
                                    <div className="branch-name">{branchInfo.name}</div>
                                    <div className="branch-details">
                                        <span className="detail-item">
                                            <strong>{branchInfo.years}</strong> Years
                                        </span>
                                        <span className="detail-separator">•</span>
                                        <span className="detail-item">
                                            <strong>{branchInfo.divisions}</strong> Divisions
                                        </span>
                                    </div>
                                </div>
                            ) : (
                                <div className="no-branch">
                                    <p className="no-branch-text">No branch selected</p>
                                    <button
                                        onClick={() => navigate('/branch-setup')}
                                        className="setup-branch-btn"
                                    >
                                        Set up branch →
                                    </button>
                                </div>
                            )}
                        </div>

                        {/* Timetable Status Indicator */}
                        <div className="status-card timetable-status-card">
                            <div className="card-icon-header">
                                <div className="card-icon status-icon">
                                    <span>📅</span>
                                </div>
                                <h3 className="card-title">Timetable Status</h3>
                            </div>

                            <div className="status-indicator">
                                <div
                                    className="status-badge"
                                    style={{ backgroundColor: `${statusInfo.color}20`, borderColor: statusInfo.color }}
                                >
                                    <span className="status-icon-large" style={{ color: statusInfo.color }}>
                                        {statusInfo.icon}
                                    </span>
                                    <span className="status-label" style={{ color: statusInfo.color }}>
                                        {statusInfo.label}
                                    </span>
                                </div>
                                <p className="status-description">{statusInfo.description}</p>
                            </div>
                        </div>
                    </div>

                    {/* Quick Actions Section */}
                    <div className="quick-actions-section">
                        <h2 className="section-title">Quick Actions</h2>
                        <div className="quick-actions-grid">

                            {/* Generate New Timetable */}
                            <button
                                className="action-button generate-action"
                                onClick={handleGenerate}
                            >
                                <div className="action-icon-wrapper">
                                    <span className="action-icon">🚀</span>
                                </div>
                                <h3 className="action-title">Generate New Timetable</h3>
                                <p className="action-description">
                                    {!branchInfo.exists
                                        ? 'Set up branch first, then generate clash-free timetable'
                                        : 'Create a new AI-powered clash-free timetable'}
                                </p>
                                <div className="action-footer">
                                    <span className="action-arrow">→</span>
                                </div>
                            </button>

                            {/* Upload Existing Timetable */}
                            <button
                                className="action-button upload-action"
                                onClick={handleUpload}
                            >
                                <div className="action-icon-wrapper">
                                    <span className="action-icon">📤</span>
                                </div>
                                <h3 className="action-title">Upload Existing Timetable</h3>
                                <p className="action-description">
                                    Upload Excel/CSV and auto-detect clashes
                                </p>
                                <div className="action-footer">
                                    <span className="action-arrow">→</span>
                                </div>
                            </button>

                            {/* Edit Current Timetable */}
                            <button
                                className={`action-button edit-action ${!canEdit ? 'disabled' : ''}`}
                                onClick={handleEdit}
                                disabled={!canEdit}
                            >
                                <div className="action-icon-wrapper">
                                    <span className="action-icon">✏️</span>
                                </div>
                                <h3 className="action-title">Edit Current Timetable</h3>
                                <p className="action-description">
                                    {canEdit
                                        ? 'Modify timetable with automatic conflict resolution'
                                        : 'Generate or upload a timetable first'}
                                </p>
                                <div className="action-footer">
                                    {canEdit ? (
                                        <span className="action-arrow">→</span>
                                    ) : (
                                        <span className="disabled-badge">Not Available</span>
                                    )}
                                </div>
                            </button>

                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default Dashboard
