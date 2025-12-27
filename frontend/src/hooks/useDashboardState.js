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

    // Load state from localStorage on mount
    useEffect(() => {
        const branchData = localStorage.getItem('selectedBranch')
        const statusData = localStorage.getItem('timetableStatus')
        const hasTimetableData = localStorage.getItem('hasTimetable')

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

    return {
        getBranchInfo,
        getTimetableStatus,
        hasActiveTimetable,
        updateBranch,
        updateTimetableStatus,
        updateHasTimetable
    }
}
