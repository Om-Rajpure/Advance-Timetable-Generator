import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import SummaryInsights from '../components/SummaryInsights'
import BottleneckAlerts from '../components/BottleneckAlerts'
import TeacherWorkloadChart from '../components/TeacherWorkloadChart'
import LabUsageHeatmap from '../components/LabUsageHeatmap'
import FreeSlotChart from '../components/FreeSlotChart'
import './Analytics.css'

function Analytics() {
    const navigate = useNavigate()
    const [analyticsData, setAnalyticsData] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        loadAnalytics()
    }, [])

    const loadAnalytics = async () => {
        setLoading(true)
        setError(null)

        try {
            // Try to load timetable data from session storage or generate sample
            const sampleTimetable = getSampleTimetable()
            const sampleBranchData = getSampleBranchData()
            const sampleSmartInput = getSampleSmartInput()

            if (!sampleTimetable || sampleTimetable.length === 0) {
                // No timetable available
                setLoading(false)
                return
            }

            // Call analytics API
            const response = await fetch('http://localhost:5000/api/analytics/full-report', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    timetable: sampleTimetable,
                    branchData: sampleBranchData,
                    smartInputData: sampleSmartInput
                })
            })

            if (!response.ok) {
                throw new Error('Failed to fetch analytics')
            }

            const data = await response.json()
            setAnalyticsData(data)
        } catch (err) {
            console.error('Analytics error:', err)
            setError(err.message)
        } finally {
            setLoading(false)
        }
    }

    const handleRefresh = () => {
        loadAnalytics()
    }

    const handleGoToGenerate = () => {
        navigate('/smart-input')
    }

    if (loading) {
        return (
            <div className="analytics-page">
                <div className="loading-container">
                    <div className="loading-spinner"></div>
                    <p>Analyzing timetable...</p>
                </div>
            </div>
        )
    }

    if (error) {
        return (
            <div className="analytics-page">
                <div className="error-container">
                    <div className="error-icon">❌</div>
                    <h3>Failed to Load Analytics</h3>
                    <p>{error}</p>
                    <button className="btn-primary" onClick={handleRefresh}>
                        Try Again
                    </button>
                </div>
            </div>
        )
    }

    if (!analyticsData) {
        return (
            <div className="analytics-page">
                <div className="no-data-container">
                    <div className="no-data-icon">📊</div>
                    <h2>No Timetable Data Available</h2>
                    <p>Please generate or upload a timetable first to view analytics and insights.</p>
                    <button onClick={handleGoToGenerate}>
                        Generate Timetable
                    </button>
                </div>
            </div>
        )
    }

    return (
        <div className="analytics-page">
            <div className="analytics-header">
                <h1>📊 Analytics & Insights</h1>
                <p>
                    Read-only analysis of your timetable quality, resource utilization, and scheduling efficiency
                </p>
                <div className="header-actions">
                    <button className="btn-primary" onClick={handleRefresh}>
                        🔄 Refresh Analytics
                    </button>
                </div>
            </div>

            <div className="analytics-content">
                <SummaryInsights summary={analyticsData.summary} />

                <BottleneckAlerts bottlenecks={analyticsData.bottlenecks} />

                <div className="analytics-grid">
                    <TeacherWorkloadChart workload={analyticsData.workload} />
                    <LabUsageHeatmap labUsage={analyticsData.labUsage} />
                </div>

                <FreeSlotChart freeSlots={analyticsData.freeSlots} />
            </div>
        </div>
    )
}

// Helper function to get sample timetable (replace with actual data loading)
function getSampleTimetable() {
    // Try to get from session storage first
    const stored = sessionStorage.getItem('currentTimetable')
    if (stored) {
        return JSON.parse(stored)
    }

    // Return sample data for demo
    return [
        { year: 'FE', division: 'A', day: 'Monday', time: '9:00-10:00', subject: 'Math', teacher: 'Dr. Sharma', room: 'R101', type: 'Lecture' },
        { year: 'FE', division: 'A', day: 'Monday', time: '10:00-11:00', subject: 'Physics', teacher: 'Prof. Patel', room: 'R102', type: 'Lecture' },
        { year: 'FE', division: 'A', day: 'Monday', time: '11:00-12:00', subject: 'Chemistry', teacher: 'Dr. Verma', room: 'R103', type: 'Lecture' },
        { year: 'FE', division: 'A', day: 'Tuesday', time: '9:00-10:00', subject: 'CS Lab', teacher: 'Prof. Kumar', lab: 'Lab-1', type: 'Practical' },
        { year: 'FE', division: 'A', day: 'Tuesday', time: '10:00-11:00', subject: 'CS Lab', teacher: 'Prof. Kumar', lab: 'Lab-1', type: 'Practical' },
        { year: 'FE', division: 'A', day: 'Wednesday', time: '9:00-10:00', subject: 'Math', teacher: 'Dr. Sharma', room: 'R101', type: 'Lecture' },
        { year: 'FE', division: 'A', day: 'Wednesday', time: '10:00-11:00', subject: 'English', teacher: 'Ms. Singh', room: 'R104', type: 'Lecture' },
        { year: 'FE', division: 'A', day: 'Thursday', time: '9:00-10:00', subject: 'Physics', teacher: 'Prof. Patel', room: 'R102', type: 'Lecture' },
        { year: 'FE', division: 'A', day: 'Thursday', time: '10:00-11:00', subject: 'Physics', teacher: 'Prof. Patel', room: 'R102', type: 'Lecture' },
        { year: 'FE', division: 'A', day: 'Thursday', time: '11:00-12:00', subject: 'Chemistry', teacher: 'Dr. Verma', room: 'R103', type: 'Lecture' },
        { year: 'FE', division: 'A', day: 'Thursday', time: '2:00-3:00', subject: 'Math', teacher: 'Dr. Sharma', room: 'R101', type: 'Lecture' },
        { year: 'FE', division: 'A', day: 'Friday', time: '9:00-10:00', subject: 'English', teacher: 'Ms. Singh', room: 'R104', type: 'Lecture' },
        { year: 'FE', division: 'B', day: 'Monday', time: '9:00-10:00', subject: 'Math', teacher: 'Dr. Sharma', room: 'R201', type: 'Lecture' },
        { year: 'FE', division: 'B', day: 'Monday', time: '10:00-11:00', subject: 'Physics', teacher: 'Prof. Patel', room: 'R202', type: 'Lecture' },
        { year: 'FE', division: 'B', day: 'Tuesday', time: '11:00-12:00', subject: 'CS Lab', teacher: 'Prof. Kumar', lab: 'Lab-2', type: 'Practical' },
    ]
}

function getSampleBranchData() {
    return {
        branchName: 'Computer Engineering',
        academicYears: ['FE', 'SE', 'TE', 'BE'],
        divisions: {
            'FE': ['A', 'B'],
            'SE': ['A', 'B'],
            'TE': ['A'],
            'BE': ['A']
        },
        workingDays: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
        timeSlots: [
            '9:00-10:00', '10:00-11:00', '11:00-12:00', '12:00-1:00',
            '1:00-2:00', '2:00-3:00', '3:00-4:00', '4:00-5:00'
        ],
        slotsPerDay: 8,
        labs: ['Lab-1', 'Lab-2', 'Lab-3'],
        rooms: ['R101', 'R102', 'R103', 'R104', 'R201', 'R202']
    }
}

function getSampleSmartInput() {
    return {
        teachers: [
            { name: 'Dr. Sharma', id: 't1' },
            { name: 'Prof. Patel', id: 't2' },
            { name: 'Dr. Verma', id: 't3' },
            { name: 'Prof. Kumar', id: 't4' },
            { name: 'Ms. Singh', id: 't5' }
        ],
        subjects: [
            { name: 'Math', id: 's1' },
            { name: 'Physics', id: 's2' },
            { name: 'Chemistry', id: 's3' },
            { name: 'CS Lab', id: 's4' },
            { name: 'English', id: 's5' }
        ]
    }
}

export default Analytics
