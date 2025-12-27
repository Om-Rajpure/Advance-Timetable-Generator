import React from 'react'
import '../../styles/formComponents.css'
import '../../styles/branchSetup.css'
import ReviewCard from '../ReviewCard'

function Step7Review({ formData, onEditStep }) {
    const {
        branchName,
        academicYears,
        divisions,
        workingDays,
        startTime,
        endTime,
        lectureDuration,
        recessEnabled,
        recessStart,
        recessDuration,
        classrooms,
        sharedLabs
    } = formData

    // Calculate total slots
    const calculateSlots = () => {
        const timeToMinutes = (timeStr) => {
            const [time, period] = timeStr.split(' ')
            let [hours, minutes] = time.split(':').map(Number)
            if (period === 'PM' && hours !== 12) hours += 12
            if (period === 'AM' && hours === 12) hours = 0
            return hours * 60 + minutes
        }

        const totalMinutes = timeToMinutes(endTime) - timeToMinutes(startTime)
        const recessMins = recessEnabled ? recessDuration : 0
        const availableMinutes = totalMinutes - recessMins
        return Math.floor(availableMinutes / lectureDuration)
    }

    const totalSlots = calculateSlots()

    return (
        <div className="step-content">
            <h2 className="step-title">
                <span>✅</span>
                Review & Confirm
            </h2>
            <p className="step-description">
                Review your branch configuration before submitting. You can edit any section by clicking the Edit button.
            </p>

            {/* Branch Summary */}
            <ReviewCard
                title="Branch Identity"
                icon="🎓"
                onEdit={() => onEditStep(0)}
            >
                <div className="review-info-item">
                    <span className="review-info-label">Branch Name:</span>
                    <span className="review-info-value"><strong>{branchName}</strong></span>
                </div>
            </ReviewCard>

            {/* Academic Structure */}
            <ReviewCard
                title="Academic Structure"
                icon="📚"
                onEdit={() => onEditStep(1)}
            >
                <table className="review-table">
                    <thead>
                        <tr>
                            <th>Year</th>
                            <th>Divisions</th>
                            <th>Count</th>
                        </tr>
                    </thead>
                    <tbody>
                        {academicYears.map((year) => (
                            <tr key={year}>
                                <td><strong>{year}</strong></td>
                                <td>{divisions[year]?.join(', ')}</td>
                                <td>{divisions[year]?.length || 0}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </ReviewCard>

            {/* Schedule Summary */}
            <ReviewCard
                title="Weekly Schedule"
                icon="📅"
                onEdit={() => onEditStep(3)}
            >
                <div className="review-info-item">
                    <span className="review-info-label">Working Days:</span>
                    <span className="review-info-value">{workingDays.join(', ')}</span>
                </div>
                <div className="review-info-item">
                    <span className="review-info-label">Daily Schedule:</span>
                    <span className="review-info-value">{startTime} - {endTime}</span>
                </div>
                <div className="review-info-item">
                    <span className="review-info-label">Lecture Duration:</span>
                    <span className="review-info-value">{lectureDuration} minutes</span>
                </div>
                <div className="review-info-item">
                    <span className="review-info-label">Slots Per Day:</span>
                    <span className="review-info-value"><strong>{totalSlots} slots</strong></span>
                </div>
                {recessEnabled && (
                    <div className="review-info-item">
                        <span className="review-info-label">Recess:</span>
                        <span className="review-info-value">{recessStart} ({recessDuration} minutes)</span>
                    </div>
                )}
            </ReviewCard>

            {/* Facilities */}
            <ReviewCard
                title="Facilities"
                icon="🏫"
                onEdit={() => onEditStep(5)}
            >
                <div style={{ marginBottom: 'var(--spacing-4)' }}>
                    <h4 style={{ marginBottom: 'var(--spacing-2)', color: 'var(--color-gray-700)' }}>
                        Classrooms
                    </h4>
                    {academicYears.map((year) => (
                        <div key={year} style={{ marginBottom: 'var(--spacing-2)' }}>
                            <strong>{year}:</strong> {classrooms[year]?.join(', ') || 'None'}
                        </div>
                    ))}
                </div>

                <div>
                    <h4 style={{ marginBottom: 'var(--spacing-2)', color: 'var(--color-gray-700)' }}>
                        Shared Labs
                    </h4>
                    <ul className="review-list">
                        {sharedLabs.map((lab, idx) => (
                            <li key={idx}>
                                {lab.name} {lab.capacity && `- Capacity: ${lab.capacity}`}
                            </li>
                        ))}
                    </ul>
                </div>
            </ReviewCard>

            {/* Summary Stats */}
            <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
                gap: 'var(--spacing-4)',
                marginTop: 'var(--spacing-6)',
                padding: 'var(--spacing-6)',
                background: 'var(--gradient-card)',
                borderRadius: 'var(--radius-xl)',
                border: '2px solid var(--color-primary)'
            }}>
                <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: 'var(--font-size-3xl)', fontWeight: 'bold', color: 'var(--color-primary)' }}>
                        {academicYears.length}
                    </div>
                    <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-gray-600)' }}>
                        Years
                    </div>
                </div>
                <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: 'var(--font-size-3xl)', fontWeight: 'bold', color: 'var(--color-primary)' }}>
                        {academicYears.reduce((sum, year) => sum + (divisions[year]?.length || 0), 0)}
                    </div>
                    <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-gray-600)' }}>
                        Total Divisions
                    </div>
                </div>
                <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: 'var(--font-size-3xl)', fontWeight: 'bold', color: 'var(--color-primary)' }}>
                        {totalSlots}
                    </div>
                    <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-gray-600)' }}>
                        Slots/Day
                    </div>
                </div>
                <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: 'var(--font-size-3xl)', fontWeight: 'bold', color: 'var(--color-primary)' }}>
                        {sharedLabs.length}
                    </div>
                    <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-gray-600)' }}>
                        Labs
                    </div>
                </div>
            </div>
        </div>
    )
}

export default Step7Review
