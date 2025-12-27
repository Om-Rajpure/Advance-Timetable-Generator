import React, { useState, useEffect } from 'react'
import PropTypes from 'prop-types'

function StructureMapper({ rawData, detectedMapping, onMappingConfirm }) {
    const [mapping, setMapping] = useState(detectedMapping?.mapping || {})
    const [confidence, setConfidence] = useState(detectedMapping?.confidence || {})
    const columns = detectedMapping?.columns || []
    const preview = detectedMapping?.preview || []

    useEffect(() => {
        if (detectedMapping) {
            setMapping(detectedMapping.mapping)
            setConfidence(detectedMapping.confidence)
        }
    }, [detectedMapping])

    const fields = [
        { key: 'dayColumn', label: 'Day', required: true },
        { key: 'timeColumn', label: 'Time Slot', required: true },
        { key: 'subjectColumn', label: 'Subject', required: true },
        { key: 'teacherColumn', label: 'Teacher', required: false },
        { key: 'roomColumn', label: 'Room/Lab', required: false },
        { key: 'yearColumn', label: 'Year', required: false },
        { key: 'divisionColumn', label: 'Division', required: false },
        { key: 'batchColumn', label: 'Batch (Optional)', required: false }
    ]

    const handleMappingChange = (field, value) => {
        setMapping({
            ...mapping,
            [field]: value === '' ? null : value
        })
    }

    const getConfidenceLevel = (field) => {
        const score = confidence[field] || 0
        if (score >= 0.8) return 'high'
        if (score >= 0.5) return 'medium'
        return 'low'
    }

    const getConfidenceColor = (level) => {
        switch (level) {
            case 'high':
                return '#10B981'
            case 'medium':
                return '#F59E0B'
            case 'low':
                return '#EF4444'
            default:
                return '#94A3B8'
        }
    }

    const isValid = () => {
        const requiredFields = fields.filter(f => f.required).map(f => f.key)
        return requiredFields.every(field => mapping[field])
    }

    const handleConfirm = () => {
        if (isValid()) {
            onMappingConfirm(mapping)
        }
    }

    const renderPreviewRow = (row, rowIndex) => {
        return (
            <tr key={rowIndex}>
                {fields.map(field => {
                    const columnName = mapping[field.key]
                    const value = columnName ? row[columnName] : ''
                    return (
                        <td key={field.key} className="preview-cell">
                            {value || <span className="empty-cell">—</span>}
                        </td>
                    )
                })}
            </tr>
        )
    }

    return (
        <div className="structure-mapper">
            <div className="structure-mapper-header">
                <h3>📋 Map Your Timetable Structure</h3>
                <p className="mapper-description">
                    We've detected the structure of your file. Please confirm or adjust the column mappings below.
                </p>
            </div>

            <div className="mapping-grid">
                {fields.map(field => {
                    const confLevel = getConfidenceLevel(field.key)
                    const confColor = getConfidenceColor(confLevel)

                    return (
                        <div key={field.key} className="mapping-field">
                            <label className="mapping-label">
                                {field.label}
                                {field.required && <span className="required-mark">*</span>}
                            </label>

                            <div className="mapping-select-wrapper">
                                <select
                                    className="mapping-select"
                                    value={mapping[field.key] || ''}
                                    onChange={(e) => handleMappingChange(field.key, e.target.value)}
                                    style={{
                                        borderColor: mapping[field.key] ? confColor : '#D1D5DB'
                                    }}
                                >
                                    <option value="">-- Select Column --</option>
                                    {columns.map(col => (
                                        <option key={col} value={col}>
                                            {col}
                                        </option>
                                    ))}
                                </select>

                                {mapping[field.key] && (
                                    <div
                                        className="confidence-indicator"
                                        style={{ backgroundColor: confColor }}
                                        title={`Confidence: ${confLevel}`}
                                    >
                                        {confLevel === 'high' && '✓'}
                                        {confLevel === 'medium' && '~'}
                                        {confLevel === 'low' && '?'}
                                    </div>
                                )}
                            </div>

                            {!field.required && (
                                <p className="field-hint">Optional</p>
                            )}
                        </div>
                    )
                })}
            </div>

            <div className="confidence-legend">
                <span className="legend-item">
                    <span className="legend-dot" style={{ backgroundColor: '#10B981' }}></span>
                    High confidence
                </span>
                <span className="legend-item">
                    <span className="legend-dot" style={{ backgroundColor: '#F59E0B' }}></span>
                    Medium confidence
                </span>
                <span className="legend-item">
                    <span className="legend-dot" style={{ backgroundColor: '#EF4444' }}></span>
                    Low confidence or manual
                </span>
            </div>

            {preview.length > 0 && (
                <div className="mapping-preview">
                    <h4>Preview (First 5 Rows)</h4>
                    <div className="preview-table-wrapper">
                        <table className="preview-table">
                            <thead>
                                <tr>
                                    {fields.map(field => (
                                        <th key={field.key} className="preview-header">
                                            {field.label}
                                        </th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {preview.map((row, index) => renderPreviewRow(row, index))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            <div className="mapping-actions">
                {!isValid() && (
                    <p className="validation-message">
                        ⚠️ Please map all required fields (marked with *)
                    </p>
                )}

                <button
                    className="btn-primary btn-lg"
                    onClick={handleConfirm}
                    disabled={!isValid()}
                >
                    Confirm Mapping & Continue →
                </button>
            </div>
        </div>
    )
}

StructureMapper.propTypes = {
    rawData: PropTypes.array.isRequired,
    detectedMapping: PropTypes.shape({
        mapping: PropTypes.object,
        confidence: PropTypes.object,
        columns: PropTypes.arrayOf(PropTypes.string),
        preview: PropTypes.array
    }).isRequired,
    onMappingConfirm: PropTypes.func.isRequired
}

export default StructureMapper
