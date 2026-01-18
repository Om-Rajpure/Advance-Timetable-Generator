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

        // Generate default layout WITH TIMES (Fallback)
        const startTime = 9; // 9 AM
        return Array.from({ length: count }, (_, i) => {
            const time = startTime + i;
            const timeStr = time > 12 ? `${time - 12}:00 PM` : `${time}:00 ${time === 12 ? 'PM' : 'AM'}`;
            return {
                type: 'lecture',
                index: i + 1,
                label: `${timeStr} (Slot ${i + 1})`
            };
        });
    })();

    console.log("📅 [TimetableGrid] Using Columns:", columns);

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
                                            {/* PURELY VISUAL COLUMN - NO CONTENT */}
                                        </td>
                                    );
                                }

                                const currentSlotNum = col.index;
                                const cellSlots = getSlots(day, currentSlotNum);

                                // MERGE LOGIC: Check if this slot was already covered by a previous colSpan
                                if (col._skip) return null;

                                // Check if we can merge with NEXT slots
                                // Only merge if it's a LAB (or Practical) and looks identical to next one
                                let colSpan = 1;
                                if (cellSlots && cellSlots.length === 1) {
                                    const item = cellSlots[0];
                                    const isLab = item.type === 'LAB' || item.isPractical || item.type === 'Practical';

                                    if (isLab) {
                                        // Look ahead
                                        for (let k = i + 1; k < columns.length; k++) {
                                            const nextCol = columns[k];
                                            if (nextCol.type === 'recess') break; // Don't span across recess

                                            const nextSlots = getSlots(day, nextCol.index);
                                            if (nextSlots && nextSlots.length === 1) {
                                                const nextItem = nextSlots[0];
                                                // Identity check: Same subject + same batch + same teacher
                                                if (nextItem.subject === item.subject &&
                                                    nextItem.batch === item.batch &&
                                                    nextItem.teacher === item.teacher) {
                                                    colSpan++;
                                                    nextCol._skip = true; // Mark next col to be skipped
                                                } else {
                                                    break;
                                                }
                                            } else {
                                                break;
                                            }
                                        }
                                    }
                                }

                                return (
                                    <td key={i} className="slot-cell" colSpan={colSpan}>
                                        {cellSlots && cellSlots.length > 0 ? (
                                            <div className="slot-content">
                                                <span className="mobile-time-label">{col.label}</span>
                                                {cellSlots.map((slot, idx) => (
                                                    <div
                                                        key={slot.id || idx}
                                                        className={`slot-item ${getConflictClass(slot)} ${colSpan > 1 ? 'is-merged-lab' : ''}`}
                                                        onClick={() => onSlotClick && onSlotClick(slot)}
                                                        title="Click to edit"
                                                        style={colSpan > 1 ? { minHeight: '60px', justifyContent: 'center' } : {}}
                                                    >
                                                        <div className="slot-subject">{slot.subject}</div>
                                                        <div className="slot-teacher">{slot.teacher}</div>
                                                        <div className="slot-room">📍 {slot.room || 'CR'}</div>
                                                        {slot.batch && (
                                                            <div className="slot-batch">{slot.batch}</div>
                                                        )}
                                                        {colSpan > 1 && <div className="slot-duration-tag">({colSpan} Hrs)</div>}
                                                    </div>
                                                ))}
                                            </div>
                                        ) : (
                                            <div className="empty-slot">
                                                <span className="mobile-time-label">{col.label}</span>
                                                —
                                            </div>
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
