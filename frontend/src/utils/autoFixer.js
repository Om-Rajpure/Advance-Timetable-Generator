
/**
 * Auto Fixer Utility
 * Finds the nearest valid slot for a conflicting lecture
 */

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
const MAX_SLOTS = 8; // Assuming 8 slots/day standard

/**
 * Find the best available slot for a given lecture
 * @param {Object} slotToCheck - The slot object causing conflict
 * @param {Array} allSlots - The entire timetable (all classes)
 * @param {Object} branchData - Context for slot limits (optional)
 * @returns {Object|null} - { day, slot } or null if no fix found
 */
export function findAutoFix(slotToCheck, allSlots, branchData = null) {
    // 1. Extract Constraints
    const teacher = slotToCheck.teacher;
    const room = slotToCheck.room;
    const year = slotToCheck.year;
    const division = slotToCheck.division;
    const currentId = slotToCheck.id;

    // 2. Iterate through all possible time slots (Day -> Slot)
    for (const day of DAYS) {
        // Determine slots for this day (could be variable, but using standard 8 for now)
        for (let slot = 1; slot <= MAX_SLOTS; slot++) {

            // Skip if it's the SAME slot (moving to itself doesn't fix anything)
            if (day === slotToCheck.day && slot === Number(slotToCheck.slot)) continue;

            // 3. Check Validity
            if (isSlotFree(day, slot, teacher, room, year, division, allSlots, currentId)) {
                return { day, slot };
            }
        }
    }

    return null; // No valid slot found
}

/**
 * Check if a specific time slot is free from conflicts
 */
function isSlotFree(day, slot, teacher, room, year, division, allSlots, currentId) {
    // Check against every other slot in the universe
    for (const other of allSlots) {
        if (other.id === currentId) continue; // Skip self

        // Same Time Check
        if (other.day === day && Number(other.slot) === slot) {

            // A. Teacher Conflict: Is this teacher busy elsewhere?
            if (teacher && teacher !== 'TBA' && other.teacher === teacher) {
                return false;
            }

            // B. Room Conflict: Is this room occupied?
            if (room && room !== 'TBA' && other.room === room) {
                return false;
            }

            // C. Class Occupied: Is this class (Year-Div) already having a lecture?
            if (other.year === year && other.division === division) {
                return false; // Class is busy
            }
        }
    }

    return true; // No conflicts found!
}
