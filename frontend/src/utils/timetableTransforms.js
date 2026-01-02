/**
 * Transforms timetable slots into a structured grid format, handling both flat arrays and nested objects.
 * @param {Array|Object} data - Array of slot objects (flat) or nested object { Year: { Div: { Day: [SlotObjects] } } }
 * @param {Object} branchData - Branch configuration (for Recess/Times)
 * @returns {Object} Structured data { [year]: { [division]: { [day]: { [slotIndex]: [entries] } } } }
 */
export const transformToGrid = (data, branchData) => {
    if (!data) return {};

    const grid = {};

    // Debug Incoming Data
    // console.log("transformToGrid Input:", Object.keys(data));

    // CASE 1: Flat List (Legacy / Initial Implementation)
    if (Array.isArray(data)) {
        // Sort slots by time to ensure order
        const sortedSlots = [...data].sort((a, b) => a.slot - b.slot);

        sortedSlots.forEach(slot => {
            const { year, division, day, slot: slotIndex } = slot;

            if (!grid[year]) grid[year] = {};
            if (!grid[year][division]) grid[year][division] = {};
            if (!grid[year][division][day]) grid[year][division][day] = {};
            if (!grid[year][division][day][slotIndex]) grid[year][division][day][slotIndex] = [];

            // Check for duplicates
            const existing = grid[year][division][day][slotIndex];
            const isDuplicate = existing.some(s => s.batch === slot.batch && s.id === slot.id);

            if (!isDuplicate) {
                grid[year][division][day][slotIndex].push(slot);
            }
        });
        return grid;
    }

    // CASE 2 & 3: Nested Object (New Academic Engine or Canonical Format)
    // Structure A: { Year: { Div: { Day: [SlotObjects] } } }
    // Structure B: { "Year-Div": { Day: [SlotObjects] } } (Canonical)

    Object.keys(data).forEach(key => {
        // Check if key is "Year-Div"
        if (key.includes('-')) {
            const [year, div] = key.split('-');

            if (!grid[year]) grid[year] = {};
            if (!grid[year][div]) grid[year][div] = {};

            const schedule = data[key]; // { Day: [Slots] }
            Object.keys(schedule).forEach(day => {
                if (!grid[year][div][day]) grid[year][div][day] = {};

                const slotsList = schedule[day];
                if (Array.isArray(slotsList)) {
                    slotsList.forEach(slot => {
                        const slotIdx = slot.slot;
                        if (!grid[year][div][day][slotIdx]) grid[year][div][day][slotIdx] = [];
                        grid[year][div][day][slotIdx].push(slot);
                    });
                }
            });

        } else {
            // Assume Standard Nested { Year: { Div: ... } }
            const year = key;
            if (!grid[year]) grid[year] = {};

            // Check if value is object (Divisions)
            if (typeof data[year] === 'object') {
                Object.keys(data[year]).forEach(div => {
                    grid[year][div] = {};
                    // ... rest of logic for deep nested (can reuse logic?)
                    // For simplicity, inline standard nested logic
                    Object.keys(data[year][div]).forEach(day => {
                        grid[year][div][day] = {};
                        const slotsList = data[year][div][day];
                        if (Array.isArray(slotsList)) {
                            slotsList.forEach(slot => {
                                const slotIdx = slot.slot;
                                if (!grid[year][div][day][slotIdx]) grid[year][div][day][slotIdx] = [];
                                grid[year][div][day][slotIdx].push(slot);
                            });
                        }
                    });
                });
            }
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
