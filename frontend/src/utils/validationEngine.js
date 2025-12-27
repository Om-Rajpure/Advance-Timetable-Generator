/**
 * Validation Engine for Smart Input Module
 * Provides comprehensive validation for academic data before timetable generation
 */

/**
 * Validate complete smart input data
 * @param {Object} data - Complete data structure with teachers, subjects, etc.
 * @returns {Object} { valid: boolean, errors: Array, warnings: Array }
 */
export function validateSmartInputData(data) {
    const errors = []
    const warnings = []

    // Validate teachers
    const teacherValidation = validateTeachers(data.teachers || [])
    errors.push(...teacherValidation.errors)
    warnings.push(...teacherValidation.warnings)

    // Validate subjects
    const subjectValidation = validateSubjects(data.subjects || [])
    errors.push(...subjectValidation.errors)
    warnings.push(...subjectValidation.warnings)

    // Validate teacher-subject mapping
    const mappingValidation = validateTeacherSubjectMapping(
        data.teachers || [],
        data.subjects || [],
        data.teacherSubjectMap || []
    )
    errors.push(...mappingValidation.errors)
    warnings.push(...mappingValidation.warnings)

    // Validate workload
    const workloadValidation = validateTeacherWorkload(
        data.teachers || [],
        data.teacherSubjectMap || []
    )
    warnings.push(...workloadValidation.warnings)

    return {
        valid: errors.length === 0,
        errors,
        warnings
    }
}

/**
 * Validate teachers array
 */
function validateTeachers(teachers) {
    const errors = []
    const warnings = []
    const seenNames = new Set()

    teachers.forEach((teacher, index) => {
        // Required field validation
        if (!teacher.name || teacher.name.trim() === '') {
            errors.push({
                type: 'MISSING_FIELD',
                severity: 'error',
                message: `Teacher at index ${index} is missing a name`,
                field: 'teachers',
                index
            })
        }

        // Duplicate detection
        const normalizedName = teacher.name?.trim().toLowerCase()
        if (normalizedName && seenNames.has(normalizedName)) {
            errors.push({
                type: 'DUPLICATE',
                severity: 'error',
                message: `Duplicate teacher name: "${teacher.name}"`,
                field: 'teachers',
                value: teacher.name
            })
        }
        seenNames.add(normalizedName)

        // Validate max lectures per day
        if (teacher.maxLecturesPerDay !== undefined) {
            if (teacher.maxLecturesPerDay < 1 || teacher.maxLecturesPerDay > 10) {
                warnings.push({
                    type: 'UNUSUAL_VALUE',
                    severity: 'warning',
                    message: `Teacher "${teacher.name}" has unusual max lectures per day: ${teacher.maxLecturesPerDay}`,
                    field: 'teachers',
                    value: teacher.maxLecturesPerDay
                })
            }
        }
    })

    return { errors, warnings }
}

/**
 * Validate subjects array
 */
function validateSubjects(subjects) {
    const errors = []
    const warnings = []
    const seenSubjects = new Map() // key: name+year, value: subject

    subjects.forEach((subject, index) => {
        // Required fields
        if (!subject.name || subject.name.trim() === '') {
            errors.push({
                type: 'MISSING_FIELD',
                severity: 'error',
                message: `Subject at index ${index} is missing a name`,
                field: 'subjects',
                index
            })
        }

        if (!subject.year) {
            errors.push({
                type: 'MISSING_FIELD',
                severity: 'error',
                message: `Subject "${subject.name}" is missing academic year`,
                field: 'subjects',
                value: subject.name
            })
        }

        // Duplicate detection (same subject in same year)
        const key = `${subject.name?.trim().toLowerCase()}-${subject.year}`
        if (subject.name && subject.year) {
            if (seenSubjects.has(key)) {
                errors.push({
                    type: 'DUPLICATE',
                    severity: 'error',
                    message: `Duplicate subject: "${subject.name}" in year ${subject.year}`,
                    field: 'subjects',
                    value: subject.name
                })
            }
            seenSubjects.set(key, subject)
        }

        // Weekly lectures validation
        if (subject.weeklyLectures !== undefined) {
            if (subject.weeklyLectures < 1 || subject.weeklyLectures > 20) {
                warnings.push({
                    type: 'UNUSUAL_VALUE',
                    severity: 'warning',
                    message: `Subject "${subject.name}" has unusual weekly lectures: ${subject.weeklyLectures}`,
                    field: 'subjects',
                    value: subject.weeklyLectures
                })
            }
        } else {
            warnings.push({
                type: 'MISSING_OPTIONAL',
                severity: 'warning',
                message: `Subject "${subject.name}" is missing weekly lecture count`,
                field: 'subjects',
                value: subject.name
            })
        }

        // Check practical flag
        if (subject.isPractical && (!subject.weeklyLectures || subject.weeklyLectures < 2)) {
            warnings.push({
                type: 'PRACTICAL_WARNING',
                severity: 'warning',
                message: `Practical subject "${subject.name}" has low weekly lectures (${subject.weeklyLectures || 0})`,
                field: 'subjects',
                value: subject.name
            })
        }
    })

    return { errors, warnings }
}

/**
 * Validate teacher-subject mapping
 */
function validateTeacherSubjectMapping(teachers, subjects, mapping) {
    const errors = []
    const warnings = []

    const teacherIds = new Set(teachers.map(t => t.id))
    const subjectIds = new Set(subjects.map(s => s.id))

    // Check for unmapped teachers
    const mappedTeacherIds = new Set(mapping.map(m => m.teacherId))
    teachers.forEach(teacher => {
        if (!mappedTeacherIds.has(teacher.id)) {
            warnings.push({
                type: 'UNMAPPED_TEACHER',
                severity: 'warning',
                message: `Teacher "${teacher.name}" is not assigned to any subject`,
                field: 'teacherSubjectMap',
                value: teacher.name
            })
        }
    })

    // Check for unmapped subjects
    const mappedSubjectIds = new Set(mapping.map(m => m.subjectId))
    subjects.forEach(subject => {
        if (!mappedSubjectIds.has(subject.id)) {
            errors.push({
                type: 'UNMAPPED_SUBJECT',
                severity: 'error',
                message: `Subject "${subject.name}" (${subject.year}) has no teacher assigned`,
                field: 'teacherSubjectMap',
                value: subject.name
            })
        }
    })

    // Validate mapping integrity
    mapping.forEach((map, index) => {
        if (!teacherIds.has(map.teacherId)) {
            errors.push({
                type: 'INVALID_REFERENCE',
                severity: 'error',
                message: `Mapping at index ${index} references non-existent teacher`,
                field: 'teacherSubjectMap',
                index
            })
        }

        if (!subjectIds.has(map.subjectId)) {
            errors.push({
                type: 'INVALID_REFERENCE',
                severity: 'error',
                message: `Mapping at index ${index} references non-existent subject`,
                field: 'teacherSubjectMap',
                index
            })
        }
    })

    return { errors, warnings }
}

/**
 * Validate teacher workload
 */
function validateTeacherWorkload(teachers, mapping) {
    const warnings = []

    teachers.forEach(teacher => {
        const subjectCount = mapping.filter(m => m.teacherId === teacher.id).length
        const maxLectures = teacher.maxLecturesPerDay || 6

        // Check if teacher has too many subjects for their max lectures
        if (subjectCount > maxLectures) {
            warnings.push({
                type: 'HIGH_WORKLOAD',
                severity: 'warning',
                message: `Teacher "${teacher.name}" is assigned ${subjectCount} subjects but max ${maxLectures} lectures/day`,
                field: 'teachers',
                value: teacher.name
            })
        }

        // Check for very high subject count
        if (subjectCount > 8) {
            warnings.push({
                type: 'EXTREME_WORKLOAD',
                severity: 'warning',
                message: `Teacher "${teacher.name}" is assigned ${subjectCount} subjects (very high workload)`,
                field: 'teachers',
                value: teacher.name
            })
        }
    })

    return { warnings }
}

/**
 * Quick validation for specific field
 */
export function validateField(field, value, context = {}) {
    const errors = []

    switch (field) {
        case 'teacherName':
            if (!value || value.trim().length < 2) {
                errors.push('Teacher name must be at least 2 characters')
            }
            break

        case 'subjectName':
            if (!value || value.trim().length < 2) {
                errors.push('Subject name must be at least 2 characters')
            }
            break

        case 'weeklyLectures':
            const num = parseInt(value)
            if (isNaN(num) || num < 1 || num > 20) {
                errors.push('Weekly lectures must be between 1 and 20')
            }
            break

        case 'maxLecturesPerDay':
            const max = parseInt(value)
            if (isNaN(max) || max < 1 || max > 10) {
                errors.push('Max lectures per day must be between 1 and 10')
            }
            break
    }

    return errors
}

export default {
    validateSmartInputData,
    validateField
}
