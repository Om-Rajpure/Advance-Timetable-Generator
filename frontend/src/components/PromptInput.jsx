import React, { useState } from 'react'
import { parseNaturalLanguage } from '../utils/dataParser'
import PreviewTable from './PreviewTable'

function PromptInput({ onDataParsed, academicYears = [] }) {
    const [prompt, setPrompt] = useState('')
    const [extractedData, setExtractedData] = useState(null)
    const [processing, setProcessing] = useState(false)
    const [clarificationNeeded, setClarificationNeeded] = useState(false)

    const handleAnalyze = () => {
        if (!prompt.trim()) return

        setProcessing(true)

        // Simulate small delay for parsing
        setTimeout(() => {
            const parsed = parseNaturalLanguage(prompt)
            setExtractedData(parsed)
            setClarificationNeeded(parsed.needsClarification)
            setProcessing(false)
        }, 300)
    }

    const handleConfirm = () => {
        if (extractedData) {
            onDataParsed(extractedData)
            setPrompt('')
            setExtractedData(null)
            setClarificationNeeded(false)
        }
    }

    const examplePrompts = [
        {
            title: "Basic Setup",
            text: "We have 5 teachers. Ajay teaches Maths and AI. Neha teaches ML and Data Science. Each subject has 4 lectures per week."
        },
        {
            title: "With Practicals",
            text: "Ramesh is teaching DBMS and Computer Networks. Priya handles the ML Lab which is a practical subject. All subjects have 3 lectures weekly."
        },
        {
            title: "Multiple Teachers",
            text: "Ajay, Neha, and Ramesh are our teachers. Ajay handles Mathematics. Neha teaches AI and ML. Ramesh is responsible for DBMS."
        }
    ]

    return (
        <div className="prompt-input">
            <div className="prompt-header">
                <h3>🤖 Natural Language Input</h3>
                <p className="prompt-description">
                    Describe your academic setup in plain English. The system will extract teachers, subjects, and mappings.
                </p>
            </div>

            {/* Example Prompts */}
            <div className="example-prompts">
                <h4>Try these examples:</h4>
                <div className="example-grid">
                    {examplePrompts.map((example, idx) => (
                        <div
                            key={idx}
                            className="example-card"
                            onClick={() => setPrompt(example.text)}
                        >
                            <h5>{example.title}</h5>
                            <p>{example.text}</p>
                        </div>
                    ))}
                </div>
            </div>

            {/* Prompt Input */}
            <div className="prompt-input-section">
                <label>Describe your setup:</label>
                <textarea
                    className="prompt-textarea"
                    placeholder={`Example:\n"We have 5 teachers. Ajay teaches Maths and AI. Neha teaches ML and Data Science. Each subject has 4 lectures per week."`}
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    rows={8}
                />

                <button
                    className="btn-analyze"
                    onClick={handleAnalyze}
                    disabled={!prompt.trim() || processing}
                >
                    {processing ? 'Analyzing...' : '🔍 Analyze & Extract'}
                </button>
            </div>

            {/* Clarification Needed */}
            {clarificationNeeded && (
                <div className="clarification-box warning">
                    <div className="clarification-icon">❓</div>
                    <div className="clarification-content">
                        <h4>Need More Information</h4>
                        <p>
                            I couldn't extract enough information from your prompt.
                            Please provide more details about teachers and the subjects they teach.
                        </p>
                        <div className="clarification-tips">
                            <strong>Tips:</strong>
                            <ul>
                                <li>Mention teacher names explicitly</li>
                                <li>Use phrases like "teaches", "is teaching", "handles"</li>
                                <li>List subjects after each teacher</li>
                            </ul>
                        </div>
                    </div>
                </div>
            )}

            {/* Understood As Preview */}
            {extractedData && !clarificationNeeded && (
                <div className="understood-section">
                    <div className="understood-header">
                        <h4>✨ Understood As:</h4>
                        <p>Review the extracted data below. Make changes if needed.</p>
                    </div>

                    {/* Metadata Summary */}
                    {extractedData.metadata && (
                        <div className="metadata-summary">
                            {extractedData.metadata.defaultWeeklyLectures && (
                                <div className="metadata-item">
                                    <span className="metadata-label">Default Weekly Lectures:</span>
                                    <span className="metadata-value">{extractedData.metadata.defaultWeeklyLectures}</span>
                                </div>
                            )}
                            {extractedData.metadata.expectedTeacherCount && (
                                <div className="metadata-item">
                                    <span className="metadata-label">Expected Teachers:</span>
                                    <span className="metadata-value">{extractedData.metadata.expectedTeacherCount}</span>
                                </div>
                            )}
                        </div>
                    )}

                    {/* Teachers Table */}
                    {extractedData.teachers.length > 0 && (
                        <div className="extracted-section">
                            <h5>👨‍🏫 Teachers ({extractedData.teachers.length})</h5>
                            <PreviewTable
                                data={extractedData.teachers}
                                columns={[
                                    { key: 'name', label: 'Name' },
                                    { key: 'maxLecturesPerDay', label: 'Max Lectures/Day' }
                                ]}
                            />
                        </div>
                    )}

                    {/* Subjects Table */}
                    {extractedData.subjects.length > 0 && (
                        <div className="extracted-section">
                            <h5>📚 Subjects ({extractedData.subjects.length})</h5>
                            <PreviewTable
                                data={extractedData.subjects}
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

                    {/* Teacher-Subject Mapping */}
                    {extractedData.teacherSubjectMap.length > 0 && (
                        <div className="extracted-section">
                            <h5>🔗 Teacher-Subject Mapping ({extractedData.teacherSubjectMap.length})</h5>
                            <div className="mapping-list">
                                {extractedData.teacherSubjectMap.map((map, idx) => {
                                    const teacher = extractedData.teachers.find(t => t.id === map.teacherId)
                                    const subject = extractedData.subjects.find(s => s.id === map.subjectId)
                                    return (
                                        <div key={idx} className="mapping-item">
                                            <span className="mapping-teacher">{teacher?.name}</span>
                                            <span className="mapping-arrow">→</span>
                                            <span className="mapping-subject">{subject?.name}</span>
                                        </div>
                                    )
                                })}
                            </div>
                        </div>
                    )}

                    {/* Actions */}
                    <div className="understood-actions">
                        <button
                            className="btn-secondary"
                            onClick={() => {
                                setExtractedData(null)
                                setClarificationNeeded(false)
                            }}
                        >
                            ← Edit Prompt
                        </button>
                        <button
                            className="btn-primary"
                            onClick={handleConfirm}
                        >
                            ✓ Looks Good, Add This Data
                        </button>
                    </div>
                </div>
            )}

            {/* Tips Section */}
            <div className="prompt-tips">
                <h4>💡 Tips for Better Results:</h4>
                <ul>
                    <li>Use natural sentences like "Ajay teaches Maths and AI"</li>
                    <li>Separate multiple subjects with commas or "and"</li>
                    <li>Mention lecture counts: "4 lectures per week" or "weekly 5 classes"</li>
                    <li>Indicate practicals: "ML Lab is a practical subject"</li>
                    <li>Be specific about academic years when applicable</li>
                </ul>
            </div>
        </div>
    )
}

export default PromptInput
