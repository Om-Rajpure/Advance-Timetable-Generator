import React from 'react'
import '../../styles/formComponents.css'
import TimeSlotPreview from '../TimeSlotPreview'

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

const TIME_OPTIONS = [
    '6:00 AM', '6:30 AM', '7:00 AM', '7:30 AM', '8:00 AM', '8:30 AM', '9:00 AM', '9:30 AM', '10:00 AM',
    '10:30 AM', '11:00 AM', '11:30 AM', '12:00 PM', '12:30 PM', '1:00 PM', '1:30 PM', '2:00 PM',
    '2:30 PM', '3:00 PM', '3:30 PM', '4:00 PM', '4:30 PM', '5:00 PM', '5:30 PM', '6:00 PM'
]

function Step4WorkingDays({ formData, onChange, errors, setErrors }) {
    const workingDays = formData.workingDays || ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    const startTime = formData.startTime || '8:00 AM'
    const endTime = formData.endTime || '5:00 PM'
    const lectureDuration = formData.lectureDuration || 60

    const handleDayToggle = (day) => {
        let newDays = [...workingDays]

        if (newDays.includes(day)) {
            newDays = newDays.filter(d => d !== day)
        } else {
            newDays.push(day)
            // Maintain order
            newDays = DAYS.filter(d => newDays.includes(d))
        }

        if (newDays.length === 0) {
            setErrors({ ...errors, workingDays: 'At least one working day must be selected' })
        } else {
            setErrors({ ...errors, workingDays: null })
        }

        onChange('workingDays', newDays)
    }

    const handleTimeChange = (field, value) => {
        onChange(field, value)

        // Validate after state update
        setTimeout(() => validateTimes(field === 'startTime' ? value : startTime, field === 'endTime' ? value : endTime), 0)
    }

    const validateTimes = (start, end) => {
        const startIdx = TIME_OPTIONS.indexOf(start)
        const endIdx = TIME_OPTIONS.indexOf(end)

        if (endIdx <= startIdx) {
            setErrors({ ...errors, timeRange: 'End time must be after start time' })
        } else {
            setErrors({ ...errors, timeRange: null })
        }
    }

    return (
        <div className="step-content">
            <h2 className="step-title">
                <span>📅</span>
                Working Days & Time Slots
            </h2>
            <p className="step-description">
                Define your weekly schedule and daily time structure.
            </p>

            {/* Working Days */}
            <div className="form-field">
                <label className="form-label">Working Days</label>
                <div className="pill-selector">
                    {DAYS.map((day) => (
                        <button
                            key={day}
                            type="button"
                            className={`pill-button ${workingDays.includes(day) ? 'selected' : ''}`}
                            onClick={() => handleDayToggle(day)}
                        >
                            {day.substring(0, 3)}
                        </button>
                    ))}
                </div>
                {errors.workingDays && (
                    <div className="input-error">
                        <span>⚠️</span>
                        {errors.workingDays}
                    </div>
                )}
            </div>

            {/* Time Schedule */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 'var(--spacing-4)', marginBottom: 'var(--spacing-6)' }}>
                <div className="form-field">
                    <label className="form-label">Start Time</label>
                    <select
                        className="input-text"
                        value={startTime}
                        onChange={(e) => handleTimeChange('startTime', e.target.value)}
                    >
                        {TIME_OPTIONS.slice(0, 15).map((time) => (
                            <option key={time} value={time}>{time}</option>
                        ))}
                    </select>
                </div>

                <div className="form-field">
                    <label className="form-label">End Time</label>
                    <select
                        className="input-text"
                        value={endTime}
                        onChange={(e) => handleTimeChange('endTime', e.target.value)}
                    >
                        {TIME_OPTIONS.slice(10).map((time) => (
                            <option key={time} value={time}>{time}</option>
                        ))}
                    </select>
                </div>

                <div className="form-field">
                    <label className="form-label">Lecture Duration</label>
                    <select
                        className="input-text"
                        value={lectureDuration}
                        onChange={(e) => onChange('lectureDuration', parseInt(e.target.value))}
                    >
                        <option value={45}>45 minutes</option>
                        <option value={60}>1 hour</option>
                        <option value={90}>1.5 hours</option>
                    </select>
                </div>
            </div>

            {errors.timeRange && (
                <div className="input-error" style={{ marginBottom: 'var(--spacing-4)' }}>
                    <span>⚠️</span>
                    {errors.timeRange}
                </div>
            )}

            {/* Time Slot Preview */}
            {!errors.timeRange && (
                <TimeSlotPreview
                    startTime={startTime}
                    endTime={endTime}
                    lectureDuration={lectureDuration}
                    recessStart={formData.recessEnabled ? formData.recessStart : null}
                    recessDuration={formData.recessEnabled ? formData.recessDuration : 0}
                />
            )}
        </div>
    )
}

export default Step4WorkingDays
