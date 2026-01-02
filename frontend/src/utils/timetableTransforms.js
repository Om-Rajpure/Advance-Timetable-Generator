/**
 * Transforms flat timetable slots into a structured grid format
 * @param {Array} flatSlots - Array of slot objects from backend
 * @param {Object} branchData - Branch configuration (for Recess/Times)
 * @returns {Object} Structured data { [year]: { [division]: { [day]: { [slotIndex]: [entries] } } } }
 */
export const transformToGrid = (flatSlots, branchData) => {
    if (!flatSlots || !Array.isArray(flatSlots)) return {};

    const grid = {};
    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

    // Sort slots by time to ensure order
    const sortedSlots = [...flatSlots].sort((a, b) => a.slot - b.slot);

    sortedSlots.forEach(slot => {
        const { year, division, day, slot: slotIndex } = slot;

        if (!grid[year]) grid[year] = {};
        if (!grid[year][division]) grid[year][division] = {};
        if (!grid[year][division][day]) grid[year][division][day] = {};
        if (!grid[year][division][day][slotIndex]) grid[year][division][day][slotIndex] = [];

        // Check for duplicates (e.g. same batch assigned twice? shouldn't happen but good to be safe)
        const existing = grid[year][division][day][slotIndex];
        const isDuplicate = existing.some(s => s.batch === slot.batch && s.id === slot.id);

        if (!isDuplicate) {
            grid[year][division][day][slotIndex].push(slot);
        }
    });

    return grid;
};

/**
 * Calculates time range string for a slot index
 * @param {Number} slotIndex - 0-based slot index
 * @param {Object} branchData - Branch config with startTime, duration
 * @returns {String} "9:00 - 10:00"
 */
export const getSlotTimeRange = (slotIndex, branchData) => {
    const startStr = branchData?.startTime || "9:00 AM";
    const duration = parseInt(branchData?.lectureDuration || 60);

    // Simplified parser
    let [time, modifier] = startStr.split(' ');
    let [hours, minutes] = time.split(':').map(Number);
    if (modifier === 'PM' && hours !== 12) hours += 12;
    if (modifier === 'AM' && hours === 12) hours = 0;

    const totalStartMinutes = (hours * 60) + minutes + (slotIndex * duration);
    const totalEndMinutes = totalStartMinutes + duration;

    const formatTime = (totalMins) => {
        let h = Math.floor(totalMins / 60);
        let m = totalMins % 60;
        const ampm = h >= 12 ? 'PM' : 'AM';
        if (h > 12) h -= 12;
        if (h === 0) h = 12;
        return `${h}:${m.toString().padStart(2, '0')} ${ampm}`;
    };

    return `${formatTime(totalStartMinutes)} - ${formatTime(totalEndMinutes)}`;
};
