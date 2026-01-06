import React from 'react';
import './TimetableGrid.css';

function TimetableGrid({ gridData = {}, conflictingSlots = [], onSlotClick, totalSlots, dayLayout }) {
    console.log("🧩 [TimetableGrid] Received gridData:", gridData);
    // Organize timetable into grid structure
    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

    // Helper: Safely get slots for a specific cell
    const getSlots = (day, slotIndex) => {
        try {
            return gridData[day]?.[slotIndex] || [];
        } catch (e) {
            return [];
        }
    };

    // Calculate columns based on layout OR totalSlots OR dynamic
    // Priority: dayLayout > totalSlots > dynamic
    const columns = (() => {
        if (dayLayout && dayLayout.length > 0) return dayLayout;

        let count = 0;
        if (totalSlots) {
            count = totalSlots;
        } else {
            // Dynamic calc
            let max = 6;
            Object.values(gridData).forEach(daySlots => {
                if (daySlots) {
                    Object.keys(daySlots).forEach(slotIdx => {
                        const idx = parseInt(slotIdx);
                        if (idx + 1 > max) max = idx + 1;
                    });
                }
            });
            count = max;
        }

        // Generate default lecture-only layout
        return Array.from({ length: count }, (_, i) => ({
            type: 'lecture',
            index: i + 1,
            label: `Slot ${i + 1}`
        }));
    })();

    // Helper: Check conflict
    const isSlotConflicting = (slot) => {
        return conflictingSlots.includes(slot.id);
    };

    const getConflictClass = (slot) => {
        const conflicting = isSlotConflicting(slot);
        if (!conflicting) return 'valid';
        return 'hard-conflict';
    };

    return (
        <div className="timetable-grid">

            <table className="grid-table">
                <thead>
                    <tr>
                        <th className="day-header">Day</th>
                        {columns.map((col, i) => (
                            <th key={i} className={`slot-header ${col.type === 'recess' ? 'recess-header' : ''}`}>
                                {col.label}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {days.map(day => (
                        <tr key={day}>
                            <td className="day-cell">{day}</td>

                            {columns.map((col, i) => {
                                if (col.type === 'recess') {
                                    return (
                                        <td key={i} className="slot-cell recess-cell">
                                            <div className="recess-content">Break</div>
                                        </td>
                                    );
                                }

                                // Lecture Slot
                                const currentSlotNum = col.index;
                                const cellSlots = getSlots(day, currentSlotNum);

                                return (
                                    <td key={i} className="slot-cell">
                                        {cellSlots && cellSlots.length > 0 ? (
                                            <div className="slot-content">
                                                {cellSlots.map((slot, idx) => (
                                                    <div
                                                        key={slot.id || idx}
                                                        className={`slot-item ${getConflictClass(slot)}`}
                                                        onClick={() => onSlotClick && onSlotClick(slot)}
                                                        title="Click to edit"
                                                    >
                                                        <div className="slot-subject">{slot.subject}</div>
                                                        <div className="slot-teacher">{slot.teacher}</div>
                                                        <div className="slot-room">📍 {slot.room || 'CR'}</div>
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
