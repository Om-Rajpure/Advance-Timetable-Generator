import { useState, useEffect } from 'react'

/**
 * Custom hook to manage dashboard state
 * Currently uses localStorage for state persistence
 * Can be easily migrated to API calls + Context/Redux when backend is ready
 */
export function useDashboardState() {
    const [selectedBranch, setSelectedBranch] = useState(null)
    const [timetableStatus, setTimetableStatus] = useState('draft')
    const [hasTimetable, setHasTimetable] = useState(false)

    // Workflow completion tracking
    const [branchSetupCompleted, setBranchSetupCompleted] = useState(false)
    const [smartInputCompleted, setSmartInputCompleted] = useState(false)
    const [timetableGenerated, setTimetableGenerated] = useState(false)

    // Load state from localStorage on mount
    useEffect(() => {
        const branchData = localStorage.getItem('selectedBranch')
        const statusData = localStorage.getItem('timetableStatus')
        const hasTimetableData = localStorage.getItem('hasTimetable')

        // Load workflow completion states
        const branchSetupData = localStorage.getItem('branchSetupCompleted')
        const smartInputData = localStorage.getItem('smartInputCompleted')
        const timetableGeneratedData = localStorage.getItem('timetableGenerated')

        if (branchData) {
            try {
                setSelectedBranch(JSON.parse(branchData))
            } catch (e) {
                console.error('Failed to parse branch data:', e)
            }
        }

        if (statusData) {
            setTimetableStatus(statusData)
        }

        if (hasTimetableData) {
            setHasTimetable(hasTimetableData === 'true')
        }

        // Set workflow states
        setBranchSetupCompleted(branchSetupData === 'true')
        setSmartInputCompleted(smartInputData === 'true')
        setTimetableGenerated(timetableGeneratedData === 'true')
    }, [])

    // Helper methods
    const getBranchInfo = () => {
        if (!selectedBranch) {
            return {
                exists: false,
                name: null,
                years: null,
                divisions: null
            }
        }

        return {
            exists: true,
            name: selectedBranch.name,
            years: selectedBranch.years,
            divisions: selectedBranch.divisions
        }
    }

    const getTimetableStatus = () => {
        const statusConfig = {
            draft: {
                label: 'Draft',
                icon: '⚠️',
                color: '#F59E0B',
                description: 'No timetable has been generated yet'
            },
            generated: {
                label: 'Generated',
                icon: '✅',
                color: '#3B82F6',
                description: 'Timetable generated and ready for review'
            },
            locked: {
                label: 'Locked',
                icon: '🔒',
                color: '#10B981',
                description: 'Timetable finalized and locked for distribution'
            }
        }

        return statusConfig[timetableStatus] || statusConfig.draft
    }

    const hasActiveTimetable = () => {
        return hasTimetable
    }

    // Update methods (for future use when implementing state changes)
    const updateBranch = (branch) => {
        localStorage.setItem('selectedBranch', JSON.stringify(branch))
        setSelectedBranch(branch)
    }

    const updateTimetableStatus = (status) => {
        localStorage.setItem('timetableStatus', status)
        setTimetableStatus(status)
    }

    const updateHasTimetable = (value) => {
        localStorage.setItem('hasTimetable', String(value))
        setHasTimetable(value)
    }

    // Workflow completion methods
    const completeBranchSetup = () => {
        localStorage.setItem('branchSetupCompleted', 'true')
        setBranchSetupCompleted(true)
    }

    const completeSmartInput = () => {
        localStorage.setItem('smartInputCompleted', 'true')
        setSmartInputCompleted(true)
    }

    const completeTimetableGeneration = () => {
        localStorage.setItem('timetableGenerated', 'true')
        setTimetableGenerated(true)
    }

    // Get current workflow status
    const getWorkflowStatus = () => {
        return {
            branchSetupCompleted,
            smartInputCompleted,
            timetableGenerated,
            currentStep: branchSetupCompleted
                ? (smartInputCompleted ? (timetableGenerated ? 3 : 2) : 1)
                : 0,
            canAccessSmartInput: branchSetupCompleted,
            canAccessGenerate: branchSetupCompleted && smartInputCompleted
        }
    }

    return {
        getBranchInfo,
        getTimetableStatus,
        hasActiveTimetable,
        updateBranch,
        updateTimetableStatus,
        updateHasTimetable,
        completeBranchSetup,
        completeSmartInput,
        completeTimetableGeneration,
        getWorkflowStatus
    }
}
