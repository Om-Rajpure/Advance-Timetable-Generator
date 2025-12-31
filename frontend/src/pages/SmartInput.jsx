import React, { lazy, Suspense, useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDashboardState } from '../hooks/useDashboardState'
import LoadingState from '../components/LoadingState'
import '../components/LoadingState.css'
import '../styles/smartInput.css'

// ✅ DYNAMIC IMPORTS - Load child components only when needed
const InputTabs = lazy(() => import('../components/InputTabs'))
const CsvUploader = lazy(() => import('../components/CsvUploader'))
const BulkTextInput = lazy(() => import('../components/BulkTextInput'))
const PromptInput = lazy(() => import('../components/PromptInput'))
const PreviewTable = lazy(() => import('../components/PreviewTable'))


function SmartInput() {
    const navigate = useNavigate()
    const { completeSmartInput } = useDashboardState()

    // ✅ SIMPLIFIED WORKFLOW GUARD - Use selectedBranch as single source of truth
    useEffect(() => {
        const selectedBranch = localStorage.getItem('selectedBranch')

        console.log('🔍 SmartInput Guard - selectedBranch:', selectedBranch ? 'EXISTS' : 'NULL')

        if (!selectedBranch) {
            console.log('❌ No branch - redirecting to Branch Setup')
            alert('⚠️ Branch Setup Required\n\nPlease complete Branch Setup before accessing Smart Input.')
            navigate('/branch-setup')
            return
        }

        console.log('✅ Branch exists - Smart Input access granted')
    }, [navigate])

    // Tab Management
    const [activeTab, setActiveTab] = useState('csv')
    const [completedTabs, setCompletedTabs] = useState({
        csv: false,
        bulk: false,
        prompt: false
    })

    // State Management for Input Lifecycle
    // Stages: 'idle' -> 'extracted' -> 'editing' -> 'confirmed' -> 'added'
    const [inputStage, setInputStage] = useState(() => {
        return localStorage.getItem('smartInputStage') || 'idle'
    })

    // Generation Loading State
    const [isGenerating, setIsGenerating] = useState(false)
    const [generationStatus, setGenerationStatus] = useState('')

    // Track uploaded files metadata
    const [uploadedFiles, setUploadedFiles] = useState(() => {
        const saved = localStorage.getItem('smartInputFiles')
        return saved ? JSON.parse(saved) : {
            teachers: null,
            subjects: null,
            mapping: null
        }
    })

    // Data State - Initialize from LocalStorage if available
    const [aggregatedData, setAggregatedData] = useState(() => {
        const saved = localStorage.getItem('smartInputData')
        return saved ? JSON.parse(saved) : {
            teachers: [],
            subjects: [],
            teacherSubjectMap: []
        }
    })

    // Persist state changes
    useEffect(() => {
        localStorage.setItem('smartInputStage', inputStage)
        localStorage.setItem('smartInputFiles', JSON.stringify(uploadedFiles))
        localStorage.setItem('smartInputData', JSON.stringify(aggregatedData))
    }, [inputStage, uploadedFiles, aggregatedData])

    // ... (imports and other setup)

    // Academic context (could be passed from parent or fetched)
    const [academicYears, setAcademicYears] = useState(['FE', 'SE', 'TE', 'BE'])

    // Tab Configuration
    const tabs = [
        { id: 'csv', label: 'File Upload', icon: '📊', completed: completedTabs.csv },
        { id: 'bulk', label: 'Bulk Text', icon: '✍️', completed: completedTabs.bulk },
        { id: 'prompt', label: 'Natural Language', icon: '🤖', completed: completedTabs.prompt }
    ]

    // Handle CSV Data Upload
    const handleCsvData = (data, uploadType) => {
        console.log('CSV Data received:', uploadType, data)

        setAggregatedData(prev => {
            // Basic merge logic
            const updated = { ...prev }

            if (uploadType === 'teachers' && data.length > 0) {
                const existingNames = new Set(prev.teachers.map(t => t.name.toLowerCase()))
                const newTeachers = data.filter(t => !existingNames.has(t.name.toLowerCase()))
                updated.teachers = [...prev.teachers, ...newTeachers]
            }
            else if (uploadType === 'subjects' && data.length > 0) {
                const existingNames = new Set(prev.subjects.map(s => s.name.toLowerCase()))
                const newSubjects = data.filter(s => !existingNames.has(s.name.toLowerCase()))
                updated.subjects = [...prev.subjects, ...newSubjects]
            }
            else if (uploadType === 'teacher_subject_map') {
                // Replace mapping significantly or append? Append is safer.
                updated.teacherSubjectMap = [...prev.teacherSubjectMap, ...data]
            }
            else if (uploadType === 'lab_mapping') {
                const existingNames = new Set(prev.labs.map(l => l.name.toLowerCase()))
                const newLabs = data.filter(l => !existingNames.has(l.name.toLowerCase()))
                updated.labs = [...(prev.labs || []), ...newLabs]
            }


            return updated
        })

        // Transition to 'extracted' if idle
        if (inputStage === 'idle') {
            setInputStage('extracted')
        }

        setCompletedTabs(prev => ({ ...prev, csv: true }))
    }

    // Handle Bulk/Prompt Data (Placeholder connections)
    const handleBulkTextData = (data) => {
        console.log('Bulk Data:', data)
        // Implementation similar to CSV merge
    }
    const handlePromptData = (data) => {
        console.log('Prompt Data:', data)
    }
    const handleDataUpdate = (type, newData) => {
        setAggregatedData(prev => ({ ...prev, [type]: newData }))
    }


    // Handle Tab Change
    const handleTabChange = (tabId) => {
        setActiveTab(tabId)
    }

    // Toggle Edit Mode
    const toggleEditMode = () => {
        if (inputStage === 'added') return // Locked

        if (inputStage === 'editing') {
            setInputStage('extracted')
        } else {
            setInputStage('editing')
        }
    }

    // Save Changes (End Edit Mode)
    const handleSaveChanges = () => {
        setInputStage('extracted')
    }

    // Confirm (Lock Data)
    const handleConfirmData = () => {
        // Validation Gate 1 & 2
        if (aggregatedData.teachers.length === 0 || aggregatedData.subjects.length === 0) {
            alert('❌ Cannot confirm empty data. Please upload Teachers and Subjects.')
            return
        }

        // Removed Strict Mapping Check for now to allow partial progress per "No hard dependency" rule
        // But warning is good.
        if (aggregatedData.teacherSubjectMap.length === 0) {
            if (!window.confirm('⚠️ No Teacher-Subject mappings found!\n\nTimetable generation requires mappings. Proceed anyway?')) {
                return
            }
        }

        setInputStage('confirmed')
        window.scrollTo({ top: 0, behavior: 'smooth' })
    }

    // Add to System (Final Commit & Generate)
    const triggerTimetableGeneration = async () => {
        setIsGenerating(true)
        setGenerationStatus('Preparing data...')

        try {
            const branchConfig = JSON.parse(localStorage.getItem('branchConfig') || '{}')

            // Payload
            const payload = {
                branchData: branchConfig,
                smartInputData: aggregatedData,
                maxIterations: 5000
            }

            setGenerationStatus('Generating initial schedule...')
            // Call API
            const response = await fetch('http://localhost:5000/api/generate/full', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })

            if (!response.ok) {
                const err = await response.json()
                throw new Error(err.error || 'Generation failed')
            }

            const result = await response.json()
            console.log('Generation Result:', result)

            if (result.success) {
                setGenerationStatus('Finalizing timetable...')
                // Save timetable to local storage or context for View Page
                localStorage.setItem('generatedTimetable', JSON.stringify(result.timetable))

                // Navigate
                completeSmartInput()
                navigate('/edit-timetable', {
                    state: {
                        timetable: result.timetable,
                        context: {
                            teachers: aggregatedData.teachers,
                            subjects: aggregatedData.subjects
                        }
                    }
                }) // Navigate to timetable view
            } else {
                alert('Generation failed: ' + result.message)
            }

        } catch (error) {
            console.error('Generation Error:', error)
            alert('Simulation failed: ' + error.message)
        } finally {
            setIsGenerating(false)
        }
    }

    const handleAddToSystem = () => {
        if (inputStage !== 'confirmed') return

        const confirmMsg = '🎯 Finish & Generate?\n\nThis will lock your inputs and attempt to generate the timetable.'

        if (window.confirm(confirmMsg)) {
            setInputStage('added')
            triggerTimetableGeneration()
        }
    }

    // Edit Again (from Confirmed state)
    const handleEditAgain = () => {
        setInputStage('editing')
    }

    const handleFileRemove = (type) => {
        if (inputStage === 'added') return

        if (window.confirm(`🗑 Remove ${type} data?`)) {
            setUploadedFiles(prev => ({ ...prev, [type]: null }))
            setAggregatedData(prev => {
                const updated = { ...prev }
                if (type === 'teachers') { updated.teachers = []; } // Don't clear mappings aggressively
                else if (type === 'subjects') { updated.subjects = []; }
                else if (type === 'mapping') { updated.teacherSubjectMap = []; }
                return updated
            })
        }
    }

    if (isGenerating) {
        return (
            <div className="smart-input-page">
                <LoadingState message={generationStatus} />
            </div>
        )
    }

    return (
        <div className="smart-input-page">
            <div className="smart-input-container">
                {/* Header */}
                <div className="smart-input-header">
                    <h1 className="smart-input-title">🎯 Smart Input Module</h1>
                    <p className="smart-input-subtitle">
                        Choose your preferred input method: File Upload (Excel/CSV), Bulk Text, or Prompt
                    </p>
                </div>

                {/* Suspense Wrapper - Load components dynamically */}
                <Suspense fallback={<LoadingState message="Loading Smart Input..." />}>


                    {/* Tab Navigation */}
                    <InputTabs
                        activeTab={activeTab}
                        onTabChange={handleTabChange}
                        tabs={tabs}
                    />

                    {/* Tab Content - Conditional Rendering for Optimal Lazy Loading */}
                    <div className="smart-input-content">
                        {activeTab === 'csv' && (
                            <CsvUploader
                                onDataParsed={handleCsvData}
                                existingData={aggregatedData}
                                uploadedFiles={uploadedFiles}
                                onFileRemove={handleFileRemove}
                                onFileUpload={(type, file) => setUploadedFiles(prev => ({
                                    ...prev,
                                    [type]: { name: file.name, timestamp: Date.now() }
                                }))}
                                isLocked={inputStage === 'added'}
                            />
                        )}

                        {activeTab === 'bulk' && (
                            <BulkTextInput
                                onDataParsed={handleBulkTextData}
                                existingData={aggregatedData}
                                academicYears={academicYears}
                            />
                        )}

                        {activeTab === 'prompt' && (
                            <PromptInput
                                onDataParsed={handlePromptData}
                                academicYears={academicYears}
                            />
                        )}
                    </div>

                    {/* Aggregated Data Preview & Actions */}
                    {(aggregatedData.teachers.length > 0 || aggregatedData.subjects.length > 0) && (
                        <div className="aggregated-preview">
                            <div className="preview-header">
                                <h3>
                                    📋 Aggregated Data Summary
                                    {inputStage === 'confirmed' && <span className="status-badge locked">🔒 Locked</span>}
                                    {inputStage === 'editing' && <span className="status-badge editing">✏️ Editing</span>}
                                </h3>

                                <div className="header-actions">
                                    {inputStage === 'extracted' && (
                                        <>
                                            <button
                                                className="btn-edit-toggle"
                                                onClick={toggleEditMode}
                                            >
                                                ✏️ Edit Data
                                            </button>
                                        </>
                                    )}

                                    {inputStage === 'editing' && (
                                        <>
                                            <button
                                                className="btn-cancel-edit"
                                                onClick={toggleEditMode}
                                            >
                                                ❌ Cancel Format
                                            </button>
                                            <button
                                                className="btn-save-data"
                                                onClick={handleSaveChanges}
                                            >
                                                💾 Save Changes
                                            </button>
                                        </>
                                    )}

                                    {inputStage === 'extracted' && aggregatedData.teachers.length > 0 && (
                                        <button
                                            className="btn-confirm-data"
                                            onClick={handleConfirmData}
                                        >
                                            ✅ Confirm Data
                                        </button>
                                    )}

                                    {inputStage === 'confirmed' && (
                                        <>
                                            <button
                                                className="btn-secondary"
                                                onClick={handleEditAgain}
                                            >
                                                ✏️ Edit Again
                                            </button>
                                            <button
                                                className="btn-add-system"
                                                onClick={handleAddToSystem}
                                            >
                                                🚀 Finish & Generate
                                            </button>
                                        </>
                                    )}
                                </div>
                            </div>

                            <div className="preview-stats">
                                <div className="stat-card">
                                    <span className="stat-icon">👨‍🏫</span>
                                    <span className="stat-value">{aggregatedData.teachers.length}</span>
                                    <span className="stat-label">Teachers</span>
                                </div>
                                <div className="stat-card">
                                    <span className="stat-icon">📚</span>
                                    <span className="stat-value">{aggregatedData.subjects.length}</span>
                                    <span className="stat-label">Subjects</span>
                                </div>
                                <div className="stat-card">
                                    <span className="stat-icon">🔗</span>
                                    <span className="stat-value">{aggregatedData.teacherSubjectMap.length}</span>
                                    <span className="stat-label">Mappings</span>
                                </div>

                            </div>

                            {/* Teachers Preview */}
                            {aggregatedData.teachers.length > 0 && (
                                <div className="preview-section">
                                    <PreviewTable
                                        data={aggregatedData.teachers}
                                        columns={[
                                            { key: 'name', label: 'Teacher Name', editable: true },
                                            { key: 'maxLecturesPerDay', label: 'Max Lectures/Day', editable: true, type: 'number' }
                                        ]}
                                        title="Teachers"
                                        isEditable={inputStage === 'editing'}
                                        onDataUpdate={(newData) => handleDataUpdate('teachers', newData)}
                                    />
                                </div>
                            )}

                            {/* Subjects Preview */}
                            {aggregatedData.subjects.length > 0 && (
                                <div className="preview-section">
                                    <PreviewTable
                                        data={aggregatedData.subjects}
                                        columns={[
                                            { key: 'name', label: 'Subject Name', editable: true },
                                            { key: 'year', label: 'Year', editable: true, options: ['FE', 'SE', 'TE', 'BE'] },
                                            { key: 'weeklyLectures', label: 'Weekly Lectures', editable: true, type: 'number' },
                                            {
                                                key: 'isPractical',
                                                label: 'Type',
                                                editable: true,
                                                type: 'select',
                                                options: [
                                                    { label: 'Theory', value: false },
                                                    { label: 'Practical (Lab)', value: true }
                                                ],
                                                render: (val) => val ? <span className="badge-lab">🔵 Lab</span> : <span className="badge-theory">🟢 Theory</span>
                                            },
                                            { key: 'sessionLength', label: 'Slots', editable: true, type: 'number' },
                                        ]}
                                        title="Subjects"
                                        isEditable={inputStage === 'editing'}
                                        onDataUpdate={(newData) => handleDataUpdate('subjects', newData)}
                                    />
                                </div>
                            )}



                            {/* Teacher-Subject Mappings Preview */}
                            {aggregatedData.teacherSubjectMap.length > 0 && (
                                <div className="preview-section">
                                    <PreviewTable
                                        data={aggregatedData.teacherSubjectMap}
                                        columns={[
                                            { key: 'teacherName', label: 'Teacher' },
                                            { key: 'subjectName', label: 'Subject' }
                                        ]}
                                        title="🧩 Teacher-Subject Mappings"
                                        isEditable={false} // Mappings hard to edit inline due to IDs
                                    />
                                </div>
                            )}
                        </div>
                    )}
                </Suspense>
            </div>
        </div>
    )
}

export default SmartInput
