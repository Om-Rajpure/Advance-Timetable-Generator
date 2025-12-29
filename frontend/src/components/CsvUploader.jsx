import React, { useState, useRef } from 'react'
import { parseCSV, createCSVTemplate } from '../utils/dataParser'
import PreviewTable from './PreviewTable'

function CsvUploader({ onDataParsed, existingData = {} }) {
    const [dragActive, setDragActive] = useState(false)
    const [uploadType, setUploadType] = useState('teachers')
    const [parsing, setParsing] = useState(false)
    const [previewData, setPreviewData] = useState(null)
    const [parseErrors, setParseErrors] = useState([])
    const fileInputRef = useRef(null)

    const handleDrag = (e) => {
        e.preventDefault()
        e.stopPropagation()
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true)
        } else if (e.type === "dragleave") {
            setDragActive(false)
        }
    }

    const handleDrop = (e) => {
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
        if (!file.name.endsWith('.csv')) {
            alert('Please upload a CSV file')
            return
        }

        setParsing(true)
        setParseErrors([])

        try {
            const text = await file.text()
            const result = await parseCSV(text, uploadType)

            setPreviewData(result.data)
            setParseErrors(result.errors)

            if (result.errors.length === 0) {
                // Auto-confirm good data
                onDataParsed(result.data, uploadType)
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
                        label: 'Practical',
                        render: (val) => val ? '✓ Yes' : '✗ No'
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
                    <button
                        className="btn-template"
                        onClick={() => downloadTemplate('teachers')}
                    >
                        📥 Teachers Template
                    </button>
                    <button
                        className="btn-template"
                        onClick={() => downloadTemplate('subjects')}
                    >
                        📥 Subjects Template
                    </button>
                    <button
                        className="btn-template"
                        onClick={() => downloadTemplate('teacher_subject_map')}
                    >
                        📥 Mapping Template
                    </button>
                </div>
            </div>

            {/* Upload Type Selector */}
            <div className="upload-type-selector">
                <label>Upload Type:</label>
                <div className="radio-group">
                    <label className="radio-label">
                        <input
                            type="radio"
                            value="teachers"
                            checked={uploadType === 'teachers'}
                            onChange={(e) => setUploadType(e.target.value)}
                        />
                        <span>Teachers</span>
                    </label>
                    <label className="radio-label">
                        <input
                            type="radio"
                            value="subjects"
                            checked={uploadType === 'subjects'}
                            onChange={(e) => setUploadType(e.target.value)}
                        />
                        <span>Subjects</span>
                    </label>
                    <label className="radio-label">
                        <input
                            type="radio"
                            value="teacher_subject_map"
                            checked={uploadType === 'teacher_subject_map'}
                            onChange={(e) => setUploadType(e.target.value)}
                        />
                        <span>🧩 Teacher-Subject Mapping</span>
                    </label>
                </div>
            </div>

            {/* Upload Zone */}
            <div
                className={`upload-zone ${dragActive ? 'drag-active' : ''}`}
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
                />

                <div className="upload-zone-content">
                    <div className="upload-icon">📁</div>
                    <p className="upload-text">
                        {parsing ? 'Parsing CSV...' : 'Drag and drop CSV file here'}
                    </p>
                    <p className="upload-subtext">or</p>
                    <button
                        className="btn-browse"
                        onClick={() => fileInputRef.current?.click()}
                        disabled={parsing}
                    >
                        Browse Files
                    </button>
                </div>
            </div>

            {/* Parse Errors */}
            {parseErrors.length > 0 && (
                <div className="parse-errors">
                    <h4>⚠️ Parse Errors ({parseErrors.length})</h4>
                    <ul>
                        {parseErrors.map((err, idx) => (
                            <li key={idx}>
                                Row {err.row}: {err.message}
                            </li>
                        ))}
                    </ul>
                    <p className="error-note">
                        Rows with errors will be skipped. Fix the CSV file or enter data manually.
                    </p>
                </div>
            )}

            {/* Preview */}
            {previewData && previewData.length > 0 && (
                <div className="csv-preview">
                    <PreviewTable
                        data={previewData}
                        columns={getPreviewColumns()}
                        title={`Preview: ${uploadType}`}
                    />

                    <div className="preview-actions">
                        <button
                            className="btn-secondary"
                            onClick={() => setPreviewData(null)}
                        >
                            Cancel
                        </button>
                        <button
                            className="btn-primary"
                            onClick={confirmData}
                        >
                            ✓ Confirm & Add to Data
                        </button>
                    </div>
                </div>
            )}
        </div>
    )
}

export default CsvUploader
