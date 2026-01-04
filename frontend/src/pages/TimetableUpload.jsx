import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import UploadZone from '../components/UploadZone'
import LoadingState from '../components/LoadingState'
import { parseFile, detectStructure, parseWithMapping } from '../utils/timetableParser'
import { uploadPdfFile } from '../utils/pdfParserClient'
import { detectAllConflicts } from '../utils/conflictDetector'
import '../styles/timetableUpload.css'

function TimetableUpload() {
    const navigate = useNavigate()
    const [loading, setLoading] = useState(false)
    const [loadingMessage, setLoadingMessage] = useState('')

    // Handle file selection - DIRECT FLOW
    const handleFileSelect = async (file) => {
        setLoading(true)
        setLoadingMessage('Reading timetable...')

        try {
            let dataToParse = null;

            // 1. Parse File (Internal)
            if (file.name.toLowerCase().endsWith('.pdf')) {
                setLoadingMessage('Scanning PDF...')
                const pdfResult = await uploadPdfFile(file)
                dataToParse = pdfResult.data
            } else {
                setLoadingMessage('Reading file...')
                const result = await parseFile(file)
                dataToParse = result.data
            }

            if (!dataToParse || dataToParse.length === 0) {
                throw new Error("File appears empty")
            }

            // 2. Auto-Detect Structure (Internal)
            setLoadingMessage('Analyzing structure...')
            const detectedDebug = detectStructure(dataToParse)

            // AUTO-ACCEPT best guess (High/Medium confidence)
            // We assume the detection logic is "smart enough" as requested.
            // If mapping is missing required fields, we might have issues, 
            // but for "Beginner Friendly" we try our best or fail.
            const mapping = detectedDebug.mapping

            // 3. Parse Data with Mapping (Internal)
            setLoadingMessage('Digitizing...')
            const parseResult = parseWithMapping(dataToParse, mapping)

            if (parseResult.slots.length === 0) {
                throw new Error("We couldn't understand this timetable. Please upload a clearer file.")
            }

            // 4. Initial Conflict Check (Internal)
            // We pass null for context to imply "infer from timetable"
            const conflictResult = detectAllConflicts(parseResult.slots, null, null)

            // 5. Navigate DIRECTLY to Editor
            navigate('/edit-timetable', {
                state: {
                    timetable: parseResult.slots,
                    conflicts: conflictResult.conflicts,
                    context: {
                        // Infer context from the parsed slots themselves
                        inferred: true
                    }
                }
            })

        } catch (error) {
            console.error('Upload flow error:', error)
            // User-friendly error
            alert('We couldn\'t understand this timetable. Please upload a clearer file.')
        } finally {
            setLoading(false)
        }
    }

    if (loading) {
        return (
            <div className="timetable-upload-page">
                <div className="upload-content centered">
                    <LoadingState message={loadingMessage} />
                </div>
            </div>
        )
    }

    return (
        <div className="timetable-upload-page centered-layout">
            <div className="upload-container">
                <h1 className="simple-title">Edit Existing Timetable</h1>

                <div className="upload-box-wrapper">
                    <UploadZone
                        onFileSelect={handleFileSelect}
                        accept=".csv,.xlsx,.xls,.pdf"
                    />
                    <p className="upload-instruction">
                        Upload your timetable (PDF / Excel / CSV)
                    </p>
                </div>
            </div>
        </div>
    )
}

export default TimetableUpload
