import React from 'react'
import './TeacherWorkloadChart.css'

function TeacherWorkloadChart({ workload }) {
    if (!workload || !workload.metrics) {
        return null
    }

    const { metrics, insights } = workload
    const { perTeacher, averageLectures } = metrics

    // Get max lectures for scaling
    const maxLectures = Math.max(...Object.values(perTeacher).map(t => t.totalLectures), 1)

    // Get days for heatmap
    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

    // Get intensity class based on lecture count
    const getIntensityClass = (count) => {
        if (count === 0) return 'intensity-0'
        if (count <= 2) return 'intensity-1 intensity-2'
        if (count <= 4) return 'intensity-3 intensity-4'
        if (count <= 6) return 'intensity-5 intensity-6'
        return 'intensity-7 intensity-8 intensity-9'
    }

    return (
        <div className="teacher-workload-chart">
            <h3>👨‍🏫 Teacher Workload Analysis</h3>

            <div className="chart-section">
                <div className="chart-subtitle">Total Lectures per Teacher</div>
                <div className="bar-chart">
                    {Object.entries(perTeacher).map(([teacher, data]) => {
                        const width = (data.totalLectures / maxLectures) * 100
                        return (
                            <div key={teacher} className="bar-row">
                                <div className="teacher-name" title={teacher}>
                                    {teacher}
                                </div>
                                <div className="bar-container">
                                    <div
                                        className={`bar-fill ${data.classification}`}
                                        style={{ width: `${Math.max(width, 5)}%` }}
                                    >
                                        {data.totalLectures}
                                    </div>
                                </div>
                            </div>
                        )
                    })}
                </div>
                <div style={{ marginTop: '12px', fontSize: '13px', color: '#6b7280' }}>
                    Average: {averageLectures} lectures/week
                </div>
            </div>

            <div className="chart-section">
                <div className="chart-subtitle">Daily Distribution Heatmap</div>
                <div className="heatmap">
                    <table className="heatmap-table">
                        <thead>
                            <tr>
                                <th>Teacher</th>
                                {days.map(day => (
                                    <th key={day}>{day.substring(0, 3)}</th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {Object.entries(perTeacher).map(([teacher, data]) => (
                                <tr key={teacher}>
                                    <td style={{ textAlign: 'left', fontWeight: '500' }}>
                                        {teacher}
                                    </td>
                                    {days.map(day => {
                                        const count = data.lecturesPerDay[day] || 0
                                        return (
                                            <td key={day}>
                                                <div
                                                    className={`heatmap-cell ${getIntensityClass(count)}`}
                                                    title={`${teacher} on ${day}: ${count} lectures`}
                                                >
                                                    {count || '-'}
                                                </div>
                                            </td>
                                        )
                                    })}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {insights && insights.length > 0 && (
                <div className="chart-section">
                    <div className="chart-subtitle">Insights</div>
                    <ul className="insights-list">
                        {insights.map((insight, idx) => (
                            <li key={idx}>{insight}</li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    )
}

export default TeacherWorkloadChart
