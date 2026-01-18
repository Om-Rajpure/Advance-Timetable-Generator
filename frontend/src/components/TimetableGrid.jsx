import React from 'react';
import './TimetableGrid.css';

function TimetableGrid({ gridData = {}, conflictingSlots = [], onSlotClick, dayLayout = [] }) {
    // console.log("🧩 [TimetableGrid] Layout:", dayLayout);
    // console.log("🧩 [TimetableGrid] Data:", gridData);

    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

    // 1. Columns derived STRICTLY from dayLayout
    // If no layout provided, we can't render correctly.
    if (!dayLayout || dayLayout.length === 0) {
        return <div className="no-layout">No time layout available.</div>;
    }

    // CSS Grid Template: 100px (Day) + n columns
    // Use MINMAX to prevent shrinking, repeat(N) for exact count.
    const gridStyle = {
        gridTemplateColumns: `100px repeat(${dayLayout.length}, minmax(140px, 1fr))`
    };

    // Helper: Get slots for a specific day and visual index
    const getSlotsForIndex = (day, visualIndex) => {
        try {
            return gridData[day]?.[visualIndex] || [];
        } catch (e) {
            return [];
        }
    };

    const isSlotConflicting = (slotId) => conflictingSlots.includes(slotId);

    return (
        <div className="timetable-grid">
            <div className="grid-container-view" style={gridStyle}>

                {/* HEADER ROW */}
                <div className="grid-header-cell">Day</div>
                {dayLayout.map((col, i) => (
                    <div key={`head-${i}`} className={`grid-header-cell ${col.type === 'recess' ? 'recess-header' : ''}`}>
                        {col.label}
                    </div>
                ))}

                {/* DAY ROWS */}
                {days.map(day => (
                    <React.Fragment key={day}>
                        {/* Day Label */}
                        <div className="grid-day-cell">{day}</div>

                        {/* Slots */}
                        {(() => {
                            const rowCells = [];

                            // Use a traditional loop to handle spanning
                            for (let i = 0; i < dayLayout.length; i++) {
                                const col = dayLayout[i];

                                // RECESS CELL
                                if (col.type === 'recess') {
                                    rowCells.push(
                                        <div key={`${day}-recess-${i}`} className="grid-cell grid-recess-cell">
                                            {/* No Text as requested */}
                                        </div>
                                    );
                                    continue;
                                }

                                // LECTURE SLOT
                                const visualIndex = col.index;
                                const cellSlots = getSlotsForIndex(day, visualIndex);

                                // SPANNING CHECK
                                // If this cell has a slot that has duration > 1 or implies spanning?
                                // We rely on backend data. If backend placed the same lab in Slot 1 and Slot 2,
                                // we want to merge them if they are identical.

                                let span = 1;
                                // Simple Merge Logic: Check next columns
                                if (cellSlots.length === 1 && (cellSlots[0].type === 'LAB' || cellSlots[0].isPractical || cellSlots[0].type === 'Practical')) {
                                    const currentSlot = cellSlots[0];

                                    for (let j = i + 1; j < dayLayout.length; j++) {
                                        const nextCol = dayLayout[j];
                                        if (nextCol.type === 'recess') break; // Never span recess

                                        const nextSlots = getSlotsForIndex(day, nextCol.index);
                                        if (nextSlots.length === 1) {
                                            const nextSlot = nextSlots[0];
                                            // Check identity
                                            if (nextSlot.subject === currentSlot.subject &&
                                                nextSlot.batch === currentSlot.batch &&
                                                nextSlot.teacher === currentSlot.teacher) {
                                                span++;
                                            } else {
                                                break;
                                            }
                                        } else {
                                            break;
                                        }
                                    }
                                }

                                // Only render IF we are at the start of the span (implicitly handled by loop skipping)
                                // But here we are iterating. We need to skip `i` if `span > 1`.
                                // However, standard map doesn't skip. We are building `rowCells` manually.

                                // Render the cell
                                rowCells.push(
                                    <div
                                        key={`${day}-${i}`}
                                        className="grid-cell"
                                        style={span > 1 ? { gridColumn: `span ${span}`, zIndex: 2 } : {}}
                                    >
                                        {cellSlots.length > 0 ? (
                                            <div className="slot-content">
                                                {cellSlots.map((slot, idx) => (
                                                    <div
                                                        key={slot.id || idx}
                                                        className={`slot-item ${isSlotConflicting(slot.id) ? 'hard-conflict' : 'valid'}`}
                                                        onClick={() => onSlotClick && onSlotClick(slot)}
                                                    >
                                                        <div className="slot-subject">{slot.subject}</div>
                                                        <div className="slot-teacher">{slot.teacher}</div>
                                                        <div className="slot-room">{slot.room || 'CR'}</div>
                                                        {slot.batch && <div className="slot-batch">{slot.batch}</div>}
                                                    </div>
                                                ))}
                                            </div>
                                        ) : (
                                            <div className="empty-slot">-</div>
                                        )}
                                    </div>
                                );

                                // Skip indices if spanned
                                i += (span - 1);
                            }

                            return rowCells;
                        })()}
                    </React.Fragment>
                ))}
            </div>
        </div>
    );
}

export default TimetableGrid;
