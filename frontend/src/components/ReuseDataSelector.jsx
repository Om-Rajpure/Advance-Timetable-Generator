import React, { useState, useEffect } from 'react'
import PreviewTable from './PreviewTable'

function ReuseDataSelector({ onDataSelected }) {
    const [previousSetups, setPreviousSetups] = useState([])
    const [loading, setLoading] = useState(true)
    const [selectedSetup, setSelectedSetup] = useState(null)
    const [reuseOptions, setReuseOptions] = useState({
        teachers: true,
        subjects: true,
        mappings: true
    })
    const [showWarning, setShowWarning] = useState(false)

    useEffect(() => {
        fetchPreviousSetups()
    }, [])

    const fetchPreviousSetups = async () => {
        setLoading(true)
        try {
            const response = await fetch('http://localhost:5000/api/smart-input/history')

            if (response.ok) {
                const data = await response.json()
                setPreviousSetups(data.history || [])
            } else {
                console.error('Failed to fetch history')
                setPreviousSetups([])
            }
        } catch (error) {
            console.error('Error fetching history:', error)
            // For development, use mock data
            setPreviousSetups([
                {
                    id: '1',
                    branchName: 'Computer Engineering',
                    createdAt: '2025-12-20T10:30:00Z',
                    teacherCount: 5,
                    subjectCount: 12,
                    data: {
                        teachers: [
                            { id: '1', name: 'Ajay', maxLecturesPerDay: 4 },
                            { id: '2', name: 'Neha', maxLecturesPerDay: 3 }
                        ],
                        subjects: [
                            { id: '1', name: 'Mathematics', year: 'SE', weeklyLectures: 4, isPractical: false },
                            { id: '2', name: 'AI', year: 'TE', weeklyLectures: 3, isPractical: false }
                        ],
                        teacherSubjectMap: [
                            { teacherId: '1', subjectId: '1' },
                            { teacherId: '2', subjectId: '2' }
                        ]
                    }
                },
                {
                    id: '2',
                    branchName: 'Information Technology',
                    createdAt: '2025-12-15T14:20:00Z',
                    teacherCount: 4,
                    subjectCount: 10,
                    data: {
                        teachers: [
                            { id: '3', name: 'Ramesh', maxLecturesPerDay: 5 },
                            { id: '4', name: 'Priya', maxLecturesPerDay: 4 }
                        ],
                        subjects: [
                            { id: '3', name: 'DBMS', year: 'TE', weeklyLectures: 4, isPractical: false },
                            { id: '4', name: 'Web Development', year: 'TE', weeklyLectures: 3, isPractical: true }
                        ],
                        teacherSubjectMap: [
                            { teacherId: '3', subjectId: '3' },
                            { teacherId: '4', subjectId: '4' }
                        ]
                    }
                }
            ])
        } finally {
            setLoading(false)
        }
    }

    const handleSelectSetup = (setup) => {
        setSelectedSetup(setup)
        setShowWarning(true)
    }

    const handleConfirmReuse = () => {
        if (!selectedSetup) return

        const reusedData = {
            teachers: reuseOptions.teachers ? selectedSetup.data.teachers : [],
            subjects: reuseOptions.subjects ? selectedSetup.data.subjects : [],
            teacherSubjectMap: reuseOptions.mappings ? selectedSetup.data.teacherSubjectMap : []
        }

        onDataSelected(reusedData)
        setSelectedSetup(null)
        setShowWarning(false)
    }

    const formatDate = (dateString) => {
        const date = new Date(dateString)
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        })
    }

    if (loading) {
        return (
            <div className="reuse-data-selector">
                <div className="loading-state">
                    <div className="spinner"></div>
                    <p>Loading previous setups...</p>
                </div>
            </div>
        )
    }

    if (previousSetups.length === 0) {
        return (
            <div className="reuse-data-selector">
                <div className="empty-state">
                    <div className="empty-icon">📂</div>
                    <h3>No Previous Setups Found</h3>
                    <p>Complete and save a smart input session first, then you can reuse that data here.</p>
                </div>
            </div>
        )
    }

    return (
        <div className="reuse-data-selector">
            <div className="reuse-header">
                <h3>🔄 Reuse Previous Data</h3>
                <p className="reuse-description">
                    Save time by reusing data from previous branch setups. You can choose to reuse teachers, subjects, or both.
                </p>
            </div>

            {!selectedSetup ? (
                /* Setup List */
                <div className="setup-list">
                    {previousSetups.map((setup) => (
                        <div
                            key={setup.id}
                            className="setup-card"
                            onClick={() => handleSelectSetup(setup)}
                        >
                            <div className="setup-card-header">
                                <h4>{setup.branchName}</h4>
                                <span className="setup-date">{formatDate(setup.createdAt)}</span>
                            </div>
                            <div className="setup-card-stats">
                                <div className="stat">
                                    <span className="stat-icon">👨‍🏫</span>
                                    <span className="stat-value">{setup.teacherCount}</span>
                                    <span className="stat-label">Teachers</span>
                                </div>
                                <div className="stat">
                                    <span className="stat-icon">📚</span>
                                    <span className="stat-value">{setup.subjectCount}</span>
                                    <span className="stat-label">Subjects</span>
                                </div>
                            </div>
                            <div className="setup-card-action">
                                <button className="btn-select">Select & Preview →</button>
                            </div>
                        </div>
                    ))}
                </div>
            ) : (
                /* Preview & Options */
                <div className="reuse-preview">
                    <div className="preview-top">
                        <button
                            className="btn-back"
                            onClick={() => {
                                setSelectedSetup(null)
                                setShowWarning(false)
                            }}
                        >
                            ← Back to List
                        </button>
                        <h4>Preview: {selectedSetup.branchName}</h4>
                    </div>

                    {/* Warning */}
                    {showWarning && (
                        <div className="reuse-warning">
                            <div className="warning-icon">⚠️</div>
                            <div className="warning-content">
                                <h5>This will overwrite current input data</h5>
                                <p>Any unsaved data you've entered will be replaced. Choose what to reuse below.</p>
                            </div>
                        </div>
                    )}

                    {/* Reuse Options */}
                    <div className="reuse-options">
                        <h5>Select what to reuse:</h5>
                        <div className="option-checkboxes">
                            <label className="checkbox-label">
                                <input
                                    type="checkbox"
                                    checked={reuseOptions.teachers}
                                    onChange={(e) => setReuseOptions({
                                        ...reuseOptions,
                                        teachers: e.target.checked
                                    })}
                                />
                                <span>Teachers ({selectedSetup.data.teachers.length})</span>
                            </label>
                            <label className="checkbox-label">
                                <input
                                    type="checkbox"
                                    checked={reuseOptions.subjects}
                                    onChange={(e) => setReuseOptions({
                                        ...reuseOptions,
                                        subjects: e.target.checked
                                    })}
                                />
                                <span>Subjects ({selectedSetup.data.subjects.length})</span>
                            </label>
                            <label className="checkbox-label">
                                <input
                                    type="checkbox"
                                    checked={reuseOptions.mappings}
                                    onChange={(e) => setReuseOptions({
                                        ...reuseOptions,
                                        mappings: e.target.checked
                                    })}
                                />
                                <span>Teacher-Subject Mappings ({selectedSetup.data.teacherSubjectMap.length})</span>
                            </label>
                        </div>
                    </div>

                    {/* Data Preview */}
                    {reuseOptions.teachers && selectedSetup.data.teachers.length > 0 && (
                        <div className="preview-section">
                            <h5>Teachers</h5>
                            <PreviewTable
                                data={selectedSetup.data.teachers}
                                columns={[
                                    { key: 'name', label: 'Name' },
                                    { key: 'maxLecturesPerDay', label: 'Max Lectures/Day' }
                                ]}
                            />
                        </div>
                    )}

                    {reuseOptions.subjects && selectedSetup.data.subjects.length > 0 && (
                        <div className="preview-section">
                            <h5>Subjects</h5>
                            <PreviewTable
                                data={selectedSetup.data.subjects}
                                columns={[
                                    { key: 'name', label: 'Name' },
                                    { key: 'year', label: 'Year' },
                                    { key: 'weeklyLectures', label: 'Weekly Lectures' },
                                    {
                                        key: 'isPractical',
                                        label: 'Practical',
                                        render: (val) => val ? '✓ Yes' : '✗ No'
                                    }
                                ]}
                            />
                        </div>
                    )}

                    {/* Actions */}
                    <div className="reuse-actions">
                        <button
                            className="btn-secondary"
                            onClick={() => {
                                setSelectedSetup(null)
                                setShowWarning(false)
                            }}
                        >
                            Cancel
                        </button>
                        <button
                            className="btn-primary"
                            onClick={handleConfirmReuse}
                            disabled={!reuseOptions.teachers && !reuseOptions.subjects && !reuseOptions.mappings}
                        >
                            ✓ Confirm & Apply
                        </button>
                    </div>
                </div>
            )}
        </div>
    )
}

export default ReuseDataSelector
