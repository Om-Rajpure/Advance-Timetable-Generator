import React from 'react'
import '../../styles/formComponents.css'

const ACADEMIC_YEARS = [
    {
        key: 'SE',
        label: 'Second Year',
        abbr: 'SE',
        icon: '📘',
        description: 'Second Year Engineering'
    },
    {
        key: 'TE',
        label: 'Third Year',
        abbr: 'TE',
        icon: '📗',
        description: 'Third Year Engineering'
    },
    {
        key: 'BE',
        label: 'Final Year',
        abbr: 'BE',
        icon: '📕',
        description: 'Bachelor of Engineering'
    }
]

function Step2AcademicYears({ formData, onChange, errors, setErrors }) {
    const selectedYears = formData.academicYears || ['SE', 'TE', 'BE']

    const handleToggleYear = (yearKey) => {
        let newYears = [...selectedYears]

        if (newYears.includes(yearKey)) {
            newYears = newYears.filter(y => y !== yearKey)
        } else {
            newYears.push(yearKey)
        }

        // Validation: At least one year must be selected
        if (newYears.length === 0) {
            setErrors({ ...errors, academicYears: 'Please select at least one academic year' })
        } else {
            setErrors({ ...errors, academicYears: null })
        }

        onChange('academicYears', newYears)
    }

    return (
        <div className="step-content">
            <h2 className="step-title">
                <span>📚</span>
                Academic Years
            </h2>
            <p className="step-description">
                Select which academic years this branch offers. You can select multiple years.
            </p>

            <div className="checkbox-cards">
                {ACADEMIC_YEARS.map((year) => (
                    <div
                        key={year.key}
                        className={`checkbox-card ${selectedYears.includes(year.key) ? 'selected' : ''}`}
                        onClick={() => handleToggleYear(year.key)}
                    >
                        <div className="checkbox-card-checkmark">✓</div>
                        <div className="checkbox-card-icon">{year.icon}</div>
                        <div className="checkbox-card-title">{year.abbr}</div>
                        <div className="checkbox-card-subtitle">{year.label}</div>
                    </div>
                ))}
            </div>

            {errors.academicYears && (
                <div className="input-error" style={{ marginTop: 'var(--spacing-4)' }}>
                    <span>⚠️</span>
                    {errors.academicYears}
                </div>
            )}

            <div style={{
                marginTop: 'var(--spacing-8)',
                padding: 'var(--spacing-4)',
                background: 'var(--color-gray-50)',
                borderRadius: 'var(--radius-lg)',
                textAlign: 'center'
            }}>
                <p style={{ color: 'var(--color-gray-700)', marginBottom: 'var(--spacing-2)' }}>
                    <strong>Selected:</strong> {selectedYears.length} year{selectedYears.length !== 1 ? 's' : ''}
                </p>
                <p style={{ color: 'var(--color-gray-600)', fontSize: 'var(--font-size-sm)' }}>
                    {selectedYears.map(y => ACADEMIC_YEARS.find(ay => ay.key === y)?.label).join(', ') || 'None'}
                </p>
            </div>
        </div>
    )
}

export default Step2AcademicYears
