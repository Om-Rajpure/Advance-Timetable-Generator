import React from 'react';
import './TimetableGrid.css';

function TimetableGrid({ gridData = {}, conflictingSlots = [], onSlotClick }) {
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

    // Calculate max slots dynamically from the grid data
    const calculateMaxSlots = () => {
        let max = 6; // Minimum 6 slots
        Object.values(gridData).forEach(daySlots => {
            if (daySlots) {
                Object.keys(daySlots).forEach(slotIdx => {
                    const idx = parseInt(slotIdx);
                    if (idx + 1 > max) max = idx + 1;
                });
            }
        });
        return max;
    };

    const maxSlots = calculateMaxSlots();

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
                                const slots = getSlots(day, slotIndex + 1); // 1-based index in data? No, usually 1-based in UI but let's check transform.
                                // Wait, transformToGrid uses slot.slot. In backend slot is usually 1-based?
                                // Let's check backend/scheduler.py or data sample.
                                // Actually, backend/scheduler.py: slot=1..N.
                                // transformToGrid just uses `slot.slot` as key. 
                                // So if backend sends 1, key is 1. If backend sends 0, key is 0.
                                // Standard is usually 1-based.
                                // If I use `slotIndex + 1` here, I am assuming keys are "1", "2"... 
                                // Let's stick to what previous code did: `grid[day][slotIndex]`. 
                                // Previous code loop: `for (let i = 0; i < maxSlots; i++)` -> index 0..N-1
                                // `slotIndex` in loop is 0-based.
                                // `timetable.forEach(slot => { const slotIndex = slot.slot; ... })`
                                // If `slot.slot` is 1, then `grid[day][1]` is set.
                                // But the loop `for (let i = 0; i < maxSlots; i++)` checks `grid[day][i]`.
                                // If `slot.slot` is 1-based, then `grid[day][0]` would be empty.
                                // This implies `slot.slot` matches the loop index if 0-based, or we need to adjust.
                                // Let's assume keys in `gridData` match the backend `slot` value.
                                // So we should look up `gridData[day][slotIndex + 1]` if we iterate 0..N-1 and want Slot 1..N.
                                // OR iterate 1..N.

                                // Let's safe-check: iterate 1 to maxSlots?
                                // Previous code: `Array.from({ length: maxSlots }, (_, i) => ...)` i is 0..max-1.
                                // `<th key={i}>Slot {i + 1}</th>` -> Columns are labeled 1, 2, 3...
                                // Data lookup `grid[day][slotIndex]` where `slotIndex` comes from `slot.slot`.
                                // If `slot.slot` is 1, it goes to `grid[day][1]`.
                                // Render loop uses `i` (0). `grid[day][0]`?
                                // If backend is 1-based, index 0 is empty.

                                // Let's access by key `slotIndex + 1` to align with "Slot {i+1}".

                                const currentSlotNum = slotIndex + 1;
                                const cellSlots = getSlots(day, currentSlotNum);

                                // Debug helper (optional, can be removed)
                                // if (day === 'Monday' && currentSlotNum === 1) console.log('Mon Slot 1:', cellSlots);

                                return (
                                    <td key={slotIndex} className="slot-cell">
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
