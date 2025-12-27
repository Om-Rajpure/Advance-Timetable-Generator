/**
 * Timetable Parser Utility
 * Handles parsing of CSV and Excel timetable files into internal format
 */

import Papa from 'papaparse'
import * as XLSX from 'xlsx'

/**
 * Generate unique ID for slots
 */
function generateId() {
    return `slot-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`
}

/**
 * Normalize day names to standard format
 */
function normalizeDay(dayString) {
    if (!dayString) return null

    const normalized = dayString.trim().toLowerCase()
    const dayMap = {
        'mon': 'Monday', 'monday': 'Monday', 'm': 'Monday',
        'tue': 'Tuesday', 'tuesday': 'Tuesday', 'tu': 'Tuesday',
        'wed': 'Wednesday', 'wednesday': 'Wednesday', 'w': 'Wednesday',
        'thu': 'Thursday', 'thursday': 'Thursday', 'th': 'Thursday',
        'fri': 'Friday', 'friday': 'Friday', 'f': 'Friday',
        'sat': 'Saturday', 'saturday': 'Saturday', 's': 'Saturday',
        'sun': 'Sunday', 'sunday': 'Sunday', 'su': 'Sunday'
    }

    return dayMap[normalized] || dayString
}

/**
 * Normalize time slot to slot index (0-based)
 * Handles various formats: 9-10, 09:00-10:00, 9 AM - 10 AM, etc.
 */
function normalizeTimeSlot(timeString) {
    if (!timeString) return null

    const cleaned = timeString.trim().toLowerCase()

    // Extract start hour from various formats
    const patterns = [
        /(\d{1,2})\s*-\s*\d{1,2}/, // 9-10, 09-10
        /(\d{1,2}):(\d{2})\s*-/, // 09:00-10:00
        /(\d{1,2})\s*am|pm/, // 9 AM, 10 PM
        /(\d{1,2})/ // Just a number
    ]

    for (const pattern of patterns) {
        const match = cleaned.match(pattern)
        if (match) {
            let hour = parseInt(match[1])

            // Handle PM times
            if (cleaned.includes('pm') && hour < 12) {
                hour += 12
            }

            // Convert to slot index (assuming slots start at 9 AM)
            // Slot 0 = 9-10, Slot 1 = 10-11, etc.
            const slotIndex = hour - 9

            return slotIndex >= 0 ? slotIndex : null
        }
    }

    return null
}

/**
 * Parse file (CSV or Excel)
 */
export async function parseFile(file) {
    const fileExtension = file.name.split('.').pop().toLowerCase()

    if (fileExtension === 'csv') {
        return parseCSVFile(file)
    } else if (fileExtension === 'xlsx' || fileExtension === 'xls') {
        return parseExcelFile(file)
    } else {
        throw new Error('Unsupported file format. Please upload CSV or Excel (.xlsx) files.')
    }
}

/**
 * Parse CSV file
 */
function parseCSVFile(file) {
    return new Promise((resolve, reject) => {
        Papa.parse(file, {
            header: true,
            skipEmptyLines: true,
            complete: (results) => {
                resolve({
                    data: results.data,
                    meta: results.meta
                })
            },
            error: (error) => {
                reject(new Error(`CSV parsing failed: ${error.message}`))
            }
        })
    })
}

/**
 * Parse Excel file
 */
async function parseExcelFile(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader()

        reader.onload = (e) => {
            try {
                const data = new Uint8Array(e.target.result)
                const workbook = XLSX.read(data, { type: 'array' })

                // Use first sheet
                const sheetName = workbook.SheetNames[0]
                const worksheet = workbook.Sheets[sheetName]

                // Convert to JSON with header row
                const jsonData = XLSX.utils.sheet_to_json(worksheet, {
                    header: 1,
                    defval: ''
                })

                if (jsonData.length === 0) {
                    reject(new Error('Excel file is empty'))
                    return
                }

                // Convert array format to object format with headers
                const headers = jsonData[0]
                const rows = jsonData.slice(1).map(row => {
                    const obj = {}
                    headers.forEach((header, index) => {
                        obj[header] = row[index] || ''
                    })
                    return obj
                }).filter(row => Object.values(row).some(val => val !== ''))

                resolve({
                    data: rows,
                    meta: { fields: headers }
                })
            } catch (error) {
                reject(new Error(`Excel parsing failed: ${error.message}`))
            }
        }

        reader.onerror = () => {
            reject(new Error('Failed to read file'))
        }

        reader.readAsArrayBuffer(file)
    })
}

/**
 * Detect structure of timetable data
 * Returns suggested column mappings with confidence scores
 */
export function detectStructure(data) {
    if (!data || data.length === 0) {
        throw new Error('No data to analyze')
    }

    const columns = Object.keys(data[0])
    const mapping = {
        dayColumn: null,
        timeColumn: null,
        subjectColumn: null,
        teacherColumn: null,
        roomColumn: null,
        yearColumn: null,
        divisionColumn: null,
        batchColumn: null
    }

    const confidence = {
        dayColumn: 0,
        timeColumn: 0,
        subjectColumn: 0,
        teacherColumn: 0,
        roomColumn: 0,
        yearColumn: 0,
        divisionColumn: 0,
        batchColumn: 0
    }

    // Detect each field
    columns.forEach(col => {
        const colLower = col.toLowerCase().trim()
        const sampleValues = data.slice(0, 5).map(row => row[col]).filter(v => v)

        // Day detection
        if (colLower.includes('day')) {
            mapping.dayColumn = col
            confidence.dayColumn = 0.9
        } else if (sampleValues.some(v => normalizeDay(v))) {
            if (!mapping.dayColumn || confidence.dayColumn < 0.7) {
                mapping.dayColumn = col
                confidence.dayColumn = 0.7
            }
        }

        // Time detection
        if (colLower.includes('time') || colLower.includes('slot') || colLower.includes('period')) {
            mapping.timeColumn = col
            confidence.timeColumn = 0.9
        } else if (sampleValues.some(v => normalizeTimeSlot(v) !== null)) {
            if (!mapping.timeColumn || confidence.timeColumn < 0.7) {
                mapping.timeColumn = col
                confidence.timeColumn = 0.7
            }
        }

        // Subject detection
        if (colLower.includes('subject') || colLower.includes('course')) {
            mapping.subjectColumn = col
            confidence.subjectColumn = 0.9
        }

        // Teacher detection
        if (colLower.includes('teacher') || colLower.includes('faculty') || colLower.includes('instructor')) {
            mapping.teacherColumn = col
            confidence.teacherColumn = 0.9
        }

        // Room detection
        if (colLower.includes('room') || colLower.includes('lab') || colLower.includes('venue')) {
            mapping.roomColumn = col
            confidence.roomColumn = 0.8
        }

        // Year detection
        if (colLower.includes('year') || colLower === 'yr') {
            mapping.yearColumn = col
            confidence.yearColumn = 0.9
        } else if (sampleValues.some(v => /^(FE|SE|TE|BE)$/i.test(v))) {
            if (!mapping.yearColumn || confidence.yearColumn < 0.7) {
                mapping.yearColumn = col
                confidence.yearColumn = 0.7
            }
        }

        // Division detection
        if (colLower.includes('div') || colLower === 'section' || colLower.includes('section')) {
            mapping.divisionColumn = col
            confidence.divisionColumn = 0.9
        } else if (sampleValues.some(v => /^[A-Z]$/.test(v))) {
            if (!mapping.divisionColumn || confidence.divisionColumn < 0.6) {
                mapping.divisionColumn = col
                confidence.divisionColumn = 0.6
            }
        }

        // Batch detection (for practicals)
        if (colLower.includes('batch') || colLower.includes('group')) {
            mapping.batchColumn = col
            confidence.batchColumn = 0.8
        }
    })

    return {
        mapping,
        confidence,
        columns,
        preview: data.slice(0, 5)
    }
}

/**
 * Parse timetable data with confirmed mapping
 */
export function parseWithMapping(data, mapping) {
    const slots = []
    const errors = []
    const warnings = []

    data.forEach((row, index) => {
        try {
            // Extract fields based on mapping
            const day = mapping.dayColumn ? normalizeDay(row[mapping.dayColumn]) : null
            const timeSlot = mapping.timeColumn ? normalizeTimeSlot(row[mapping.timeColumn]) : null
            const subject = mapping.subjectColumn ? row[mapping.subjectColumn]?.trim() : null
            const teacher = mapping.teacherColumn ? row[mapping.teacherColumn]?.trim() : null
            const room = mapping.roomColumn ? row[mapping.roomColumn]?.trim() : null
            const year = mapping.yearColumn ? row[mapping.yearColumn]?.trim().toUpperCase() : null
            const division = mapping.divisionColumn ? row[mapping.divisionColumn]?.trim().toUpperCase() : null
            const batch = mapping.batchColumn ? row[mapping.batchColumn]?.trim() : null

            // Skip completely empty rows
            if (!day && !timeSlot && !subject && !teacher) {
                return
            }

            // Validate required fields
            if (!day) {
                errors.push({
                    row: index + 1,
                    message: 'Missing day',
                    data: row
                })
                return
            }

            if (timeSlot === null) {
                errors.push({
                    row: index + 1,
                    message: 'Invalid or missing time slot',
                    data: row
                })
                return
            }

            if (!subject) {
                warnings.push({
                    row: index + 1,
                    message: 'Missing subject',
                    severity: 'warning'
                })
            }

            // Determine type based on keywords
            const subjectLower = (subject || '').toLowerCase()
            const isPractical = subjectLower.includes('lab') ||
                subjectLower.includes('practical') ||
                !!batch

            // Create slot object
            const slot = {
                id: generateId(),
                day,
                slot: timeSlot,
                subject: subject || 'Unassigned',
                teacher: teacher || 'TBA',
                room: room || 'TBA',
                year: year || 'Unknown',
                division: division || 'A',
                type: isPractical ? 'Practical' : 'Lecture',
                batch: batch || null,
                rawRow: index + 1
            }

            slots.push(slot)
        } catch (error) {
            errors.push({
                row: index + 1,
                message: `Parsing error: ${error.message}`,
                data: row
            })
        }
    })

    return {
        slots,
        errors,
        warnings,
        summary: {
            total: data.length,
            parsed: slots.length,
            failed: errors.length,
            warnings: warnings.length
        }
    }
}

/**
 * Validate file before processing
 */
export function validateFile(file) {
    const errors = []

    // Check file size (max 10MB)
    const maxSize = 10 * 1024 * 1024
    if (file.size > maxSize) {
        errors.push('File size exceeds 10MB limit')
    }

    // Check file type
    const validExtensions = ['csv', 'xlsx', 'xls']
    const extension = file.name.split('.').pop().toLowerCase()
    if (!validExtensions.includes(extension)) {
        errors.push('Invalid file type. Please upload CSV or Excel files.')
    }

    return {
        isValid: errors.length === 0,
        errors
    }
}

export default {
    parseFile,
    detectStructure,
    parseWithMapping,
    validateFile,
    normalizeDay,
    normalizeTimeSlot
}
