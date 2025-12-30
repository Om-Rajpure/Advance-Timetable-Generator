import React, { useState, useRef } from 'react'
import { parseCSV, createCSVTemplate } from '../utils/dataParser'
import PreviewTable from './PreviewTable'

function CsvUploader({ onDataParsed, existingData = {}, uploadedFiles = {}, onFileRemove, onFileUpload, isLocked }) {
    const [dragActive, setDragActive] = useState(false)
    const [uploadType, setUploadType] = useState('teachers')
    const [parsing, setParsing] = useState(false)
    const [previewData, setPreviewData] = useState(null)
    const [parseErrors, setParseErrors] = useState([])
    const fileInputRef = useRef(null)

    const handleDrag = (e) => {
        if (isLocked) return
        e.preventDefault()
        e.stopPropagation()
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true)
        } else if (e.type === "dragleave") {
            setDragActive(false)
        }
    }

    const handleDrop = (e) => {
        if (isLocked) return
        e.preventDefault()
        e.stopPropagation()
        setDragActive(false)

        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleFileUpload(e.dataTransfer.files[0])
        }
    }

    const handleChange = (e) => {
        e.preventDefault()
        if (e.target.files && e.target.files[0]) {
            handleFileUpload(e.target.files[0])
        }
    }

    const handleFileUpload = async (file) => {
        if (!file.name.toLowerCase().endsWith('.csv')) {
            alert('Please upload a CSV file')
            return
        }

        setParsing(true)
        setParseErrors([])

        try {
            const text = await file.text()
            // Pass true for smart lab detection if uploading subjects
            const result = await parseCSV(text, uploadType)

            setPreviewData(result.data)
            setParseErrors(result.errors)

            if (result.errors.length === 0) {
                // Auto-confirm good data
                onDataParsed(result.data, uploadType)
                if (onFileUpload) onFileUpload(uploadType, file)
            }
        } catch (error) {
            console.error('CSV parse error:', error)
            alert('Failed to parse CSV file. Please check the format.')
        } finally {
            setParsing(false)
        }
    }

    const downloadTemplate = (type) => {
        const content = createCSVTemplate(type)
        const blob = new Blob([content], { type: 'text/csv' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${type}_template.csv`
        a.click()
        URL.revokeObjectURL(url)
    }

    const confirmData = () => {
        if (previewData) {
            onDataParsed(previewData, uploadType)
            if (onFileUpload) onFileUpload(uploadType, { name: 'Manually Uploaded' })
            setPreviewData(null)
        }
    }

    const getPreviewColumns = () => {
        switch (uploadType) {
            case 'teachers':
                return [
                    { key: 'name', label: 'Teacher Name' },
                    { key: 'maxLecturesPerDay', label: 'Max Lectures/Day' }
                ]
            case 'subjects':
                return [
                    { key: 'name', label: 'Subject Name' },
                    { key: 'year', label: 'Year' },
                    { key: 'weeklyLectures', label: 'Weekly Lectures' },
                    {
                        key: 'isPractical',
                        label: 'Type',
                        render: (val) => val ? <span className="badge-lab">🔵 Lab</span> : <span className="badge-theory">🟢 Theory</span>
                    }
                ]
            case 'teacher_subject_map':
                return [
                    { key: 'teacherName', label: 'Teacher' },
                    { key: 'subjectName', label: 'Subject' }
                ]
            default:
                return []
        }
    }

    // Check if current type is already uploaded
    const isCurrentTypeUploaded = uploadedFiles && uploadedFiles[uploadType]

    return (
        <div className="csv-uploader">
            <div className="csv-uploader-header">
                <h3>📊 CSV / Excel Upload</h3>
                <p className="csv-uploader-description">
                    Upload CSV files for fast bulk import. Download templates to get started.
                </p>
            </div>

            {/* Template Downloads */}
            <div className="template-section">
                <h4>Download CSV Templates:</h4>
                <div className="template-buttons">
                    <button className="btn-template" onClick={() => downloadTemplate('teachers')}>📥 Teachers</button>
                    <button className="btn-template" onClick={() => downloadTemplate('subjects')}>📥 Subjects</button>
                    <button className="btn-template" onClick={() => downloadTemplate('teacher_subject_map')}>📥 Mapping</button>
                </div>
            </div>

            {/* Upload Type Selector */}
            <div className="upload-type-selector">
                <label>Upload Type:</label>
                <div className="radio-group">
                    {['teachers', 'subjects', 'teacher_subject_map'].map(type => (
                        <label key={type} className={`radio-label ${uploadedFiles[type] ? 'uploaded' : ''}`}>
                            <input
                                type="radio"
                                value={type}
                                checked={uploadType === type}
                                onChange={(e) => setUploadType(e.target.value)}
                            />
                            <span>
                                {type === 'teachers' && 'Teachers'}
                                {type === 'subjects' && 'Subjects'}
                                {type === 'teacher_subject_map' && 'Mapping'}
                                {uploadedFiles[type] && ' ✅'}
                            </span>
                        </label>
                    ))}
                </div>
            </div>

            {/* Upload Zone or File Status */}
            {isCurrentTypeUploaded ? (
                <div className="file-uploaded-state">
                    <div className="file-info">
                        <span className="file-icon">📄</span>
                        <div>
                            <h4>{uploadType.toUpperCase().replace(/_/g, ' ')} Uploaded</h4>
                            <p>{uploadedFiles[uploadType].name}</p>
                        </div>
                    </div>
                    <div className="file-actions">
                        {!isLocked && (
                            <button
                                className="btn-remove-file"
                                onClick={() => onFileRemove(uploadType)}
                            >
                                🗑 Remove & Re-upload
                            </button>
                        )}
                    </div>
                </div>
            ) : (
                <div
                    className={`upload-zone ${dragActive ? 'drag-active' : ''} ${isLocked ? 'locked' : ''}`}
                    onDragEnter={handleDrag}
                    onDragLeave={handleDrag}
                    onDragOver={handleDrag}
                    onDrop={handleDrop}
                >
                    <input
                        ref={fileInputRef}
                        type="file"
                        accept=".csv"
                        onChange={handleChange}
                        style={{ display: 'none' }}
                        disabled={isLocked}
                    />

                    <div className="upload-zone-content">
                        <div className="upload-icon">📁</div>
                        <p className="upload-text">
                            {isLocked ? 'Input Locked' : (parsing ? 'Parsing CSV...' : `Drag & Drop ${uploadType} CSV`)}
                        </p>
                        {!isLocked && (
                            <button
                                className="btn-browse"
                                onClick={() => fileInputRef.current?.click()}
                                disabled={parsing}
                            >
                                Browse Files
                            </button>
                        )}
                    </div>
                </div>
            )}

            {/* Parse Errors */}
            {parseErrors.length > 0 && (
                <div className="parse-errors">
                    <h4>⚠️ Parse Errors ({parseErrors.length})</h4>
                    <ul>
                        {parseErrors.map((err, idx) => (
                            <li key={idx}>Row {err.row}: {err.message}</li>
                        ))}
                    </ul>
                </div>
            )}

            {/* Preview (Only for new uploads before confirm) */}
            {previewData && previewData.length > 0 && (
                <div className="csv-preview">
                    <PreviewTable
                        data={previewData}
                        columns={getPreviewColumns()}
                        title={`Preview: ${uploadType}`}
                    />
                    <div className="preview-actions">
                        <button className="btn-secondary" onClick={() => setPreviewData(null)}>Cancel</button>
                        <button className="btn-primary" onClick={confirmData}>✓ Confirm & Add</button>
                    </div>
                </div>
            )}
        </div>
    )
}

export default CsvUploader
