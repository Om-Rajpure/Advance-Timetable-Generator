import React from 'react'
import '../../styles/formComponents.css'
import TimeSlotPreview from '../TimeSlotPreview'

const TIME_OPTIONS = [
    '8:00 AM', '8:30 AM', '9:00 AM', '9:30 AM', '10:00 AM', '10:30 AM', '11:00 AM', '11:30 AM',
    '12:00 PM', '12:30 PM', '1:00 PM', '1:30 PM', '2:00 PM', '2:30 PM', '3:00 PM', '3:30 PM', '4:00 PM'
]

const DURATION_OPTIONS = [
    { value: 15, label: '15 minutes' },
    { value: 30, label: '30 minutes' },
    { value: 45, label: '45 minutes' },
    { value: 60, label: '1 hour' }
]

function Step5Recess({ formData, onChange }) {
    const recessEnabled = formData.recessEnabled !== undefined ? formData.recessEnabled : true
    const recessStart = formData.recessStart || '12:00 PM'
    const recessDuration = formData.recessDuration || 60

    const handleToggleRecess = () => {
        onChange('recessEnabled', !recessEnabled)
    }

    return (
        <div className="step-content">
            <h2 className="step-title">
                <span>☕</span>
                Recess Configuration
            </h2>
            <p className="step-description">
                Configure the break time for students and faculty. You can skip this if not needed.
            </p>

            {/* Enable Recess Toggle */}
            <div className="toggle-field" style={{ marginBottom: 'var(--spacing-8)' }}>
                <div>
                    <div className="toggle-label">Enable Recess/Break Time</div>
                    <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-gray-600)', marginTop: 'var(--spacing-1)' }}>
                        Add a scheduled break during the day
                    </p>
                </div>
                <div
                    className={`toggle-switch ${recessEnabled ? 'active' : ''}`}
                    onClick={handleToggleRecess}
                >
                    <div className="toggle-slider"></div>
                </div>
            </div>

            {/* Recess Configuration (shown only if enabled) */}
            {recessEnabled && (
                <div style={{
                    animation: 'fadeIn 0.4s ease-out',
                    background: 'var(--color-gray-50)',
                    padding: 'var(--spacing-6)',
                    borderRadius: 'var(--radius-lg)',
                    marginBottom: 'var(--spacing-6)'
                }}>
                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: '1fr 1fr',
                        gap: 'var(--spacing-4)'
                    }}>
                        <div className="form-field">
                            <label className="form-label">Recess Start Time</label>
                            <select
                                className="input-text"
                                value={recessStart}
                                onChange={(e) => onChange('recessStart', e.target.value)}
                            >
                                {TIME_OPTIONS.map((time) => (
                                    <option key={time} value={time}>{time}</option>
                                ))}
                            </select>
                        </div>

                        <div className="form-field">
                            <label className="form-label">Recess Duration</label>
                            <select
                                className="input-text"
                                value={recessDuration}
                                onChange={(e) => onChange('recessDuration', parseInt(e.target.value))}
                            >
                                {DURATION_OPTIONS.map((option) => (
                                    <option key={option.value} value={option.value}>
                                        {option.label}
                                    </option>
                                ))}
                            </select>
                        </div>
                    </div>
                </div>
            )}

            {/* Visual Preview */}
            <TimeSlotPreview
                startTime={formData.startTime || '8:00 AM'}
                endTime={formData.endTime || '5:00 PM'}
                lectureDuration={formData.lectureDuration || 60}
                recessStart={recessEnabled ? recessStart : null}
                recessDuration={recessEnabled ? recessDuration : 0}
            />

            {!recessEnabled && (
                <div style={{
                    marginTop: 'var(--spacing-6)',
                    padding: 'var(--spacing-4)',
                    background: 'var(--color-gray-50)',
                    borderRadius: 'var(--radius-lg)',
                    textAlign: 'center',
                    color: 'var(--color-gray-600)'
                }}>
                    ℹ️ No recess scheduled. Continuous lecture slots will be used.
                </div>
            )}
        </div>
    )
}

export default Step5Recess
