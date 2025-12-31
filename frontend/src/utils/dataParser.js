/**
 * Data Parser Utilities for Smart Input Module
 * Handles parsing and normalization of data from various input sources
 */

import Papa from 'papaparse'
import * as XLSX from 'xlsx'

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
 * Parse File (CSV or Excel)
 */
export async function parseFile(file, fileType = 'teachers') {
    const isExcel = file.name.toLowerCase().endsWith('.xlsx') || file.name.toLowerCase().endsWith('.xls')

    if (isExcel) {
        return parseExcel(file, fileType)
    } else {
        const text = await file.text()
        return parseCSV(text, fileType)
    }
}

/**
 * Parse Excel File
 */
function parseExcel(file, fileType) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader()

        reader.onload = (e) => {
            try {
                const data = new Uint8Array(e.target.result)
                const workbook = XLSX.read(data, { type: 'array' })

                // Assist user by finding the best sheet
                const firstSheetName = workbook.SheetNames[0]
                const worksheet = workbook.Sheets[firstSheetName]

                // Convert to JSON
                const jsonData = XLSX.utils.sheet_to_json(worksheet, {
                    header: 0, // Auto-detect header
                    defval: '' // Default value for empty cells
                })

                // Normalize keys to lowercase with underscores
                const normalizedData = jsonData.map(row => {
                    const newRow = {}
                    Object.keys(row).forEach(key => {
                        const newKey = key.trim().toLowerCase().replace(/\s+/g, '_')
                        newRow[newKey] = row[key]
                    })
                    return newRow
                })

                const parsed = processParsedData(normalizedData, fileType)
                resolve(parsed)

            } catch (error) {
                reject(error)
            }
        }

        reader.onerror = (error) => reject(error)
        reader.readAsArrayBuffer(file)
    })
}

/**
 * Parse CSV Text
 */
function parseCSV(csvText, fileType) {
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
                    const parsed = processParsedData(results.data, fileType)
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
 * Process parsed data based on file type
 */
function processParsedData(data, fileType) {
    const processed = {
        data: [],
        errors: []
    }

    switch (fileType) {
        case 'teachers':
            data.forEach((row, index) => {
                const teacherName = row.teacher_name || row.name || row.teacher || row.full_name

                if (!teacherName) {
                    // Skip empty rows silently or log?
                    // processed.errors.push({ row: index + 1, message: 'Missing teacher name' })
                    return
                }

                const maxLectures = parseInt(row.max_lectures_per_day || row.max_lectures || row.max_load || '6')

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
                const year = row.year || row.academic_year || row.class

                if (!subjectName) {
                    return
                }

                if (!year) {
                    processed.errors.push({
                        row: index + 1,
                        message: 'Missing academic year'
                    })
                    return
                }

                const weeklyLectures = parseInt(row.weekly_lectures || row.lectures || row.hours || '4')

                // Smart Type Detection Logic
                let isPractical = false
                let sessionDuration = 2 // Default lab duration

                // 1. Check explicit 'type' column
                if (row.type) {
                    const typeVal = row.type.toLowerCase().trim()
                    if (typeVal === 'lab' || typeVal === 'practical' || typeVal === 'p') {
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

                // Parse session length (Slots)
                // Default: 2 for Labs, 1 for Theory
                // Logic: Check user input 'slots', 'duration', 'session_length'
                const userDuration = parseInt(row.slots || row.duration || row.session_length || '0')

                if (userDuration > 0) {
                    sessionDuration = userDuration
                } else {
                    sessionDuration = isPractical ? 2 : 1
                }

                processed.data.push({
                    id: generateId(),
                    name: normalizeSubjectName(subjectName),
                    year: year.toUpperCase().replace('YEAR', '').trim(), // Clean year input like 'SE Year' -> 'SE'
                    weeklyLectures: isNaN(weeklyLectures) ? 4 : weeklyLectures,
                    isPractical,
                    sessionLength: sessionDuration
                })
            })
            break

        case 'teacher_subject_map':
            processed.data = data.map(row => ({
                teacherName: normalizeTeacherName(row.teacher_name || row.teacher || ''),
                subjectName: normalizeSubjectName(row.subject_name || row.subject || '')
            })).filter(item => item.teacherName && item.subjectName)
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
                // Create new subject
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
 * Create CSV Template
 */
export function createCSVTemplate(type) {
    switch (type) {
        case 'teachers':
            return 'teacher_name,max_lectures_per_day\nAjay,4\nNeha,3\nRamesh,5'

        case 'subjects':
            return 'subject_name,year,weekly_lectures,type,slots\nMathematics,SE,4,Theory,1\nAI,TE,3,Theory,1\nML Lab,TE,2,Lab,2'

        case 'teacher_subject_map':
            return 'teacher_name,subject_name\nAjay,Mathematics\nAjay,AI\nNeha,ML Lab'

        default:
            return ''
    }
}

export default {
    parseFile,
    parseBulkText,
    parseNaturalLanguage,
    mergeData,
    createCSVTemplate,
    generateId
}
