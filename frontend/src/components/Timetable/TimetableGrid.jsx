import React from 'react';
import TimetableCell from './TimetableCell';
import { getSlotTimeRange } from '../../utils/timetableTransforms';
import './Timetable.css';

const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
const slots = [1, 2, 3, 4, 5, 6, 7]; // Assuming 7 slots max for now, need dynamic later

const TimetableGrid = ({ gridData, year, division, branchData }) => {
    // Determine recess slot (e.g., slot 4 is recess?)
    // For now hardcoding or deriving from config.
    // Assuming generated data might have a specific 'Break' entry or we check config.
    // Let's rely on visuals for now: if slot index == 3 (4th slot) implies 12:00-1:00 usually?
    const recessSlotIndex = branchData?.recessSlot ? parseInt(branchData.recessSlot) - 1 : 3;

    // Resolve max slots from data to avoid empty rows
    const maxSlot = 7; // Default

    // Grid Helpers
    const getCellData = (day, slotIndex) => {
        if (!gridData || !gridData[day]) return [];
        return gridData[day][slotIndex + 1] || []; // Slot indices are 1-based in backend usually
    };

    return (
        <div className="tt-grid-container">
            {/* Header Row: Days */}
            <div className="tt-header-row">
                <div className="tt-header-cell time-col">Time</div>
                {days.map(day => (
                    <div key={day} className="tt-header-cell">{day}</div>
                ))}
            </div>

            {/* Grid Body */}
            <div className="tt-body">
                {Array.from({ length: maxSlot }).map((_, slotIdx) => {
                    const isRecess = slotIdx === recessSlotIndex;
                    const timeLabel = getSlotTimeRange(slotIdx, branchData);

                    if (isRecess) {
                        return (
                            <div key={`recess-${slotIdx}`} className="tt-row recess-row">
                                <div className="tt-time-cell">{timeLabel}</div>
                                <div className="tt-recess-full">
                                    ☕ LUNCH BREAK / RECESS
                                </div>
                            </div>
                        )
                    }

                    return (
                        <div key={`slot-${slotIdx}`} className="tt-row">
                            <div className="tt-time-cell">
                                <span className="time-range">{timeLabel}</span>
                                <span className="slot-num">Slot {slotIdx + 1}</span>
                            </div>
                            {days.map(day => (
                                <div key={`${day}-${slotIdx}`} className="tt-day-col">
                                    <TimetableCell entries={getCellData(day, slotIdx)} />
                                </div>
                            ))}
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default TimetableGrid;
