import { useState, useMemo } from 'react'
import { Link } from 'react-router-dom'
import './Attendance.css'

function Attendance() {
    // Stage: 'input', 'marking', 'report'
    const [stage, setStage] = useState('input')

    // Inputs
    const [formData, setFormData] = useState({
        year: 'FE',
        division: 'A',
        studentCount: 60,
        subject: '',
        date: new Date().toISOString().split('T')[0] // Today YYYY-MM-DD
    })

    // Attendance State: Set to store Present roll numbers (Green). 
    // Spec: "Default Red = Absent". So if not in set, it's absent.
    // If we have 60 students, logic is: all 1..60 are Absent by default.
    // Click -> Add to Present set.
    const [presentRolls, setPresentRolls] = useState(new Set())

    const handleInputChange = (e) => {
        const { name, value } = e.target
        setFormData(prev => ({
            ...prev,
            [name]: name === 'studentCount' ? parseInt(value) || 0 : value
        }))
    }

    const startAttendance = () => {
        if (!formData.subject || formData.studentCount < 1) {
            alert("Please provide a Subject and valid Number of Students.")
            return
        }
        setStage('marking')
    }

    const toggleRoll = (roll) => {
        setPresentRolls(prev => {
            const next = new Set(prev)
            if (next.has(roll)) {
                next.delete(roll) // Go back to Absent (Red)
            } else {
                next.add(roll) // Mark Present (Green)
            }
            return next
        })
    }

    const reset = () => {
        setStage('input')
        setPresentRolls(new Set())
        setFormData(prev => ({ ...prev, studentCount: 60, subject: '', date: new Date().toISOString().split('T')[0] }))
    }

    // Stats
    const total = formData.studentCount
    const presentCount = presentRolls.size
    const absentCount = total - presentCount

    // Report Generation
    const generateReport = () => {
        setStage('report')
    }

    const reportText = useMemo(() => {
        if (stage !== 'report') return ''

        // Calculate absent rolls
        const absents = []
        const presents = []

        for (let i = 1; i <= total; i++) {
            if (presentRolls.has(i)) {
                presents.push(i)
            } else {
                absents.push(i)
            }
        }

        const dateStr = new Date(formData.date).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })

        return `Attendance Report
-----------------
Date: ${dateStr}
Year: ${formData.year}
Division: ${formData.division}
Subject: ${formData.subject}

Present (${presents.length}):
${presents.join(', ') || 'None'}

Absent (${absents.length}):
${absents.join(', ') || 'None'}`
    }, [stage, formData, presentRolls, total])

    const copyToClipboard = () => {
        navigator.clipboard.writeText(reportText)
        alert("Report copied to clipboard!")
    }

    return (
        <div className="attendance-page">
            {/* Minimal Navbar */}
            <nav className="attendance-navbar">
                <Link to="/" className="attendance-brand">
                    <span>🗓️</span>
                    <span>Smart Attendance</span>
                </Link>
                <Link to="/" className="btn btn-outline" style={{ fontSize: '0.9rem', padding: '0.4rem 1rem' }}>
                    Back to Home
                </Link>
            </nav>

            <main className="attendance-container">
                <div className="attendance-card">
                    {/* Header */}
                    <div className="card-header">
                        <h1 className="card-title">
                            {stage === 'input' && "Class Details"}
                            {stage === 'marking' && "Mark Attendance"}
                            {stage === 'report' && "Attendance Summary"}
                        </h1>
                    </div>

                    <div className="card-body">
                        {/* INPUT STAGE */}
                        {stage === 'input' && (
                            <div className="input-form">
                                <div className="input-grid">
                                    <div className="form-group">
                                        <label className="form-label">Year</label>
                                        <select name="year" value={formData.year} onChange={handleInputChange} className="form-select">
                                            {['FE', 'SE', 'TE', 'BE'].map(y => <option key={y} value={y}>{y}</option>)}
                                        </select>
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Division</label>
                                        <select name="division" value={formData.division} onChange={handleInputChange} className="form-select">
                                            {['A', 'B', 'C'].map(d => <option key={d} value={d}>{d}</option>)}
                                        </select>
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Subject</label>
                                        <input
                                            type="text"
                                            name="subject"
                                            value={formData.subject}
                                            onChange={handleInputChange}
                                            placeholder="e.g. Data Structures"
                                            className="form-input"
                                        />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Date</label>
                                        <input
                                            type="date"
                                            name="date"
                                            value={formData.date}
                                            onChange={handleInputChange}
                                            className="form-input"
                                        />
                                    </div>
                                    <div className="form-group full-width">
                                        <label className="form-label">Number of Students</label>
                                        <input
                                            type="number"
                                            name="studentCount"
                                            value={formData.studentCount}
                                            onChange={handleInputChange}
                                            min="1"
                                            max="200"
                                            className="form-input"
                                        />
                                    </div>
                                </div>
                                <button
                                    className="btn btn-primary full-width"
                                    style={{ marginTop: '1.5rem', width: '100%', padding: '1rem', fontSize: '1.1rem' }}
                                    onClick={startAttendance}
                                >
                                    Start Attendance
                                </button>
                            </div>
                        )}

                        {/* MARKING STAGE */}
                        {stage === 'marking' && (
                            <div className="marking-interface">
                                <div className="info-bar" style={{ marginBottom: '1.5rem', textAlign: 'center', color: '#6b7280' }}>
                                    {formData.year} - {formData.division} | {formData.subject} | {new Date(formData.date).toLocaleDateString()}
                                </div>

                                {/* Live Stats */}
                                <div className="stats-bar">
                                    <div className="stat-item">
                                        <span className="stat-label">Present (Green)</span>
                                        <span className="stat-value text-green">{presentCount}</span>
                                    </div>
                                    <div className="stat-item">
                                        <span className="stat-label">Absent (Red)</span>
                                        <span className="stat-value text-red">{absentCount}</span>
                                    </div>
                                </div>

                                {/* Grid */}
                                <div className="roll-grid">
                                    {Array.from({ length: total }, (_, i) => i + 1).map(roll => {
                                        const isPresent = presentRolls.has(roll)
                                        return (
                                            <button
                                                key={roll}
                                                onClick={() => toggleRoll(roll)}
                                                className={`roll-btn ${isPresent ? 'present' : 'absent'}`}
                                            >
                                                {roll}
                                            </button>
                                        )
                                    })}
                                </div>

                                <button
                                    className="btn btn-primary"
                                    style={{ width: '100%', padding: '1rem', fontSize: '1.1rem' }}
                                    onClick={generateReport}
                                >
                                    Generate Attendance Report
                                </button>
                                <button
                                    className="btn btn-outline"
                                    style={{ width: '100%', marginTop: '1rem' }}
                                    onClick={() => setStage('input')}
                                >
                                    Edit Details
                                </button>
                            </div>
                        )}

                        {/* REPORT STAGE */}
                        {stage === 'report' && (
                            <div className="report-interface">
                                <div className="report-container">
                                    <div className="report-content">
                                        {reportText}
                                    </div>
                                    <button
                                        className="btn btn-primary"
                                        style={{ width: '100%' }}
                                        onClick={copyToClipboard}
                                    >
                                        📋 Copy to Clipboard
                                    </button>
                                </div>

                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                                    <button
                                        className="btn btn-outline"
                                        onClick={() => setStage('marking')}
                                    >
                                        ← Back to Edit
                                    </button>
                                    <button
                                        className="btn btn-outline"
                                        style={{ color: '#dc2626', borderColor: '#fecaca' }}
                                        onClick={reset}
                                    >
                                        ↺ Reset
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </main>
        </div>
    )
}

export default Attendance
