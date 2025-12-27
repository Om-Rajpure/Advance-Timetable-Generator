import React, { useState, useRef } from 'react'
import PropTypes from 'prop-types'

function UploadZone({ onFileSelect, accept = '.csv,.xlsx,.xls,.pdf', maxSize = 10 * 1024 * 1024 }) {
    const [dragActive, setDragActive] = useState(false)
    const [error, setError] = useState(null)
    const fileInputRef = useRef(null)

    const handleDrag = (e) => {
        e.preventDefault()
        e.stopPropagation()
        if (e.type === 'dragenter' || e.type === 'dragover') {
            setDragActive(true)
        } else if (e.type === 'dragleave') {
            setDragActive(false)
        }
    }

    const validateFile = (file) => {
        setError(null)

        // Check file size
        if (file.size > maxSize) {
            setError(`File size exceeds ${Math.round(maxSize / 1024 / 1024)}MB limit`)
            return false
        }

        // Check file type
        const validExtensions = accept.split(',').map(ext => ext.trim().replace('.', ''))
        const fileExtension = file.name.split('.').pop().toLowerCase()

        if (!validExtensions.includes(fileExtension)) {
            setError(`Invalid file type. Please upload ${accept} files.`)
            return false
        }

        return true
    }

    const handleDrop = (e) => {
        e.preventDefault()
        e.stopPropagation()
        setDragActive(false)

        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            const file = e.dataTransfer.files[0]
            if (validateFile(file)) {
                onFileSelect(file)
            }
        }
    }

    const handleChange = (e) => {
        e.preventDefault()
        if (e.target.files && e.target.files[0]) {
            const file = e.target.files[0]
            if (validateFile(file)) {
                onFileSelect(file)
            }
        }
    }

    const handleClick = () => {
        fileInputRef.current?.click()
    }

    return (
        <div className="upload-zone-container">
            <div
                className={`upload-zone ${dragActive ? 'drag-active' : ''} ${error ? 'error' : ''}`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={handleClick}
            >
                <input
                    ref={fileInputRef}
                    type="file"
                    accept={accept}
                    onChange={handleChange}
                    style={{ display: 'none' }}
                />

                <div className="upload-zone-content">
                    <div className="upload-icon">
                        {dragActive ? '📂' : '📁'}
                    </div>
                    <h3 className="upload-title">
                        {dragActive ? 'Drop file here' : 'Upload Timetable'}
                    </h3>
                    <p className="upload-description">
                        Drag and drop your timetable file here
                    </p>
                    <p className="upload-subtext">or</p>
                    <button
                        type="button"
                        className="btn-browse"
                        onClick={(e) => {
                            e.stopPropagation()
                            handleClick()
                        }}
                    >
                        Browse Files
                    </button>
                    <p className="upload-hint">
                        Supported formats: CSV, Excel (.xlsx), PDF
                    </p>
                </div>
            </div>

            {error && (
                <div className="upload-error">
                    <span className="error-icon">⚠️</span>
                    <span className="error-message">{error}</span>
                </div>
            )}

            <div className="upload-instructions">
                <h4>📝 Instructions</h4>
                <ul>
                    <li>Upload your existing timetable in CSV, Excel, or PDF format</li>
                    <li>The system will automatically detect the structure</li>
                    <li>You can confirm or adjust the column mappings</li>
                    <li>Conflicts will be detected and highlighted</li>
                </ul>
            </div>
        </div>
    )
}

UploadZone.propTypes = {
    onFileSelect: PropTypes.func.isRequired,
    accept: PropTypes.string,
    maxSize: PropTypes.number
}

export default UploadZone
