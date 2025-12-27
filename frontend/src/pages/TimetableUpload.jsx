import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import UploadZone from '../components/UploadZone'
import PdfExtractionStatus from '../components/PdfExtractionStatus'
import StructureMapper from '../components/StructureMapper'
import TimetablePreview from '../components/TimetablePreview'
import LoadingState from '../components/LoadingState'
import { parseFile, detectStructure, parseWithMapping } from '../utils/timetableParser'
import { uploadPdfFile } from '../utils/pdfParserClient'
import { detectAllConflicts } from '../utils/conflictDetector'
import '../styles/timetableUpload.css'

function TimetableUpload() {
    const navigate = useNavigate()

    // Wizard steps: 1=Upload, 2=Mapping, 3=Processing, 4=Preview
    const [currentStep, setCurrentStep] = useState(1)
    const [loading, setLoading] = useState(false)
    const [loadingMessage, setLoadingMessage] = useState('')

    // Data state
    const [uploadedFile, setUploadedFile] = useState(null)
    const [rawData, setRawData] = useState(null)
    const [detectedMapping, setDetectedMapping] = useState(null)
    const [confirmedMapping, setConfirmedMapping] = useState(null)
    const [parsedSlots, setParsedSlots] = useState([])
    const [conflicts, setConflicts] = useState([])
    const [parseErrors, setParseErrors] = useState([])

    // PDF-specific state
    const [pdfExtractionInfo, setPdfExtractionInfo] = useState(null)
    const [isPdfExtraction, setIsPdfExtraction] = useState(false)

    // Handle file selection
    const handleFileSelect = async (file) => {
        setUploadedFile(file)
        setLoading(true)
        setLoadingMessage('Reading file...')

        // Check if file is PDF
        const isPdf = file.name.toLowerCase().endsWith('.pdf')
        setIsPdfExtraction(isPdf)

        try {
            if (isPdf) {
                // Handle PDF upload
                setLoadingMessage('Extracting PDF data...')

                const pdfResult = await uploadPdfFile(file)
                setPdfExtractionInfo(pdfResult.pdfInfo)
                setRawData(pdfResult.data)

                // Show PDF extraction status
                setLoading(false)
                setCurrentStep(1.5) // Intermediate step to show PDF status
            } else {
                // Handle CSV/Excel upload (existing logic)
                const result = await parseFile(file)
                setRawData(result.data)

                if (result.data.length === 0) {
                    alert('No data found in file. Please check the file and try again.')
                    setLoading(false)
                    return
                }

                setLoadingMessage('Detecting structure...')

                // Detect structure
                const detected = detectStructure(result.data)
                setDetectedMapping(detected)

                // Move to mapping step
                setCurrentStep(2)
                setLoading(false)
            }
        } catch (error) {
            console.error('File parsing error:', error)
            alert(`Failed to parse file: ${error.message}`)
            setLoading(false)
            setLoadingMessage('')
        }
    }

    // Handle PDF extraction status continuation
    const handlePdfContinue = () => {
        setLoading(true)
        setLoadingMessage('Detecting structure...')

        try {
            // Detect structure from PDF data
            const detected = detectStructure(rawData)
            setDetectedMapping(detected)

            // Move to mapping step
            setCurrentStep(2)
        } catch (error) {
            console.error('Structure detection error:', error)
            alert(`Failed to detect structure: ${error.message}`)
        } finally {
            setLoading(false)
            setLoadingMessage('')
        }
    }

    // Handle mapping confirmation
    const handleMappingConfirm = async (mapping) => {
        setConfirmedMapping(mapping)
        setLoading(true)
        setLoadingMessage('Parsing timetable data...')
        setCurrentStep(3)

        try {
            // Parse with confirmed mapping
            const parseResult = parseWithMapping(rawData, mapping)
            setParsedSlots(parseResult.slots)
            setParseErrors(parseResult.errors)

            setLoadingMessage('Detecting conflicts...')

            // Detect conflicts
            // TODO: Get branch data and smart input data from context/localStorage
            const conflictResult = detectAllConflicts(parseResult.slots, null, null)
            setConflicts(conflictResult.conflicts)

            // Move to preview step
            setCurrentStep(4)
        } catch (error) {
            console.error('Parsing error:', error)
            alert(`Failed to parse timetable: ${error.message}`)
            setCurrentStep(2) // Go back to mapping
        } finally {
            setLoading(false)
            setLoadingMessage('')
        }
    }

    // Handle back to mapping
    const handleBackToMapping = () => {
        setCurrentStep(2)
        setParsedSlots([])
        setConflicts([])
    }

    // Handle final confirmation
    const handleFinalConfirm = () => {
        // TODO: Save timetable data to backend or pass to constraint engine
        console.log('Confirmed timetable:', {
            slots: parsedSlots,
            conflicts,
            file: uploadedFile.name
        })

        alert(`Timetable uploaded successfully!\n${parsedSlots.length} slots parsed.\n${conflicts.length} conflicts detected.`)

        // Navigate to dashboard or next step
        navigate('/dashboard')
    }

    // Handle cancel
    const handleCancel = () => {
        if (currentStep > 1) {
            const confirmed = window.confirm('Are you sure you want to cancel? All progress will be lost.')
            if (!confirmed) return
        }
        navigate('/dashboard')
    }

    // Render step content
    const renderStepContent = () => {
        if (loading) {
            return <LoadingState message={loadingMessage} />
        }

        switch (currentStep) {
            case 1:
                return <UploadZone onFileSelect={handleFileSelect} />

            case 1.5:
                // PDF extraction status (intermediate step)
                return (
                    <PdfExtractionStatus
                        pdfInfo={pdfExtractionInfo}
                        isLoading={loading}
                        onContinue={handlePdfContinue}
                    />
                )

            case 2:
                return (
                    <StructureMapper
                        rawData={rawData}
                        detectedMapping={detectedMapping}
                        onMappingConfirm={handleMappingConfirm}
                    />
                )

            case 3:
                return <LoadingState message={loadingMessage} />

            case 4:
                return (
                    <TimetablePreview
                        slots={parsedSlots}
                        conflicts={conflicts}
                        onBack={handleBackToMapping}
                        onConfirm={handleFinalConfirm}
                    />
                )

            default:
                return null
        }
    }

    return (
        <div className="timetable-upload-page">
            {/* Header */}
            <div className="upload-header">
                <div className="container">
                    <button className="back-btn" onClick={handleCancel}>
                        ← Back to Dashboard
                    </button>
                    <h1 className="upload-title">📤 Upload Existing Timetable</h1>
                    <p className="upload-subtitle">
                        Import your existing timetable (CSV, Excel, or PDF) and let us detect conflicts automatically
                    </p>
                </div>
            </div>

            {/* Step Indicator */}
            <div className="step-indicator">
                <div className="container">
                    <div className="steps">
                        <div className={`step ${currentStep >= 1 ? 'active' : ''} ${currentStep > 1 ? 'completed' : ''}`}>
                            <div className="step-number">1</div>
                            <div className="step-label">Upload</div>
                        </div>
                        <div className="step-line"></div>
                        <div className={`step ${currentStep >= 2 ? 'active' : ''} ${currentStep > 2 ? 'completed' : ''}`}>
                            <div className="step-number">2</div>
                            <div className="step-label">Map Structure</div>
                        </div>
                        <div className="step-line"></div>
                        <div className={`step ${currentStep >= 3 ? 'active' : ''} ${currentStep > 3 ? 'completed' : ''}`}>
                            <div className="step-number">3</div>
                            <div className="step-label">Parse & Validate</div>
                        </div>
                        <div className="step-line"></div>
                        <div className={`step ${currentStep >= 4 ? 'active' : ''}`}>
                            <div className="step-number">4</div>
                            <div className="step-label">Preview & Confirm</div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <div className="upload-content">
                <div className="container">
                    {renderStepContent()}
                </div>
            </div>

            {/* Error Summary */}
            {parseErrors.length > 0 && currentStep === 4 && (
                <div className="container">
                    <div className="parse-errors-summary">
                        <h4>⚠️ Parsing Warnings ({parseErrors.length})</h4>
                        <p>Some rows couldn't be parsed and were skipped:</p>
                        <ul>
                            {parseErrors.slice(0, 5).map((err, idx) => (
                                <li key={idx}>Row {err.row}: {err.message}</li>
                            ))}
                            {parseErrors.length > 5 && (
                                <li>... and {parseErrors.length - 5} more</li>
                            )}
                        </ul>
                    </div>
                </div>
            )}
        </div>
    )
}

export default TimetableUpload
