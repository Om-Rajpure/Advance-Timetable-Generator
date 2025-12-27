/**
 * Conflict Detector Utility
 * Detects and validates conflicts in parsed timetable data
 */

/**
 * Detect all conflicts in timetable slots
 */
export function detectAllConflicts(slots, branchData = null, smartInputData = null) {
    const conflicts = []

    // Teacher conflicts
    conflicts.push(...findTeacherConflicts(slots))

    // Room conflicts
    conflicts.push(...findRoomConflicts(slots))

    // Practical violations
    conflicts.push(...validatePracticals(slots))

    // Structural validation (if data provided)
    if (branchData || smartInputData) {
        conflicts.push(...validateStructure(slots, branchData, smartInputData))
    }

    // Add conflict IDs
    conflicts.forEach((conflict, index) => {
        conflict.id = `conflict-${index}`
    })

    return {
        conflicts,
        summary: {
            total: conflicts.length,
            errors: conflicts.filter(c => c.severity === 'error').length,
            warnings: conflicts.filter(c => c.severity === 'warning').length
        }
    }
}

/**
 * Find teacher conflicts (same teacher at same time)
 */
export function findTeacherConflicts(slots) {
    const conflicts = []
    const teacherSchedule = {}

    slots.forEach(slot => {
        // Skip slots without teachers
        if (!slot.teacher || slot.teacher === 'TBA') return

        const key = `${slot.day}-${slot.slot}`

        if (!teacherSchedule[key]) {
            teacherSchedule[key] = {}
        }

        const teacher = slot.teacher

        if (!teacherSchedule[key][teacher]) {
            teacherSchedule[key][teacher] = []
        }

        teacherSchedule[key][teacher].push(slot)
    })

    // Check for conflicts
    Object.entries(teacherSchedule).forEach(([timeKey, teachers]) => {
        Object.entries(teachers).forEach(([teacher, slotList]) => {
            if (slotList.length > 1) {
                const [day, slot] = timeKey.split('-')
                conflicts.push({
                    type: 'teacher',
                    severity: 'error',
                    message: `Teacher "${teacher}" is assigned to multiple divisions at the same time`,
                    details: {
                        teacher,
                        day,
                        slot: parseInt(slot),
                        divisions: slotList.map(s => `${s.year}-${s.division}`).join(', ')
                    },
                    affectedSlots: slotList.map(s => s.id)
                })
            }
        })
    })

    return conflicts
}

/**
 * Find room/lab conflicts (same room at same time)
 */
export function findRoomConflicts(slots) {
    const conflicts = []
    const roomSchedule = {}

    slots.forEach(slot => {
        // Skip slots without rooms
        if (!slot.room || slot.room === 'TBA') return

        const key = `${slot.day}-${slot.slot}`

        if (!roomSchedule[key]) {
            roomSchedule[key] = {}
        }

        const room = slot.room

        if (!roomSchedule[key][room]) {
            roomSchedule[key][room] = []
        }

        roomSchedule[key][room].push(slot)
    })

    // Check for conflicts
    Object.entries(roomSchedule).forEach(([timeKey, rooms]) => {
        Object.entries(rooms).forEach(([room, slotList]) => {
            if (slotList.length > 1) {
                const [day, slot] = timeKey.split('-')
                conflicts.push({
                    type: 'room',
                    severity: 'warning', // Room conflicts are warnings, not hard errors
                    message: `Room "${room}" is booked for multiple divisions at the same time`,
                    details: {
                        room,
                        day,
                        slot: parseInt(slot),
                        divisions: slotList.map(s => `${s.year}-${s.division}`).join(', ')
                    },
                    affectedSlots: slotList.map(s => s.id)
                })
            }
        })
    })

    return conflicts
}

/**
 * Validate practical batch alignment
 */
export function validatePracticals(slots) {
    const conflicts = []
    const practicalSlots = slots.filter(s => s.type === 'Practical')

    // Group by subject, year, division, day, slot
    const practicalGroups = {}

    practicalSlots.forEach(slot => {
        const key = `${slot.subject}-${slot.year}-${slot.division}-${slot.day}-${slot.slot}`

        if (!practicalGroups[key]) {
            practicalGroups[key] = []
        }

        practicalGroups[key].push(slot)
    })

    // Check each group
    Object.entries(practicalGroups).forEach(([key, group]) => {
        const [subject, year, division, day, slot] = key.split('-')

        // Check if batches are specified
        const hasBatches = group.some(s => s.batch)

        if (group.length > 1 && !hasBatches) {
            conflicts.push({
                type: 'practical',
                severity: 'warning',
                message: `Multiple practical slots for same subject without batch assignments`,
                details: {
                    subject,
                    year,
                    division,
                    day,
                    slot: parseInt(slot),
                    count: group.length
                },
                affectedSlots: group.map(s => s.id)
            })
        }

        // Check for missing lab assignments
        const missingLab = group.filter(s => !s.room || s.room === 'TBA')
        if (missingLab.length > 0) {
            conflicts.push({
                type: 'practical',
                severity: 'warning',
                message: `Practical slots missing lab/room assignment`,
                details: {
                    subject,
                    year,
                    division,
                    day,
                    slot: parseInt(slot)
                },
                affectedSlots: missingLab.map(s => s.id)
            })
        }
    })

    return conflicts
}

/**
 * Validate structure against branch setup and smart input data
 */
export function validateStructure(slots, branchData, smartInputData) {
    const conflicts = []

    // Get valid years and divisions from branch data
    const validYears = branchData?.years || []
    const validDivisions = branchData?.divisions || []

    // Get valid subjects and teachers from smart input
    const validSubjects = smartInputData?.subjects?.map(s => s.name.toLowerCase()) || []
    const validTeachers = smartInputData?.teachers?.map(t => t.name.toLowerCase()) || []

    slots.forEach(slot => {
        // Check year validity
        if (validYears.length > 0 && !validYears.includes(slot.year)) {
            conflicts.push({
                type: 'structural',
                severity: 'warning',
                message: `Year "${slot.year}" not found in branch setup`,
                details: {
                    year: slot.year,
                    validYears,
                    slot: `${slot.day} ${slot.slot}`
                },
                affectedSlots: [slot.id]
            })
        }

        // Check division validity
        if (validDivisions.length > 0 && !validDivisions.includes(slot.division)) {
            conflicts.push({
                type: 'structural',
                severity: 'warning',
                message: `Division "${slot.division}" not found in branch setup`,
                details: {
                    division: slot.division,
                    validDivisions,
                    slot: `${slot.day} ${slot.slot}`
                },
                affectedSlots: [slot.id]
            })
        }

        // Check subject validity
        if (validSubjects.length > 0 &&
            slot.subject !== 'Unassigned' &&
            !validSubjects.includes(slot.subject.toLowerCase())) {
            conflicts.push({
                type: 'structural',
                severity: 'warning',
                message: `Subject "${slot.subject}" not found in smart input data`,
                details: {
                    subject: slot.subject,
                    suggestion: 'Add this subject in Smart Input or verify spelling',
                    slot: `${slot.day} ${slot.slot}`
                },
                affectedSlots: [slot.id]
            })
        }

        // Check teacher validity
        if (validTeachers.length > 0 &&
            slot.teacher !== 'TBA' &&
            !validTeachers.includes(slot.teacher.toLowerCase())) {
            conflicts.push({
                type: 'structural',
                severity: 'warning',
                message: `Teacher "${slot.teacher}" not found in smart input data`,
                details: {
                    teacher: slot.teacher,
                    suggestion: 'Add this teacher in Smart Input or verify spelling',
                    slot: `${slot.day} ${slot.slot}`
                },
                affectedSlots: [slot.id]
            })
        }
    })

    return conflicts
}

/**
 * Get conflict severity color
 */
export function getConflictColor(severity) {
    const colors = {
        error: '#EF4444',
        warning: '#F59E0B',
        info: '#3B82F6'
    }
    return colors[severity] || colors.info
}

/**
 * Group conflicts by type
 */
export function groupConflictsByType(conflicts) {
    return conflicts.reduce((groups, conflict) => {
        const type = conflict.type
        if (!groups[type]) {
            groups[type] = []
        }
        groups[type].push(conflict)
        return groups
    }, {})
}

/**
 * Filter conflicts by severity
 */
export function filterConflictsBySeverity(conflicts, severity) {
    return conflicts.filter(c => c.severity === severity)
}

/**
 * Check if timetable has critical errors
 */
export function hasCriticalErrors(conflicts) {
    return conflicts.some(c => c.severity === 'error')
}

/**
 * Generate conflict summary report
 */
export function generateConflictReport(conflicts) {
    const grouped = groupConflictsByType(conflicts)
    const errors = filterConflictsBySeverity(conflicts, 'error')
    const warnings = filterConflictsBySeverity(conflicts, 'warning')

    return {
        total: conflicts.length,
        errors: errors.length,
        warnings: warnings.length,
        hasCriticalErrors: hasCriticalErrors(conflicts),
        byType: {
            teacher: grouped.teacher?.length || 0,
            room: grouped.room?.length || 0,
            practical: grouped.practical?.length || 0,
            structural: grouped.structural?.length || 0
        },
        canProceed: errors.length === 0 // Can proceed if no hard errors
    }
}

export default {
    detectAllConflicts,
    findTeacherConflicts,
    findRoomConflicts,
    validatePracticals,
    validateStructure,
    getConflictColor,
    groupConflictsByType,
    filterConflictsBySeverity,
    hasCriticalErrors,
    generateConflictReport
}
