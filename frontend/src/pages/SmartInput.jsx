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

    // Data State
    const [aggregatedData, setAggregatedData] = useState({
        teachers: [],
        subjects: [],
        teacherSubjectMap: []
    })

    // Academic context (could be passed from parent or fetched)
    const [academicYears, setAcademicYears] = useState(['FE', 'SE', 'TE', 'BE'])

    // Tab Configuration
    const tabs = [
        { id: 'csv', label: 'CSV Upload', icon: '📊', completed: completedTabs.csv },
        { id: 'bulk', label: 'Bulk Text', icon: '✍️', completed: completedTabs.bulk },
        { id: 'prompt', label: 'Natural Language', icon: '🤖', completed: completedTabs.prompt }
    ]

    // Handle CSV Data Upload
    const handleCsvData = (data, uploadType) => {
        console.log('CSV Data received:', uploadType, data)

        // Route mapping data to dedicated handler
        if (uploadType === 'teacher_subject_map') {
            handleMappingData(data)
            return
        }

        setAggregatedData(prev => {
            const updated = { ...prev }

            if (uploadType === 'teachers' && data.length > 0) {
                // Merge teachers, avoiding duplicates by name
                const existingNames = new Set(prev.teachers.map(t => t.name.toLowerCase()))
                const newTeachers = data.filter(t => !existingNames.has(t.name.toLowerCase()))
                updated.teachers = [...prev.teachers, ...newTeachers]
            }

            if (uploadType === 'subjects' && data.length > 0) {
                // Merge subjects, avoiding duplicates by name
                const existingNames = new Set(prev.subjects.map(s => s.name.toLowerCase()))
                const newSubjects = data.filter(s => !existingNames.has(s.name.toLowerCase()))
                updated.subjects = [...prev.subjects, ...newSubjects]
            }

            return updated
        })

        // Mark tab as completed
        setCompletedTabs(prev => ({ ...prev, csv: true }))
    }

    // Handle Teacher-Subject Mapping Upload
    const handleMappingData = (data) => {
        console.log('Mapping data received:', data)

        // Validate mappings against existing teachers and subjects
        const validMappings = []
        const errors = []

        data.forEach((mapping, index) => {
            const teacher = aggregatedData.teachers.find(
                t => t.name.toLowerCase() === mapping.teacherName.toLowerCase()
            )
            const subject = aggregatedData.subjects.find(
                s => s.name.toLowerCase() === mapping.subjectName.toLowerCase()
            )

            if (!teacher) {
                errors.push(`Row ${index + 1}: Teacher "${mapping.teacherName}" not found in Teachers list`)
            }
            if (!subject) {
                errors.push(`Row ${index + 1}: Subject "${mapping.subjectName}" not found in Subjects list`)
            }

            if (teacher && subject) {
                // Check for duplicate mapping
                const isDuplicate = aggregatedData.teacherSubjectMap.some(
                    m => m.teacherId === teacher.id && m.subjectId === subject.id
                )

                if (!isDuplicate) {
                    validMappings.push({
                        teacherId: teacher.id,
                        subjectId: subject.id,
                        teacherName: teacher.name,
                        subjectName: subject.name
                    })
                }
            }
        })

        if (errors.length > 0) {
            alert('❌ Mapping Validation Errors:\n\n' + errors.join('\n') +
                '\n\nPlease upload Teachers and Subjects first, then upload Mapping.')
            return
        }

        if (validMappings.length === 0) {
            alert('⚠️ No new mappings to add (all already exist)')
            return
        }

        setAggregatedData(prev => ({
            ...prev,
            teacherSubjectMap: [...prev.teacherSubjectMap, ...validMappings]
        }))

        alert(`✅ Added ${validMappings.length} teacher-subject mapping(s)`)

        // Mark tab as completed
        setCompletedTabs(prev => ({ ...prev, csv: true }))
    }

    // Handle Bulk Text Data
    const handleBulkTextData = (parsedData) => {
        console.log('Bulk Text Data received:', parsedData)

        setAggregatedData(prev => {
            const updated = { ...prev }

            // Merge teachers
            if (parsedData.teachers && parsedData.teachers.length > 0) {
                const existingNames = new Set(prev.teachers.map(t => t.name.toLowerCase()))
                const newTeachers = parsedData.teachers.filter(t => !existingNames.has(t.name.toLowerCase()))
                updated.teachers = [...prev.teachers, ...newTeachers]
            }

            // Merge subjects
            if (parsedData.subjects && parsedData.subjects.length > 0) {
                const existingNames = new Set(prev.subjects.map(s => s.name.toLowerCase()))
                const newSubjects = parsedData.subjects.filter(s => !existingNames.has(s.name.toLowerCase()))
                updated.subjects = [...prev.subjects, ...newSubjects]
            }

            // Merge teacher-subject mappings
            if (parsedData.teacherSubjectMap && parsedData.teacherSubjectMap.length > 0) {
                updated.teacherSubjectMap = [...prev.teacherSubjectMap, ...parsedData.teacherSubjectMap]
            }

            return updated
        })

        // Mark tab as completed
        setCompletedTabs(prev => ({ ...prev, bulk: true }))
    }

    // Handle Natural Language Prompt Data
    const handlePromptData = (extractedData) => {
        console.log('Prompt Data received:', extractedData)

        setAggregatedData(prev => {
            const updated = { ...prev }

            // Merge teachers
            if (extractedData.teachers && extractedData.teachers.length > 0) {
                const existingNames = new Set(prev.teachers.map(t => t.name.toLowerCase()))
                const newTeachers = extractedData.teachers.filter(t => !existingNames.has(t.name.toLowerCase()))
                updated.teachers = [...prev.teachers, ...newTeachers]
            }

            // Merge subjects
            if (extractedData.subjects && extractedData.subjects.length > 0) {
                const existingNames = new Set(prev.subjects.map(s => s.name.toLowerCase()))
                const newSubjects = extractedData.subjects.filter(s => !existingNames.has(s.name.toLowerCase()))
                updated.subjects = [...prev.subjects, ...newSubjects]
            }

            // Merge teacher-subject mappings
            if (extractedData.teacherSubjectMap && extractedData.teacherSubjectMap.length > 0) {
                updated.teacherSubjectMap = [...prev.teacherSubjectMap, ...extractedData.teacherSubjectMap]
            }

            return updated
        })

        // Mark tab as completed
        setCompletedTabs(prev => ({ ...prev, prompt: true }))
    }

    // Handle Tab Change
    const handleTabChange = (tabId) => {
        setActiveTab(tabId)
    }

    // Save/Submit Data
    const handleSaveData = () => {
        console.log('Saving aggregated data:', aggregatedData)

        // Mark Smart Input as completed
        completeSmartInput()

        // Show success message
        alert(`✅ Smart Input Completed!\n\n${aggregatedData.teachers.length} teachers\n${aggregatedData.subjects.length} subjects\n${aggregatedData.teacherSubjectMap.length} mappings\n\nReady for timetable generation!`)

        // Navigate to dashboard (or generate-timetable when ready)
        navigate('/dashboard')
    }

    return (
        <div className="smart-input-page">
            <div className="smart-input-container">
                {/* Header */}
                <div className="smart-input-header">
                    <h1 className="smart-input-title">🎯 Smart Input Module</h1>
                    <p className="smart-input-subtitle">
                        Choose your preferred input method: CSV Upload, Bulk Text Entry, or Natural Language
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

                    {/* Aggregated Data Preview */}
                    {(aggregatedData.teachers.length > 0 || aggregatedData.subjects.length > 0) && (
                        <div className="aggregated-preview">
                            <div className="preview-header">
                                <h3>📋 Aggregated Data Summary</h3>
                                <button
                                    className="btn-save-data"
                                    onClick={handleSaveData}
                                >
                                    💾 Save All Data
                                </button>
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
                                            { key: 'name', label: 'Teacher Name' },
                                            { key: 'maxLecturesPerDay', label: 'Max Lectures/Day' }
                                        ]}
                                        title="Teachers"
                                    />
                                </div>
                            )}

                            {/* Subjects Preview */}
                            {aggregatedData.subjects.length > 0 && (
                                <div className="preview-section">
                                    <PreviewTable
                                        data={aggregatedData.subjects}
                                        columns={[
                                            { key: 'name', label: 'Subject Name' },
                                            { key: 'year', label: 'Year' },
                                            { key: 'weeklyLectures', label: 'Weekly Lectures' },
                                            {
                                                key: 'isPractical',
                                                label: 'Practical',
                                                render: (val) => val ? '✓ Yes' : '✗ No'
                                            }
                                        ]}
                                        title="Subjects"
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
