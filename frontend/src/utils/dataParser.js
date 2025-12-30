/**
 * Data Parser Utilities for Smart Input Module
 * Handles parsing and normalization of data from various input sources
 */

import Papa from 'papaparse'

/**
 * Generate unique ID
 */
function generateId() {
    return `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`
}

/**
 * Normalize teacher name
 */
function normalizeTeacherName(name) {
    if (!name) return ''
    return name.trim()
        .split(' ')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
        .join(' ')
}

/**
 * Normalize subject name
 */
function normalizeSubjectName(name) {
    if (!name) return ''

    // Handle common abbreviations
    const abbreviations = {
        'ai': 'AI',
        'ml': 'ML',
        'ds': 'Data Science',
        'dbms': 'DBMS',
        'os': 'Operating Systems',
        'cn': 'Computer Networks',
        'dsa': 'Data Structures and Algorithms'
    }

    const normalized = name.trim().toLowerCase()

    if (abbreviations[normalized]) {
        return abbreviations[normalized]
    }

    // Capitalize each word
    return name.trim()
        .split(' ')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
        .join(' ')
}

/**
 * Parse CSV data
 */
export function parseCSV(csvText, fileType = 'teachers') {
    return new Promise((resolve, reject) => {
        Papa.parse(csvText, {
            header: true,
            skipEmptyLines: true,
            transformHeader: (header) => {
                // Normalize column headers
                return header.trim().toLowerCase().replace(/\s+/g, '_')
            },
            complete: (results) => {
                try {
                    const parsed = processCSVData(results.data, fileType)
                    resolve(parsed)
                } catch (error) {
                    reject(error)
                }
            },
            error: (error) => {
                reject(error)
            }
        })
    })
}

/**
 * Process parsed CSV data based on file type
 */
function processCSVData(data, fileType) {
    const processed = {
        data: [],
        errors: []
    }

    switch (fileType) {
        case 'teachers':
            data.forEach((row, index) => {
                const teacherName = row.teacher_name || row.name || row.teacher

                if (!teacherName) {
                    processed.errors.push({
                        row: index + 1,
                        message: 'Missing teacher name'
                    })
                    return
                }

                const maxLectures = parseInt(row.max_lectures_per_day || row.max_lectures || '6')

                processed.data.push({
                    id: generateId(),
                    name: normalizeTeacherName(teacherName),
                    maxLecturesPerDay: isNaN(maxLectures) ? 6 : maxLectures,
                    subjects: []
                })
            })
            break

        case 'subjects':
            data.forEach((row, index) => {
                const subjectName = row.subject_name || row.name || row.subject
                const year = row.year || row.academic_year

                if (!subjectName) {
                    processed.errors.push({
                        row: index + 1,
                        message: 'Missing subject name'
                    })
                    return
                }

                if (!year) {
                    processed.errors.push({
                        row: index + 1,
                        message: 'Missing academic year'
                    })
                    return
                }

                const weeklyLectures = parseInt(row.weekly_lectures || row.lectures || '4')

                // Smart Type Detection Logic
                let isPractical = false

                // 1. Check explicit 'type' column (Highest Priority)
                if (row.type) {
                    const typeVal = row.type.toLowerCase().trim()
                    if (typeVal === 'lab' || typeVal === 'practical') {
                        isPractical = true
                    }
                }
                // 2. Check traditional 'is_practical' boolean
                else if (row.is_practical || row.practical) {
                    isPractical = (row.is_practical || row.practical || '').toString().toLowerCase() === 'true'
                }
                // 3. Keyword Detection (Fallback)
                else {
                    const lowerName = subjectName.toLowerCase()
                    if (lowerName.includes('lab') || lowerName.includes('practical') || lowerName.includes('workshop')) {
                        isPractical = true
                    }
                }

                processed.data.push({
                    id: generateId(),
                    name: normalizeSubjectName(subjectName),
                    year: year.toUpperCase(),
                    weeklyLectures: isNaN(weeklyLectures) ? 4 : weeklyLectures,
                    isPractical // true = Lab, false = Theory
                })
            })
            break

        case 'teacher_subject_map':
            // This will be processed separately as it requires existing teacher/subject IDs
            processed.data = data.map(row => ({
                teacherName: normalizeTeacherName(row.teacher_name || row.teacher || ''),
                subjectName: normalizeSubjectName(row.subject_name || row.subject || '')
            }))
            break
    }

    return processed
}

/**
 * Parse bulk text input (Teacher: Subject1, Subject2)
 */
export function parseBulkText(text, academicYears = ['SE', 'TE', 'BE']) {
    const teachers = []
    const subjects = []
    const mapping = []
    const errors = []

    const lines = text.split('\n').filter(line => line.trim())

    lines.forEach((line, lineIndex) => {
        // Parse format: "Teacher Name : Subject1, Subject2, Subject3"
        const match = line.match(/^(.+?)\s*:\s*(.+)$/)

        if (!match) {
            errors.push({
                line: lineIndex + 1,
                message: `Invalid format. Expected "Teacher: Subject1, Subject2"`
            })
            return
        }

        const teacherName = normalizeTeacherName(match[1])
        const subjectsText = match[2]

        // Find or create teacher
        let teacher = teachers.find(t => t.name.toLowerCase() === teacherName.toLowerCase())
        if (!teacher) {
            teacher = {
                id: generateId(),
                name: teacherName,
                maxLecturesPerDay: 6,
                subjects: []
            }
            teachers.push(teacher)
        }

        // Parse subjects
        const subjectNames = subjectsText.split(',').map(s => normalizeSubjectName(s.trim())).filter(s => s)

        subjectNames.forEach(subjectName => {
            // Try to find existing subject
            let subject = subjects.find(s => s.name.toLowerCase() === subjectName.toLowerCase())

            if (!subject) {
                // Create new subject (default to first academic year)
                subject = {
                    id: generateId(),
                    name: subjectName,
                    year: academicYears[0] || 'SE',
                    weeklyLectures: 4,
                    isPractical: false
                }
                subjects.push(subject)
            }

            // Create mapping if not exists
            if (!mapping.find(m => m.teacherId === teacher.id && m.subjectId === subject.id)) {
                mapping.push({
                    teacherId: teacher.id,
                    subjectId: subject.id
                })
            }
        })
    })

    return {
        teachers,
        subjects,
        teacherSubjectMap: mapping,
        errors
    }
}

/**
 * Parse natural language prompt
 */
export function parseNaturalLanguage(prompt) {
    const teachers = []
    const subjects = []
    const mapping = []
    const metadata = {
        defaultWeeklyLectures: 4
    }

    // Extract teacher mentions
    const teacherPattern = /(\w+)\s+teaches?\s+([^.]+)/gi
    let match

    while ((match = teacherPattern.exec(prompt)) !== null) {
        const teacherName = normalizeTeacherName(match[1])
        const subjectsText = match[2]

        // Find or create teacher
        let teacher = teachers.find(t => t.name.toLowerCase() === teacherName.toLowerCase())
        if (!teacher) {
            teacher = {
                id: generateId(),
                name: teacherName,
                maxLecturesPerDay: 6,
                subjects: []
            }
            teachers.push(teacher)
        }

        // Extract subjects from the text
        const subjectNames = extractSubjectsFromText(subjectsText)

        subjectNames.forEach(subjectName => {
            // Find or create subject
            let subject = subjects.find(s => s.name.toLowerCase() === subjectName.toLowerCase())

            if (!subject) {
                subject = {
                    id: generateId(),
                    name: subjectName,
                    year: 'SE', // Default year
                    weeklyLectures: metadata.defaultWeeklyLectures,
                    isPractical: false
                }
                subjects.push(subject)
            }

            // Create mapping
            if (!mapping.find(m => m.teacherId === teacher.id && m.subjectId === subject.id)) {
                mapping.push({
                    teacherId: teacher.id,
                    subjectId: subject.id
                })
            }
        })
    }

    // Extract lecture count if mentioned
    const lecturePattern = /(\d+)\s+lectures?\s+(?:per\s+)?week/i
    const lectureMatch = prompt.match(lecturePattern)
    if (lectureMatch) {
        const count = parseInt(lectureMatch[1])
        metadata.defaultWeeklyLectures = count

        // Update all subjects
        subjects.forEach(subject => {
            subject.weeklyLectures = count
        })
    }

    // Extract number of teachers if mentioned
    const teacherCountPattern = /(\d+)\s+teachers?/i
    const teacherCountMatch = prompt.match(teacherCountPattern)
    if (teacherCountMatch) {
        metadata.expectedTeacherCount = parseInt(teacherCountMatch[1])
    }

    return {
        teachers,
        subjects,
        teacherSubjectMap: mapping,
        metadata,
        needsClarification: teachers.length === 0 && subjects.length === 0
    }
}

/**
 * Extract subject names from text
 */
function extractSubjectsFromText(text) {
    // Split by common delimiters: comma, 'and', '&'
    const parts = text.split(/,|\s+and\s+|\s+\&\s+/i)

    return parts
        .map(part => {
            // Remove trailing periods and clean up
            return part.trim().replace(/\.$/, '')
        })
        .filter(part => part.length > 0)
        .map(normalizeSubjectName)
}

/**
 * Merge data from multiple input sources
 */
export function mergeData(existingData, newData) {
    const merged = {
        teachers: [...existingData.teachers],
        subjects: [...existingData.subjects],
        teacherSubjectMap: [...existingData.teacherSubjectMap],
        metadata: { ...existingData.metadata, ...newData.metadata }
    }

    // Merge teachers (avoid duplicates by name)
    newData.teachers?.forEach(newTeacher => {
        const exists = merged.teachers.find(
            t => t.name.toLowerCase() === newTeacher.name.toLowerCase()
        )
        if (!exists) {
            merged.teachers.push(newTeacher)
        }
    })

    // Merge subjects (avoid duplicates by name + year)
    newData.subjects?.forEach(newSubject => {
        const exists = merged.subjects.find(
            s => s.name.toLowerCase() === newSubject.name.toLowerCase() && s.year === newSubject.year
        )
        if (!exists) {
            merged.subjects.push(newSubject)
        }
    })

    // Merge mappings (avoid duplicates)
    newData.teacherSubjectMap?.forEach(newMap => {
        const exists = merged.teacherSubjectMap.find(
            m => m.teacherId === newMap.teacherId && m.subjectId === newMap.subjectId
        )
        if (!exists) {
            merged.teacherSubjectMap.push(newMap)
        }
    })

    return merged
}

/**
 * Create CSV template content
 */
export function createCSVTemplate(type) {
    switch (type) {
        case 'teachers':
            return 'teacher_name,max_lectures_per_day\nAjay,4\nNeha,3\nRamesh,5'

        case 'subjects':
            return 'subject_name,year,weekly_lectures,type\nMathematics,SE,4,Theory\nAI,TE,3,Theory\nML Lab,TE,2,Lab'

        case 'teacher_subject_map':
            return 'teacher_name,subject_name\nAjay,Mathematics\nAjay,AI\nNeha,ML Lab'

        default:
            return ''
    }
}

export default {
    parseCSV,
    parseBulkText,
    parseNaturalLanguage,
    mergeData,
    createCSVTemplate,
    generateId
}
