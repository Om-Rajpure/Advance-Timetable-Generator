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
    const [aggregatedData, setAggregatedData] = useState(() => {
        // Load from storage if available
        const saved = localStorage.getItem('smartInputData');
        return saved ? JSON.parse(saved) : {
            teachers: [],
            subjects: [],
            teacherSubjectMap: []
        };
    });

    // Auto-save effect
    useEffect(() => {
        localStorage.setItem('smartInputData', JSON.stringify(aggregatedData));
    }, [aggregatedData]);
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

    const handleUseDummyData = () => {
        // Transformations matching user's provided structure
        const raw = {
            "years": ["SE", "TE", "BE"],
            "divisions": { "SE": ["A", "B"], "TE": ["A", "B"], "BE": ["A", "B"] },
            "subjects": {
                "SE": { "theory": ["SE_T1", "SE_T2", "SE_T3", "SE_T4", "SE_T5"], "labs": ["SE_L1", "SE_L2", "SE_L3"] },
                "TE": { "theory": ["TE_T1", "TE_T2", "TE_T3", "TE_T4", "TE_T5"], "labs": ["TE_L1", "TE_L2", "TE_L3"] },
                "BE": { "theory": ["BE_T1", "BE_T2", "BE_T3", "BE_T4", "BE_T5"], "labs": ["BE_L1", "BE_L2", "BE_L3"] }
            },
            "teachers": {
                "SE_T1": "Teacher_1", "SE_T2": "Teacher_2", "SE_T3": "Teacher_3", "SE_T4": "Teacher_4", "SE_T5": "Teacher_5",
                "SE_L1": "Teacher_6", "SE_L2": "Teacher_7", "SE_L3": "Teacher_8",
                "TE_T1": "Teacher_9", "TE_T2": "Teacher_10", "TE_T3": "Teacher_11", "TE_T4": "Teacher_12", "TE_T5": "Teacher_13",
                "TE_L1": "Teacher_14", "TE_L2": "Teacher_15", "TE_L3": "Teacher_16",
                "BE_T1": "Teacher_17", "BE_T2": "Teacher_18", "BE_T3": "Teacher_19", "BE_T4": "Teacher_20", "BE_T5": "Teacher_21",
                "BE_L1": "Teacher_22", "BE_L2": "Teacher_23", "BE_L3": "Teacher_24"
            }
        };

        const teachers = Object.entries(raw.teachers).map(([id, name]) => ({ name, maxLecturesPerDay: 4 }));
        const subjects = [];
        const mapping = [];

        Object.entries(raw.subjects).forEach(([year, types]) => {
            types.theory.forEach(sub => {
                subjects.push({ name: sub, year, isPractical: false, sessionLength: 1, weeklyLectures: 3 });
                if (raw.teachers[sub]) mapping.push({ teacherName: raw.teachers[sub], subjectName: sub });
            });
            types.labs.forEach(sub => {
                subjects.push({ name: sub, year, isPractical: true, sessionLength: 2, weeklyLectures: 4 });
                if (raw.teachers[sub]) mapping.push({ teacherName: raw.teachers[sub], subjectName: sub });
            });
        });

        setAggregatedData({
            teachers,
            subjects,
            teacherSubjectMap: mapping
        });

        // Auto-configure Branch Info in LocalStorage to match
        const dummyBranch = {
            academicYears: ["SE", "TE", "BE"],
            divisions: { "SE": ["A", "B"], "TE": ["A", "B"], "BE": ["A", "B"] },
            workingDays: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            lectureDuration: 60,
            startTime: "09:00 AM",
            slotsPerDay: 6,
            labs: ["Lab_1", "Lab_2", "Lab_3"],
            rooms: ["Room_101", "Room_102", "Room_103", "Room_104"],
            classrooms: [
                { name: "Room_101", capacity: 60 },
                { name: "Room_102", capacity: 60 },
                { name: "Room_103", capacity: 60 },
                { name: "Room_104", capacity: 60 }
            ],
            sharedLabs: [
                { name: "Lab_1", capacity: 30 },
                { name: "Lab_2", capacity: 30 },
                { name: "Lab_3", capacity: 30 }
            ]
        };
        localStorage.setItem('branchConfig', JSON.stringify(dummyBranch));

        setInputStage('confirmed');
        alert("✅ Dummy Data Loaded! Click 'Finish & Generate' now.");
    };

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
            let fullBranchData = JSON.parse(branchConfigStr)

            // 🛡️ SANITIZATION: Ensure correct types to prevent 400 Bad Request
            if (fullBranchData.academicYears && typeof fullBranchData.academicYears === 'string') {
                fullBranchData.academicYears = fullBranchData.academicYears.split(',').map(y => y.trim()).filter(Boolean);
            }
            if (!Array.isArray(fullBranchData.academicYears)) {
                // Fallback if missing
                fullBranchData.academicYears = ['SE', 'TE', 'BE'];
            }

            // Ensure divisions is a Dict, not array (common legacy issue)
            if (Array.isArray(fullBranchData.divisions)) {
                console.warn("Fixing malformed divisions (array -> dict)");
                const divMap = {};
                if (fullBranchData.divisions.length > 0) {
                    // Assume identical divisions for all years if stored as list ["A", "B"]
                    fullBranchData.academicYears.forEach(y => {
                        divMap[y] = fullBranchData.divisions;
                    });
                }
                fullBranchData.divisions = divMap;
            }

            // 2. Construct Payload matching Backend Expectation
            const payload = {
                branchData: fullBranchData,
                smartInputData: {
                    teachers: aggregatedData.teachers,
                    subjects: aggregatedData.subjects,
                    teacherSubjectMap: aggregatedData.teacherSubjectMap
                }
            }

            // 3. Send to Backend
            console.log('Sending Generation Payload:', payload)

            const response = await fetch('http://localhost:5000/api/generate/full', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })

            const result = await response.json()

            if (!response.ok) {
                throw {
                    message: result.message || 'Generation failed',
                    details: result.error || result.details,
                    stage: result.stage
                }
            }

            console.log('Generation Result (MOCKED):', result)

            setGenerationStatus('finalizing')
            await new Promise(r => setTimeout(r, 500))

            // Save result for Timetable Page (Persistence)
            localStorage.setItem('generatedTimetable', JSON.stringify(result.timetables))
            localStorage.setItem('generationStats', JSON.stringify(result.stats || {}))

            completeSmartInput()

            // Pass data via State (Immediate) + Storage (Backup)
            // INCLUDE WARNINGS for Timetable Page to display
            navigate('/timetable', {
                state: {
                    timetable: result.timetables, // Keeping prop name 'timetable' for compatibility
                    context: payload, // Valid Payload context
                    qualityScore: result.qualityScore,
                    failures: result.failures || {}, // NEW: Backend failures
                    validationErrors: result.validationErrors || [] // NEW: Soft validation errors
                }
            })

            // Prevent execution of catch block by returning early if needed, 
            // but the try block should complete naturally.
            return;

        } catch (error) {
            console.error('Generation Error:', error)

            // Network Error Handling
            if (error instanceof TypeError && error.message === "Failed to fetch") {
                alert(`
❌ Backend Unreachable
The server is not responding at http://localhost:5000.

Please ensure:
1. The backend server is running (python app.py)
2. You are using the correct port (5000)
                 `)
                setIsGenerating(false)
                return
            }

            const stage = error.stage || 'UNKNOWN'
            const message = error.message || 'Generation Failed'
            const details = error.details || error.error || ''
            const division = error.division ? `Division: ${error.division}` : ''
            const reason = error.reason ? `Reason: ${error.reason}` : ''

            alert(`
❌ Generation Failed

${division}
${reason}
Stage: ${stage}
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
                    <button
                        onClick={handleUseDummyData}
                        className="btn-secondary"
                        style={{ marginTop: '15px', background: '#6366f1', color: 'white', border: 'none' }}
                    >
                        🧪 Load Verified Dummy Data (Debug)
                    </button>
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
