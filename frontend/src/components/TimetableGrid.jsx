import React from 'react';
import './TimetableGrid.css';

function TimetableGrid({ timetable, conflictingSlots, onSlotClick }) {
    // Organize timetable into grid structure
    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

    // Get max slots per day
    const maxSlots = timetable.length > 0
        ? Math.max(...timetable.map(s => s.slot)) + 1
        : 8;

    // Group slots by day and slot index
    const grid = {};
    days.forEach(day => {
        grid[day] = {};
        for (let i = 0; i < maxSlots; i++) {
            grid[day][i] = [];
        }
    });

    timetable.forEach(slot => {
        const day = slot.day;
        const slotIndex = slot.slot;
        if (grid[day] && grid[day][slotIndex] !== undefined) {
            grid[day][slotIndex].push(slot);
        }
    });

    const isSlotConflicting = (slot) => {
        return conflictingSlots.includes(slot.id);
    };

    const getConflictClass = (slot) => {
        const conflicting = isSlotConflicting(slot);
        if (!conflicting) return 'valid';

        // Check if it's a hard or soft conflict (would need to pass this info)
        return 'hard-conflict';
    };

    return (
        <div className="timetable-grid">
            <table className="grid-table">
                <thead>
                    <tr>
                        <th className="day-header">Day</th>
                        {Array.from({ length: maxSlots }, (_, i) => (
                            <th key={i} className="slot-header">
                                Slot {i + 1}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {days.map(day => (
                        <tr key={day}>
                            <td className="day-cell">{day}</td>
                            {Array.from({ length: maxSlots }, (_, slotIndex) => {
                                const slots = grid[day][slotIndex];

                                return (
                                    <td key={slotIndex} className="slot-cell">
                                        {slots.length > 0 ? (
                                            <div className="slot-content">
                                                {slots.map(slot => (
                                                    <div
                                                        key={slot.id}
                                                        className={`slot-item ${getConflictClass(slot)}`}
                                                        onClick={() => onSlotClick(slot)}
                                                        title="Click to edit"
                                                    >
                                                        <div className="slot-subject">{slot.subject}</div>
                                                        <div className="slot-teacher">{slot.teacher}</div>
                                                        <div className="slot-room">{slot.room}</div>
                                                        {slot.batch && (
                                                            <div className="slot-batch">{slot.batch}</div>
                                                        )}
                                                    </div>
                                                ))}
                                            </div>
                                        ) : (
                                            <div className="empty-slot">—</div>
                                        )}
                                    </td>
                                );
                            })}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

export default TimetableGrid;
