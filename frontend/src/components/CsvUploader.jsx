import React, { useState, useRef } from 'react'
import { parseFile, createCSVTemplate } from '../utils/dataParser'
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
        const isExcel = file.name.toLowerCase().endsWith('.xlsx') || file.name.toLowerCase().endsWith('.xls')
        const isCsv = file.name.toLowerCase().endsWith('.csv')

        if (!isExcel && !isCsv) {
            alert('Please upload a CSV or Excel file')
            return
        }

        setParsing(true)
        setParseErrors([])

        try {
            // Pass file directly to parseFile which handles both CSV and Excel
            const result = await parseFile(file, uploadType)

            setPreviewData(result.data)
            setParseErrors(result.errors)

            if (result.errors.length === 0) {
                // Auto-confirm good data
                onDataParsed(result.data, uploadType)
                if (onFileUpload) onFileUpload(uploadType, file)
            }
        } catch (error) {
            console.error('File parse error:', error)
            alert('Failed to parse file. Please check the format.')
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
                    },
                    { key: 'sessionLength', label: 'Slots' }
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
                <h3>📊 Excel / CSV Upload</h3>
                <p className="csv-uploader-description">
                    Upload CSV or Excel files for fast bulk import. Download templates to get started.
                </p>
            </div>

            {/* Template Downloads */}
            <div className="template-section">
                <h4>Download Templates:</h4>
                <div className="template-buttons">
                    <button className="btn-template" onClick={() => downloadTemplate('teachers')}>📥 Teachers</button>
                    <button className="btn-template" onClick={() => downloadTemplate('subjects')}>📥 Subjects</button>
                    <button className="btn-template" onClick={() => downloadTemplate('teacher_subject_map')}>📥 Mapping</button>
                </div>
            </div>

            {/* Upload Type Selector - Cards */}
            <div className="upload-type-selector">
                <div className="upload-cards-grid">
                    {/* Teachers Card */}
                    <div
                        className={`upload-card ${uploadType === 'teachers' ? 'active' : ''} ${uploadedFiles.teachers ? 'completed' : ''}`}
                        onClick={() => {
                            setUploadType('teachers')
                            document.querySelector('.upload-zone')?.scrollIntoView({ behavior: 'smooth', block: 'center' })
                        }}
                    >
                        <div className="card-icon">👨‍🏫</div>
                        <div className="card-content">
                            <h4>Teachers</h4>
                            <p>Upload teachers file</p>
                        </div>
                        {uploadedFiles.teachers && <div className="card-badge">✔ Uploaded</div>}
                        {uploadedFiles.teachers && (
                            <button
                                className="ctx-reupload"
                                onClick={(e) => {
                                    e.stopPropagation()
                                    setUploadType('teachers')
                                    onFileRemove('teachers')
                                }}
                            >
                                ↺ Re-upload
                            </button>
                        )}
                    </div>

                    {/* Subjects Card */}
                    <div
                        className={`upload-card ${uploadType === 'subjects' ? 'active' : ''} ${uploadedFiles.subjects ? 'completed' : ''}`}
                        onClick={() => {
                            setUploadType('subjects')
                            document.querySelector('.upload-zone')?.scrollIntoView({ behavior: 'smooth', block: 'center' })
                        }}
                    >
                        <div className="card-icon">📘</div>
                        <div className="card-content">
                            <h4>Subjects</h4>
                            <p>Theory & Labs</p>
                        </div>
                        {uploadedFiles.subjects && <div className="card-badge">✔ Uploaded</div>}
                        {uploadedFiles.subjects && (
                            <button
                                className="ctx-reupload"
                                onClick={(e) => {
                                    e.stopPropagation()
                                    setUploadType('subjects')
                                    onFileRemove('subjects')
                                }}
                            >
                                ↺ Re-upload
                            </button>
                        )}
                    </div>

                    {/* Mapping Card */}
                    <div
                        className={`upload-card ${uploadType === 'teacher_subject_map' ? 'active' : ''} ${uploadedFiles.teacher_subject_map ? 'completed' : ''}`}
                        onClick={() => {
                            setUploadType('teacher_subject_map')
                            document.querySelector('.upload-zone')?.scrollIntoView({ behavior: 'smooth', block: 'center' })
                        }}
                    >
                        <div className="card-icon">🔗</div>
                        <div className="card-content">
                            <h4>Mapping</h4>
                            <p>Teacher ↔ Subject</p>
                        </div>
                        {uploadedFiles.teacher_subject_map && <div className="card-badge">✔ Uploaded</div>}
                        {uploadedFiles.teacher_subject_map && (
                            <button
                                className="ctx-reupload"
                                onClick={(e) => {
                                    e.stopPropagation()
                                    setUploadType('teacher_subject_map')
                                    onFileRemove('teacher_subject_map')
                                }}
                            >
                                ↺ Re-upload
                            </button>
                        )}
                    </div>




                </div>
            </div>

            {/* Upload Zone or File Status */}
            {isCurrentTypeUploaded ? (
                <div className="file-uploaded-state">
                    <div className="file-info">
                        <span className="file-icon">📄</span>
                        <div>
                            <h4>{uploadType.replace(/_/g, ' ').toUpperCase()} Uploaded</h4>
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
                        accept=".csv,.xlsx,.xls"
                        onChange={handleChange}
                        style={{ display: 'none' }}
                        disabled={isLocked}
                    />

                    <div className="upload-zone-content">
                        <div className="upload-icon">📁</div>
                        <p className="upload-text">
                            {isLocked ? 'Input Locked' : (parsing ? 'Parsing File...' : `Drag & Drop ${uploadType.replace(/_/g, ' ')} File`)}
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
