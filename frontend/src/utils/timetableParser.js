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

    const normalized = String(dayString).trim().toLowerCase()
    const dayMap = {
        'mon': 'Monday', 'monday': 'Monday', 'm': 'Monday',
        'tue': 'Tuesday', 'tuesday': 'Tuesday', 'tu': 'Tuesday',
        'wed': 'Wednesday', 'wednesday': 'Wednesday', 'w': 'Wednesday',
        'thu': 'Thursday', 'thursday': 'Thursday', 'th': 'Thursday',
        'fri': 'Friday', 'friday': 'Friday', 'f': 'Friday',
        'sat': 'Saturday', 'saturday': 'Saturday', 's': 'Saturday',
        'sun': 'Sunday', 'sunday': 'Sunday', 'su': 'Sunday'
    }

    return dayMap[normalized] || null // Return null if not a day
}

/**
 * Parse Header to Slot Index
 * Handles "Slot 1", "Period 1", "9:00-10:00"
 */
function parseHeaderToSlot(header) {
    if (!header) return null
    const text = String(header).trim().toLowerCase()

    // Case 1: Explicit "Slot N" or "Period N"
    const slotMatch = text.match(/(?:slot|period)\s*(\d+)/)
    if (slotMatch) {
        // Return 1-based index (e.g. Slot 1 -> 1)
        // Our Grid expects 1-based usually
        return parseInt(slotMatch[1])
    }

    // Case 2: Time-based "9-10"
    return normalizeTimeSlot(text)
}

/**
 * Normalize time slot string to a number index
 * 9am -> 1 (if 1-based) or based on start time. 
 * This app seems to treat 'slot' as an index ID often.
 */
function normalizeTimeSlot(timeString) {
    if (!timeString) return null

    const cleaned = String(timeString).trim().toLowerCase()

    // Extract start hour
    const patterns = [
        /(\d{1,2})\s*-\s*\d{1,2}/, // 9-10
        /(\d{1,2}):(\d{2})\s*-/, // 09:00-
        /(\d{1,2})\s*am|pm/, // 9 AM
        /(\d{1,2})/ // Just a number (fallback)
    ]

    for (const pattern of patterns) {
        const match = cleaned.match(pattern)
        if (match) {
            let hour = parseInt(match[1])

            // Handle PM
            if (cleaned.includes('pm') && hour < 12) hour += 12
            if (cleaned.includes('12') && cleaned.includes('pm')) hour = 12
            if (cleaned.includes('12') && (cleaned.includes('noon') || !cleaned.includes('am'))) hour = 12

            // If it's a small number < 8, assume it's NOT an hour but a Slot Number already
            if (hour < 7) return hour

            // Convert hour to slot index (Assuming 9am = 1, 8am = 0?)
            // Let's standardize: 9am = Slot 1.
            return (hour - 9) + 1
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
        throw new Error('Unsupported file format. Use CSV or Excel.')
    }
}

function parseCSVFile(file) {
    return new Promise((resolve, reject) => {
        Papa.parse(file, {
            header: true,
            skipEmptyLines: 'greedy', // Better for messy files
            complete: (results) => resolve({ data: results.data, meta: results.meta }),
            error: (err) => reject(new Error(`CSV Error: ${err.message}`))
        })
    })
}

async function parseExcelFile(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader()
        reader.onload = (e) => {
            try {
                const data = new Uint8Array(e.target.result)
                const workbook = XLSX.read(data, { type: 'array' })
                if (!workbook.SheetNames.length) throw new Error("Excel file empty")

                const sheet = workbook.Sheets[workbook.SheetNames[0]]
                const jsonData = XLSX.utils.sheet_to_json(sheet, { header: 1, defval: '' })

                if (jsonData.length === 0) throw new Error("Sheet empty")

                // Find header row (first non-empty row)
                let headerRowIdx = 0
                let headers = []
                for (let i = 0; i < jsonData.length; i++) {
                    if (jsonData[i].some(cell => cell && String(cell).trim().length > 0)) {
                        headerRowIdx = i
                        headers = jsonData[i]
                        break
                    }
                }

                const rows = jsonData.slice(headerRowIdx + 1).map(row => {
                    const obj = {}
                    headers.forEach((h, i) => { if (h) obj[h] = row[i] })
                    return obj
                }).filter(row => Object.keys(row).length > 0) // Remove empty object rows

                resolve({ data: rows, meta: { fields: headers } })
            } catch (err) {
                reject(err)
            }
        }
        reader.onerror = () => reject(new Error("Read failed"))
        reader.readAsArrayBuffer(file)
    })
}

/**
 * Detect structure
 */
export function detectStructure(data) {
    if (!data || data.length === 0) throw new Error('No data')

    const columns = Object.keys(data[0])

    // Default mapping
    const mapping = {
        type: 'flat',
        dayColumn: null,
        timeColumn: null,
        subjectColumn: null,
        teacherColumn: null,
        roomColumn: null,
        yearColumn: null,
        divisionColumn: null,
        batchColumn: null,
        matrixDayColumn: null,
        matrixTimeColumns: []
    }

    const confidence = { day: 0, time: 0, subject: 0 }

    // 1. Analyze Columns
    columns.forEach(col => {
        const colLower = col.toLowerCase().trim()

        // Day
        if (colLower.includes('day') || data.some(r => normalizeDay(r[col]))) {
            mapping.dayColumn = col
            confidence.day = 1
        }

        // Time / Slot
        if (colLower.includes('time') || colLower.includes('slot') || colLower.includes('period')) {
            mapping.timeColumn = col
            confidence.time = 0.8
        }

        // Subject
        if (colLower.includes('subject') || colLower.includes('course')) {
            mapping.subjectColumn = col
            confidence.subject = 1
        }

        // Teacher
        if (colLower.includes('teacher') || colLower.includes('faculty')) mapping.teacherColumn = col

        // Room
        if (colLower.includes('room') || colLower.includes('venue')) mapping.roomColumn = col

        // Year/Div
        if (colLower.includes('year') || colLower === 'yr') mapping.yearColumn = col
        if (colLower.includes('div') || colLower.includes('sect')) mapping.divisionColumn = col
    })


    // 2. CHECK FOR MATRIX STRUCTURE (Priority)
    // Criteria: Found a Day column AND multiple columns that look like Slots/Times
    let potentialDayCol = mapping.dayColumn
    const potentialTimeCols = []

    // If no explicit 'Day' column found yet, search deeper
    if (!potentialDayCol) {
        for (const col of columns) {
            const sample = data.slice(0, 10).map(r => r[col])
            if (sample.some(v => normalizeDay(v))) {
                potentialDayCol = col
                break
            }
        }
    }

    // Identify Matrix Columns (Slot 1, 9:00, etc.)
    columns.forEach(col => {
        if (col === potentialDayCol) return
        const slotIdx = parseHeaderToSlot(col)
        if (slotIdx !== null) {
            potentialTimeCols.push(col)
        }
    })

    // Decision: If we have >= 3 time-like columns and a day column/row structure, it's Matrix
    if (potentialTimeCols.length >= 3 && potentialDayCol) {
        mapping.type = 'matrix'
        mapping.matrixDayColumn = potentialDayCol
        mapping.matrixTimeColumns = potentialTimeCols
        console.log("✅ Matrix Structure Detected", { day: potentialDayCol, slots: potentialTimeCols })
    }

    return { mapping, confidence, columns }
}

/**
 * Parse parsed data content (cell text)
 */
function parseCellContent(content) {
    if (!content) return null
    const text = String(content).trim()
    if (!text) return null
    if (text === '-') return null

    // Split by newlines (common in PDF exports)
    // Format: "Subject (Batch)\nTeacher Name [Room]"
    const lines = text.split(/[\n\r]+/).map(l => l.trim()).filter(l => l)

    if (lines.length === 0) return null

    let subject = lines[0]
    let teacher = 'TBA'
    let room = 'TBA'
    let batch = null

    // Extract Batch from Subject: "Maths (B1)" or "B1: Maths"
    const batchParen = subject.match(/\(([^)]+)\)$/)
    if (batchParen) {
        batch = batchParen[1]
        subject = subject.replace(batchParen[0], '').trim()
    }
    const batchPrefix = subject.match(/^([A-Z0-9]+):\s*(.+)/)
    if (batchPrefix) {
        batch = batchPrefix[1]
        subject = batchPrefix[2]
    }

    // Line 2 often contains Teacher and Room
    if (lines.length > 1) {
        let details = lines[1] // "Mrs. Smith [C-101]"

        // Extract Room [C-101]
        const roomMatch = details.match(/\[([^\]]+)\]$/)
        if (roomMatch) {
            room = roomMatch[1]
            details = details.replace(roomMatch[0], '').trim()
        }

        if (details) teacher = details
    }
    // Fallback: If single line has multiple info "Maths (B1) - Smith"
    else {
        if (subject.includes(' - ')) {
            const parts = subject.split(' - ')
            subject = parts[0]
            teacher = parts[1]
        }
    }

    return { subject, teacher, room, batch }
}

export function parseWithMapping(data, mapping) {
    const slots = []
    const errors = []

    // --- MATRIX PARSING ---
    if (mapping.type === 'matrix') {
        let lastDay = 'Monday' // Fallback start

        data.forEach((row, idx) => {
            // Day Carry-Forward (for merged cells in Excel)
            let rawDay = row[mapping.matrixDayColumn]
            let day = normalizeDay(rawDay)

            if (day) {
                lastDay = day
            } else {
                // Heuristic: If row has data but no day, use lastDay
                // Only if previous row was same block? safest is to assume consecutive
                if (Object.values(row).some(v => v)) day = lastDay
            }

            if (!day) return

            mapping.matrixTimeColumns.forEach(col => {
                const cellVal = row[col]
                if (!cellVal) return

                const slotInfo = parseCellContent(cellVal)
                if (slotInfo) {
                    slots.push({
                        id: generateId(),
                        day: day,
                        slot: parseHeaderToSlot(col), // uses header "Slot 1" -> 1
                        subject: slotInfo.subject,
                        teacher: slotInfo.teacher,
                        room: slotInfo.room,
                        batch: slotInfo.batch,
                        type: slotInfo.batch ? 'Practical' : 'Lecture',
                        year: 'Unknown',
                        division: 'A',
                        rawRow: idx + 1
                    })
                }
            })
        })
    }
    // --- FLAT PARSING (Legacy) ---
    else {
        data.forEach((row, idx) => {
            // Re-implement flat logic cleanly
            const day = mapping.dayColumn ? normalizeDay(row[mapping.dayColumn]) : null
            const slotNum = mapping.timeColumn ? normalizeTimeSlot(row[mapping.timeColumn]) : null
            const subject = mapping.subjectColumn ? row[mapping.subjectColumn] : null

            if (day && slotNum !== null && subject) {
                slots.push({
                    id: generateId(),
                    day,
                    slot: slotNum,
                    subject: subject,
                    teacher: (mapping.teacherColumn && row[mapping.teacherColumn]) || 'TBA',
                    room: (mapping.roomColumn && row[mapping.roomColumn]) || 'TBA',
                    room: (mapping.roomColumn && row[mapping.roomColumn]) || 'TBA',
                    type: 'Lecture',
                    year: (mapping.yearColumn && row[mapping.yearColumn]) || 'Unknown',
                    division: (mapping.divisionColumn && row[mapping.divisionColumn]) || 'A'
                })
            }
        })
    }

    return {
        slots,
        summary: { parsed: slots.length },
        errors,
        warnings: []
    }
}

export function validateFile(file) {
    // ... basic check
    const errors = []
    if (file.size > 10 * 1024 * 1024) errors.push('Max sizes 10MB')
    return { isValid: errors.length === 0, errors }
}

export default { parseFile, detectStructure, parseWithMapping, validateFile, normalizeDay }
