import React, { lazy, Suspense, useState, useEffect, startTransition } from 'react'
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
import GenerationLoading from '../components/GenerationLoading'


function SmartInput() {
    const navigate = useNavigate()
    const { getBranchInfo, completeSmartInput } = useDashboardState()

    // State Management
    const [activeTab, setActiveTab] = useState('bulk') // Default to bulk for easier access
    const [aggregatedData, setAggregatedData] = useState({
        teachers: [],
        subjects: [],
        teacherSubjectMap: []
    })
    const [inputStage, setInputStage] = useState('idle') // idle, extracted, editing, confirmed, added
    const [uploadedFiles, setUploadedFiles] = useState({})

    // Generation State
    const [isGenerating, setIsGenerating] = useState(false)
    const [generationStatus, setGenerationStatus] = useState('initializing') // initializing, processing, optimizing, finalizing

    const branchInfo = getBranchInfo()
    const academicYears = branchInfo.years || ['FE', 'SE', 'TE', 'BE']

    const tabs = [
        { id: 'csv', label: 'File Upload', icon: '📂' },
        { id: 'bulk', label: 'Bulk Text', icon: '📝' },
        { id: 'prompt', label: 'AI Prompt', icon: '✨' }
    ]

    // Handlers
    const handleTabChange = (tabId) => {
        setActiveTab(tabId)
    }

    const mergeData = (newData) => {
        console.log('Merging Data:', newData)
        setAggregatedData(prev => ({
            teachers: [...prev.teachers, ...(newData.teachers || [])],
            subjects: [...prev.subjects, ...(newData.subjects || [])],
            teacherSubjectMap: [...prev.teacherSubjectMap, ...(newData.teacherSubjectMap || [])]
        }))
        if (inputStage === 'idle') {
            setInputStage('extracted')
        }
    }

    const handleCsvData = (data, type) => {
        console.log(`Handling CSV Data for ${type}:`, data)
        const keyMap = {
            'teachers': 'teachers',
            'subjects': 'subjects',
            'teacher_subject_map': 'teacherSubjectMap'
        }
        const key = keyMap[type]
        if (key) {
            mergeData({ [key]: data })
        } else {
            console.error('Unknown CSV upload type:', type)
        }
    }
    const handleBulkTextData = (data) => mergeData(data)
    const handlePromptData = (data) => mergeData(data)

    const handleFileRemove = (type) => {
        setUploadedFiles(prev => {
            const next = { ...prev }
            delete next[type]
            return next
        })
    }

    const toggleEditMode = () => {
        if (inputStage === 'editing') setInputStage('extracted')
        else setInputStage('editing')
    }

    const handleSaveChanges = () => {
        setInputStage('extracted')
    }

    const handleConfirmData = () => {
        setInputStage('confirmed')
    }

    const handleEditAgain = () => {
        setInputStage('editing')
    }

    const handleDataUpdate = (type, newData) => {
        setAggregatedData(prev => ({
            ...prev,
            [type]: newData
        }))
    }

    const handleAddToSystem = async () => {
        setIsGenerating(true)
        setGenerationStatus('initializing')

        try {
            // Simulate intialization delay for UX
            await new Promise(r => setTimeout(r, 1000))
            setGenerationStatus('processing')

            // 1. Retrieve FULL branch configuration
            const branchConfigStr = localStorage.getItem('branchConfig')
            if (!branchConfigStr) {
                throw new Error('Branch configuration missing. Please complete Branch Setup.')
            }
            const fullBranchData = JSON.parse(branchConfigStr)

            // 2. Construct Payload matching Backend Expectation
            const payload = {
                branchData: fullBranchData,
                smartInputData: {
                    teachers: aggregatedData.teachers,
                    subjects: aggregatedData.subjects,
                    teacherSubjectMap: aggregatedData.teacherSubjectMap
                }
            }

            console.log('Sending Generation Payload:', payload)

            const response = await fetch('/api/generate/full', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })

            let result;
            try {
                const text = await response.text();
                // Try parsing JSON
                try {
                    result = JSON.parse(text);
                } catch (e) {
                    // If response was not JSON (e.g. 500 HTML page)
                    throw new Error(`Invalid Backend Response: ${text.substring(0, 100)}...`);
                }
            } catch (err) {
                throw new Error('Failed to connect to backend or invalid response received.');
            }

            if (!response.ok) {
                // If backend returned 400/500, throw the parsed result (which should be our structured error)
                // or fall back to a generic error message if the structure isn't there
                throw result || new Error(`Server returned ${response.status}`);
            }
            // STRICT VALIDATION
            if (!result.timetable || !Array.isArray(result.timetable) || result.timetable.length === 0) {
                throw new Error("Backend returned success but Timetable data is missing!");
            }

            console.log('Generation Result:', result)

            if (!result.success) {
                // Handle business logic failure (feasibility etc)
                throw result // rethrow as error to catch below
            }

            setGenerationStatus('finalizing')
            await new Promise(r => setTimeout(r, 1500))

            // Save result for Timetable Page (Persistence)
            localStorage.setItem('generatedTimetable', JSON.stringify(result.timetable))
            localStorage.setItem('generationStats', JSON.stringify(result.stats || {}))

            completeSmartInput()

            // Pass data via State (Immediate) + Storage (Backup)
            navigate('/timetable', {
                state: {
                    timetable: result.timetable,
                    context: payload,
                    qualityScore: result.qualityScore
                }
            })

        } catch (error) {
            console.error('Generation Error:', error)
            const stage = error.stage || 'UNKNOWN'
            const message = error.message || 'Generation Failed'
            const details = error.details || error.error || ''

            alert(`
❌ Generation Failed

Stage: ${stage}
Reason: ${message}
Details: ${details}
            `)
            setIsGenerating(false)
        }
    }

    if (isGenerating) {
        return (
            <div className="smart-input-page">
                {/* Use the premium loading component */}
                <GenerationLoading status={generationStatus} />
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
                                isLocked={inputStage === 'added' || inputStage === 'confirmed'}
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
