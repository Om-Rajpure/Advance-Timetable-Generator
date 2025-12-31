import React, { useState } from 'react'
import '../../styles/formComponents.css'
import '../../styles/branchSetup.css'

function Step3Divisions({ formData, onChange, errors, setErrors }) {
    const academicYears = formData.academicYears || []
    const divisions = formData.divisions || {}
    const [applyToAll, setApplyToAll] = useState(false)

    // Generate division labels from count
    const generateDivisionLabels = (count) => {
        const labels = []
        for (let i = 0; i < count; i++) {
            labels.push(String.fromCharCode(65 + i)) // A, B, C, ...
        }
        return labels
    }

    // Handle division count change
    const handleDivisionCountChange = (year, delta) => {
        const currentDivisions = divisions[year] || ['A', 'B', 'C']
        const newCount = Math.max(1, Math.min(10, currentDivisions.length + delta))
        const newDivisions = generateDivisionLabels(newCount)

        if (applyToAll) {
            // Apply to all years
            const updatedDivisions = {}
            academicYears.forEach(y => {
                updatedDivisions[y] = newDivisions
            })
            onChange('divisions', updatedDivisions)
        } else {
            onChange('divisions', { ...divisions, [year]: newDivisions })
        }
    }

    // Handle batch count change
    const handleBatchCountChange = (year, delta) => {
        const currentBatches = formData.labBatchesPerYear?.[year] || 3
        const newCount = Math.max(1, Math.min(6, currentBatches + delta))

        const updatedBatches = { ...formData.labBatchesPerYear, [year]: newCount }

        if (applyToAll) {
            academicYears.forEach(y => {
                updatedBatches[y] = newCount
            })
        }

        onChange('labBatchesPerYear', updatedBatches)
    }

    // Handle apply to all toggle
    const handleApplyToAllToggle = () => {
        const newApplyToAll = !applyToAll
        setApplyToAll(newApplyToAll)

        if (newApplyToAll && academicYears.length > 0) {
            // Use first year's divisions for all
            const firstYear = academicYears[0]
            const firstYearDivisions = divisions[firstYear] || ['A', 'B', 'C']
            const updatedDivisions = {}
            academicYears.forEach(y => {
                updatedDivisions[y] = [...firstYearDivisions]
            })
            onChange('divisions', updatedDivisions)
        }
    }

    // Initialize divisions for years that don't have them
    React.useEffect(() => {
        const updatedDivisions = { ...divisions }
        let hasChanges = false

        academicYears.forEach(year => {
            if (!updatedDivisions[year]) {
                updatedDivisions[year] = ['A', 'B', 'C']
                hasChanges = true
            }
        })

        if (hasChanges) {
            onChange('divisions', updatedDivisions)
        }

        // Initialize Batches
        const updatedBatches = { ...formData.labBatchesPerYear }
        let hasBatchChanges = false
        academicYears.forEach(year => {
            if (!updatedBatches[year]) {
                updatedBatches[year] = 3 // Default to 3 batches
                hasBatchChanges = true
            }
        })

        if (hasBatchChanges) {
            onChange('labBatchesPerYear', updatedBatches)
        }
    }, [academicYears])

    return (
        <div className="step-content">
            <h2 className="step-title">
                <span>🏛️</span>
                Divisions Structure
            </h2>
            <p className="step-description">
                Configure the number of divisions (sections) for each academic year.
            </p>

            {/* Apply to All Toggle */}
            <div className="toggle-field">
                <span className="toggle-label">Apply same divisions to all years</span>
                <div
                    className={`toggle-switch ${applyToAll ? 'active' : ''}`}
                    onClick={handleApplyToAllToggle}
                >
                    <div className="toggle-slider"></div>
                </div>
            </div>

            {/* Division Cards */}
            <div className="division-config-cards">
                {academicYears.map((year) => {
                    const yearDivisions = divisions[year] || ['A', 'B', 'C']
                    return (
                        <div key={year} className="division-card">
                            <div className="division-card-header">
                                <div className="division-card-title">
                                    {year} - {year === 'SE' ? 'Second Year' : year === 'TE' ? 'Third Year' : 'Final Year'}
                                </div>
                                <div className="number-stepper">
                                    <button
                                        className="stepper-button"
                                        onClick={() => handleDivisionCountChange(year, -1)}
                                        disabled={yearDivisions.length <= 1}
                                    >
                                        −
                                    </button>
                                    <div className="stepper-value">{yearDivisions.length}</div>
                                    <button
                                        className="stepper-button"
                                        onClick={() => handleDivisionCountChange(year, 1)}
                                        disabled={yearDivisions.length >= 10}
                                    >
                                        +
                                    </button>
                                </div>
                            </div>

                            {/* Batches Configuration */}
                            <div className="batch-config-section" style={{
                                marginTop: '12px',
                                padding: '12px',
                                backgroundColor: '#f8fafc',
                                borderRadius: '8px',
                                border: '1px solid #e2e8f0'
                            }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <div style={{ fontSize: '0.9rem', fontWeight: '600', color: '#475569' }}>
                                        Batches per Division
                                        <span style={{
                                            display: 'block',
                                            fontSize: '0.75rem',
                                            fontWeight: '400',
                                            color: '#64748b',
                                            marginTop: '2px'
                                        }}>
                                            Parallel lab groups (e.g., A1, A2, A3)
                                        </span>
                                    </div>
                                    <div className="number-stepper">
                                        <button
                                            className="stepper-button"
                                            onClick={() => handleBatchCountChange(year, -1)}
                                            disabled={(formData.labBatchesPerYear?.[year] || 3) <= 1}
                                        >
                                            −
                                        </button>
                                        <div className="stepper-value">{formData.labBatchesPerYear?.[year] || 3}</div>
                                        <button
                                            className="stepper-button"
                                            onClick={() => handleBatchCountChange(year, 1)}
                                            disabled={(formData.labBatchesPerYear?.[year] || 3) >= 6}
                                        >
                                            +
                                        </button>
                                    </div>
                                </div>
                            </div>

                            {/* Division Tags */}
                            <div className="tag-list">
                                {yearDivisions.map((div, idx) => (
                                    <div key={idx} className="tag">
                                        {year}-{div}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )
                })}
            </div>

            {academicYears.length === 0 && (
                <div style={{
                    padding: 'var(--spacing-8)',
                    textAlign: 'center',
                    color: 'var(--color-gray-600)'
                }}>
                    Please select academic years in the previous step
                </div>
            )}
        </div>
    )
}

export default Step3Divisions
