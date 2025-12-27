import React, { useState, useEffect } from 'react'
import { parseBulkText } from '../utils/dataParser'
import PreviewTable from './PreviewTable'

function BulkTextInput({ onDataParsed, existingData = {}, academicYears = [] }) {
    const [inputText, setInputText] = useState('')
    const [livePreview, setLivePreview] = useState(null)
    const [suggestions, setSuggestions] = useState([])
    const [cursorPosition, setCursorPosition] = useState(0)

    useEffect(() => {
        if (inputText.trim()) {
            // Parse on the fly for live preview
            const parsed = parseBulkText(inputText, academicYears)
            setLivePreview(parsed)
        } else {
            setLivePreview(null)
        }
    }, [inputText, academicYears])

    useEffect(() => {
        // Generate suggestions based on existing subjects
        if (existingData.subjects) {
            const uniqueSubjects = [...new Set(existingData.subjects.map(s => s.name))]
            setSuggestions(uniqueSubjects)
        }
    }, [existingData])

    const handleAddData = () => {
        if (livePreview) {
            onDataParsed(livePreview)
            setInputText('')
            setLivePreview(null)
        }
    }

    const handleExampleClick = (example) => {
        setInputText(example)
    }

    const exampleText = `Ajay : Mathematics, AI
Neha : Machine Learning, Data Science
Ramesh : DBMS, Operating Systems
Priya : Computer Networks`

    return (
        <div className="bulk-text-input">
            <div className="bulk-text-header">
                <h3>✍️ Bulk Text Input</h3>
                <p className="bulk-text-description">
                    Fast manual entry. Format: <code>Teacher Name : Subject1, Subject2</code>
                </p>
            </div>

            <div className="bulk-input-layout">
                {/* Input Pane */}
                <div className="input-pane">
                    <div className="input-pane-header">
                        <h4>Input</h4>
                        <button
                            className="btn-example"
                            onClick={() => handleExampleClick(exampleText)}
                        >
                            Use Example
                        </button>
                    </div>

                    <textarea
                        className="bulk-textarea"
                        placeholder={`Enter teacher-subject mappings:\nTeacher Name : Subject1, Subject2\n\nExample:\nAjay : Maths, AI\nNeha : ML, DS`}
                        value={inputText}
                        onChange={(e) => {
                            setInputText(e.target.value)
                            setCursorPosition(e.target.selectionStart)
                        }}
                        rows={15}
                    />

                    <div className="input-hints">
                        <div className="hint-item">
                            <span className="hint-icon">💡</span>
                            <span>Separate teacher and subjects with <code>:</code></span>
                        </div>
                        <div className="hint-item">
                            <span className="hint-icon">✨</span>
                            <span>Separate multiple subjects with <code>,</code></span>
                        </div>
                        <div className="hint-item">
                            <span className="hint-icon">🔄</span>
                            <span>Duplicates are automatically merged</span>
                        </div>
                    </div>

                    {suggestions.length > 0 && (
                        <div className="suggestions-box">
                            <h5>💡 Available Subjects:</h5>
                            <div className="suggestions-list">
                                {suggestions.map((subject, idx) => (
                                    <span key={idx} className="suggestion-pill">
                                        {subject}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}
                </div>

                {/* Preview Pane */}
                <div className="preview-pane">
                    <div className="preview-pane-header">
                        <h4>Live Preview</h4>
                        {livePreview && (
                            <div className="preview-stats">
                                <span>{livePreview.teachers.length} teachers</span>
                                <span>•</span>
                                <span>{livePreview.subjects.length} subjects</span>
                            </div>
                        )}
                    </div>

                    {livePreview ? (
                        <div className="preview-content">
                            {/* Teachers Preview */}
                            {livePreview.teachers.length > 0 && (
                                <div className="preview-section">
                                    <h5>Teachers ({livePreview.teachers.length})</h5>
                                    <PreviewTable
                                        data={livePreview.teachers}
                                        columns={[
                                            { key: 'name', label: 'Name' },
                                            { key: 'maxLecturesPerDay', label: 'Max Lectures/Day' }
                                        ]}
                                    />
                                </div>
                            )}

                            {/* Subjects Preview */}
                            {livePreview.subjects.length > 0 && (
                                <div className="preview-section">
                                    <h5>Subjects ({livePreview.subjects.length})</h5>
                                    <PreviewTable
                                        data={livePreview.subjects}
                                        columns={[
                                            { key: 'name', label: 'Name' },
                                            { key: 'year', label: 'Year' },
                                            { key: 'weeklyLectures', label: 'Weekly Lectures' }
                                        ]}
                                    />
                                </div>
                            )}

                            {/* Errors */}
                            {livePreview.errors.length > 0 && (
                                <div className="preview-errors">
                                    <h5>⚠️ Parse Issues</h5>
                                    <ul>
                                        {livePreview.errors.map((err, idx) => (
                                            <li key={idx}>
                                                Line {err.line}: {err.message}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                        </div>
                    ) : (
                        <div className="preview-empty">
                            <div className="empty-icon">👁️</div>
                            <p>Start typing to see live preview</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Actions */}
            {livePreview && livePreview.teachers.length > 0 && (
                <div className="bulk-actions">
                    <button
                        className="btn-secondary"
                        onClick={() => {
                            setInputText('')
                            setLivePreview(null)
                        }}
                    >
                        Clear
                    </button>
                    <button
                        className="btn-primary"
                        onClick={handleAddData}
                    >
                        ✓ Add {livePreview.teachers.length} Teacher{livePreview.teachers.length !== 1 ? 's' : ''} & {livePreview.subjects.length} Subject{livePreview.subjects.length !== 1 ? 's' : ''}
                    </button>
                </div>
            )}
        </div>
    )
}

export default BulkTextInput
