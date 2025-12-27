import React, { useState } from 'react'
import PropTypes from 'prop-types'
import ConflictBadge from './ConflictBadge'

function TimetablePreview({ slots = [], conflicts = [], onBack, onConfirm }) {
    const [selectedConflicts, setSelectedConflicts] = useState(null)

    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    const maxSlots = Math.max(...slots.map(s => s.slot), 7) + 1

    // Group slots by year-division
    const divisions = [...new Set(slots.map(s => `${s.year}-${s.division}`))].sort()
    const [activeDivision, setActiveDivision] = useState(divisions[0] || 'SE-A')

    // Get slots for active division
    const divisionSlots = slots.filter(s => `${s.year}-${s.division}` === activeDivision)

    // Create timetable grid
    const getTimetableGrid = () => {
        const grid = {}

        days.forEach(day => {
            grid[day] = Array(maxSlots).fill(null)
        })

        divisionSlots.forEach(slot => {
            if (grid[slot.day]) {
                grid[slot.day][slot.slot] = slot
            }
        })

        return grid
    }

    const grid = getTimetableGrid()

    // Get conflicts for a specific slot
    const getSlotConflicts = (slotId) => {
        return conflicts.filter(c => c.affectedSlots?.includes(slotId))
    }

    // Get cell style based on conflicts
    const getCellStyle = (slot) => {
        if (!slot) return {}

        const slotConflicts = getSlotConflicts(slot.id)
        if (slotConflicts.length === 0) return {}

        const hasError = slotConflicts.some(c => c.severity === 'error')
        const hasWarning = slotConflicts.some(c => c.severity === 'warning')

        if (hasError) {
            return {
                borderColor: '#EF4444',
                backgroundColor: '#FEE2E2'
            }
        } else if (hasWarning) {
            return {
                borderColor: '#F59E0B',
                backgroundColor: '#FEF3C7'
            }
        }

        return {}
    }

    const formatTimeSlot = (slotIndex) => {
        const startHour = 9 + slotIndex
        const endHour = startHour + 1
        return `${startHour}:00 - ${endHour}:00`
    }

    const summary = {
        totalSlots: slots.length,
        divisions: divisions.length,
        conflicts: conflicts.length,
        errors: conflicts.filter(c => c.severity === 'error').length,
        warnings: conflicts.filter(c => c.severity === 'warning').length
    }

    const canProceed = summary.errors === 0

    return (
        <div className="timetable-preview">
            <div className="preview-header">
                <h3>📅 Timetable Preview</h3>
                <p className="preview-description">
                    Review your parsed timetable and check for conflicts before proceeding
                </p>
            </div>

            {/* Summary Stats */}
            <div className="preview-stats">
                <div className="stat-card">
                    <div className="stat-value">{summary.totalSlots}</div>
                    <div className="stat-label">Total Slots</div>
                </div>
                <div className="stat-card">
                    <div className="stat-value">{summary.divisions}</div>
                    <div className="stat-label">Divisions</div>
                </div>
                <div className="stat-card success">
                    <div className="stat-value">
                        {summary.totalSlots - conflicts.filter(c => c.affectedSlots).flatMap(c => c.affectedSlots).length}
                    </div>
                    <div className="stat-label">Valid Slots</div>
                </div>
                {summary.errors > 0 && (
                    <div className="stat-card error">
                        <div className="stat-value">{summary.errors}</div>
                        <div className="stat-label">Errors</div>
                    </div>
                )}
                {summary.warnings > 0 && (
                    <div className="stat-card warning">
                        <div className="stat-value">{summary.warnings}</div>
                        <div className="stat-label">Warnings</div>
                    </div>
                )}
            </div>

            {/* Division Tabs */}
            {divisions.length > 1 && (
                <div className="division-tabs">
                    {divisions.map(div => (
                        <button
                            key={div}
                            className={`division-tab ${div === activeDivision ? 'active' : ''}`}
                            onClick={() => setActiveDivision(div)}
                        >
                            {div}
                        </button>
                    ))}
                </div>
            )}

            {/* Timetable Grid */}
            <div className="timetable-grid-wrapper">
                <table className="timetable-grid">
                    <thead>
                        <tr>
                            <th className="time-header">Time</th>
                            {days.map(day => (
                                <th key={day} className="day-header">{day}</th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {Array.from({ length: maxSlots }).map((_, slotIndex) => (
                            <tr key={slotIndex}>
                                <td className="time-cell">{formatTimeSlot(slotIndex)}</td>
                                {days.map(day => {
                                    const slot = grid[day]?.[slotIndex]
                                    const slotConflicts = slot ? getSlotConflicts(slot.id) : []

                                    return (
                                        <td
                                            key={day}
                                            className={`timetable-cell ${slot ? 'filled' : 'empty'}`}
                                            style={getCellStyle(slot)}
                                        >
                                            {slot ? (
                                                <div className="slot-content">
                                                    <div className="slot-subject">{slot.subject}</div>
                                                    <div className="slot-teacher">{slot.teacher}</div>
                                                    <div className="slot-room">{slot.room}</div>
                                                    {slotConflicts.length > 0 && (
                                                        <div className="slot-conflicts">
                                                            <ConflictBadge
                                                                conflicts={slotConflicts}
                                                                severity={slotConflicts[0].severity}
                                                            />
                                                        </div>
                                                    )}
                                                </div>
                                            ) : (
                                                <div className="empty-slot">—</div>
                                            )}
                                        </td>
                                    )
                                })}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Conflict Summary */}
            {conflicts.length > 0 && (
                <div className="conflict-summary">
                    <h4>⚠️ Detected Conflicts ({conflicts.length})</h4>
                    <div className="conflict-summary-badges">
                        {summary.errors > 0 && (
                            <ConflictBadge
                                conflicts={conflicts}
                                severity="error"
                                onClick={(c) => setSelectedConflicts(c)}
                            />
                        )}
                        {summary.warnings > 0 && (
                            <ConflictBadge
                                conflicts={conflicts}
                                severity="warning"
                                onClick={(c) => setSelectedConflicts(c)}
                            />
                        )}
                    </div>
                    {!canProceed && (
                        <p className="error-message">
                            ❌ You must fix all errors before proceeding. Click "Fix Mapping" to adjust column mappings.
                        </p>
                    )}
                    {canProceed && summary.warnings > 0 && (
                        <p className="warning-message">
                            ⚠️ Warnings detected but you can still proceed. Review carefully.
                        </p>
                    )}
                </div>
            )}

            {/* Actions */}
            <div className="preview-actions">
                <button className="btn-secondary btn-lg" onClick={onBack}>
                    ← Fix Mapping
                </button>
                <button
                    className="btn-primary btn-lg"
                    onClick={onConfirm}
                    disabled={!canProceed}
                    title={!canProceed ? 'Fix errors before proceeding' : ''}
                >
                    {canProceed ? 'Confirm & Proceed →' : '🔒 Fix Errors First'}
                </button>
            </div>
        </div>
    )
}

TimetablePreview.propTypes = {
    slots: PropTypes.arrayOf(PropTypes.shape({
        id: PropTypes.string.isRequired,
        day: PropTypes.string.isRequired,
        slot: PropTypes.number.isRequired,
        subject: PropTypes.string,
        teacher: PropTypes.string,
        room: PropTypes.string,
        year: PropTypes.string,
        division: PropTypes.string,
        type: PropTypes.string,
        batch: PropTypes.string
    })),
    conflicts: PropTypes.array,
    onBack: PropTypes.func.isRequired,
    onConfirm: PropTypes.func.isRequired
}

export default TimetablePreview
