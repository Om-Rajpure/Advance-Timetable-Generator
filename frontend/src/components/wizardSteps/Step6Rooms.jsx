import React, { useState } from 'react'
import '../../styles/formComponents.css'
import '../../styles/branchSetup.css'

function Step6Rooms({ formData, onChange }) {
    const academicYears = formData.academicYears || []
    const classrooms = formData.classrooms || {}
    const sharedLabs = formData.sharedLabs || []
    const [reuseRooms, setReuseRooms] = useState(false)
    const [newRoomInputs, setNewRoomInputs] = useState({})
    const [newLabName, setNewLabName] = useState('')
    const [newLabCapacity, setNewLabCapacity] = useState(25) // Default Capacity

    // Default Configuration Constants
    const DEFAULT_DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    const DEFAULT_SLOTS = [1, 2, 3, 4, 5, 6, 7, 8]

    // Initialize classrooms for years
    React.useEffect(() => {
        const updatedClassrooms = { ...classrooms }
        let hasChanges = false

        academicYears.forEach(year => {
            if (!updatedClassrooms[year]) {
                updatedClassrooms[year] = [`${year}-101`, `${year}-102`, `${year}-103`]
                hasChanges = true
            }
        })

        if (hasChanges) {
            onChange('classrooms', updatedClassrooms)
        }

        // Initialize shared labs if empty
        if (sharedLabs.length === 0) {
            onChange('sharedLabs', [
                { name: 'Computer Lab 1', availableDays: [...DEFAULT_DAYS], availableSlots: [...DEFAULT_SLOTS], capacity: 30 },
                { name: 'Computer Lab 2', availableDays: [...DEFAULT_DAYS], availableSlots: [...DEFAULT_SLOTS], capacity: 30 },
                { name: 'Electronics Lab', availableDays: [...DEFAULT_DAYS], availableSlots: [...DEFAULT_SLOTS], capacity: 20 }
            ])
        } else {
            // Migration: Ensure existing labs have availability fields
            const migratedLabs = sharedLabs.map(lab => ({
                ...lab,
                availableDays: lab.availableDays || [...DEFAULT_DAYS],
                availableSlots: lab.availableSlots || [...DEFAULT_SLOTS]
            }))
            // Only update if changes found
            const needsUpdate = JSON.stringify(migratedLabs) !== JSON.stringify(sharedLabs)
            if (needsUpdate) onChange('sharedLabs', migratedLabs)
        }
    }, [academicYears])

    // Handle room addition
    const handleAddRoom = (year) => {
        const roomName = newRoomInputs[year] || ''
        if (roomName.trim()) {
            const updatedClassrooms = {
                ...classrooms,
                [year]: [...(classrooms[year] || []), roomName.trim()]
            }

            if (reuseRooms) {
                // Apply to all years
                academicYears.forEach(y => {
                    updatedClassrooms[y] = updatedClassrooms[year]
                })
            }

            onChange('classrooms', updatedClassrooms)
            setNewRoomInputs({ ...newRoomInputs, [year]: '' })
        }
    }

    // Handle room removal
    const handleRemoveRoom = (year, index) => {
        const updatedClassrooms = {
            ...classrooms,
            [year]: classrooms[year].filter((_, i) => i !== index)
        }
        onChange('classrooms', updatedClassrooms)
    }

    // Handle quick add (multiple rooms)
    const handleQuickAdd = (year) => {
        const currentRooms = classrooms[year] || []
        const count = currentRooms.length
        const newRooms = [
            ...currentRooms,
            `${year}-${count + 1}`,
            `${year}-${count + 2}`,
            `${year}-${count + 3}`
        ]

        const updatedClassrooms = { ...classrooms, [year]: newRooms }

        if (reuseRooms) {
            academicYears.forEach(y => {
                updatedClassrooms[y] = newRooms
            })
        }

        onChange('classrooms', updatedClassrooms)
    }

    // Handle lab addition
    const handleAddLab = () => {
        if (newLabName.trim()) {
            const newLab = {
                name: newLabName.trim(),
                availableDays: [...DEFAULT_DAYS],
                availableSlots: [...DEFAULT_SLOTS],
                capacity: newLabCapacity || 25
            }
            onChange('sharedLabs', [...sharedLabs, newLab])
            setNewLabName('')
            setNewLabCapacity(25)
        }
    }

    // Handle lab removal
    const handleRemoveLab = (index) => {
        onChange('sharedLabs', sharedLabs.filter((_, i) => i !== index))
    }



    // Handle Capacity Update
    const handleCapacityChange = (labIndex, delta) => {
        const updatedLabs = [...sharedLabs]
        const lab = updatedLabs[labIndex]
        const current = lab.capacity || 25
        lab.capacity = Math.max(1, current + delta)
        onChange('sharedLabs', updatedLabs)
    }

    return (
        <div className="step-content">
            <h2 className="step-title">
                <span>🏫</span>
                Rooms & Shared Labs
            </h2>
            <p className="step-description">
                Define classrooms for each year and shared laboratory spaces.
            </p>

            {/* Reuse Rooms Toggle */}
            <div className="toggle-field">
                <span className="toggle-label">Reuse same rooms for all years</span>
                <div
                    className={`toggle-switch ${reuseRooms ? 'active' : ''}`}
                    onClick={() => setReuseRooms(!reuseRooms)}
                >
                    <div className="toggle-slider"></div>
                </div>
            </div>

            {/* Classrooms Section */}
            <div className="room-section">
                <h3 className="room-section-title">
                    <span>🚪</span>
                    Classrooms
                </h3>

                {academicYears.map((year) => (
                    <div key={year} className="division-card" style={{ marginBottom: 'var(--spacing-4)' }}>
                        <div className="division-card-header">
                            <div className="division-card-title">{year} Classrooms</div>
                        </div>

                        <div className="room-input-wrapper">
                            <input
                                type="text"
                                className="input-text"
                                placeholder={`e.g., ${year}-104, Room-A`}
                                value={newRoomInputs[year] || ''}
                                onChange={(e) => setNewRoomInputs({ ...newRoomInputs, [year]: e.target.value })}
                                onKeyPress={(e) => e.key === 'Enter' && handleAddRoom(year)}
                            />
                            <button className="btn-add" onClick={() => handleAddRoom(year)}>
                                + Add
                            </button>
                        </div>

                        <button className="btn-quick-add" onClick={() => handleQuickAdd(year)}>
                            ⚡ Quick Add +3 Rooms
                        </button>

                        <div className="tag-list">
                            {(classrooms[year] || []).map((room, idx) => (
                                <div key={idx} className="tag">
                                    {room}
                                    <span className="tag-remove" onClick={() => handleRemoveRoom(year, idx)}>
                                        ×
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                ))}
            </div>

            {/* Shared Labs Section */}
            <div className="room-section">
                <h3 className="room-section-title">
                    <span>🔬</span>
                    Shared Labs
                </h3>
                <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-gray-600)', marginBottom: 'var(--spacing-4)' }}>
                    Labs are shared across all years of this branch
                </p>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1 }}>
                    <input
                        type="text"
                        className="input-text"
                        placeholder="New Lab Name (e.g., Physics Lab)"
                        value={newLabName}
                        onChange={(e) => setNewLabName(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleAddLab()}
                        style={{ flex: 1 }}
                    />
                    <input
                        type="number"
                        className="input-text"
                        placeholder="Cap."
                        title="Lab Capacity"
                        value={newLabCapacity}
                        onChange={(e) => setNewLabCapacity(parseInt(e.target.value) || '')}
                        onKeyPress={(e) => e.key === 'Enter' && handleAddLab()}
                        style={{ width: '80px' }}
                    />
                    <button className="btn-add" onClick={handleAddLab}>
                        + Add Lab
                    </button>
                </div>

                <div className="labs-grid" style={{ display: 'grid', gap: '12px', marginTop: '16px' }}>
                    {sharedLabs.map((lab, idx) => (
                        <div key={idx} className="lab-card-minimal" style={{
                            border: '1px solid #e2e8f0',
                            borderRadius: '8px',
                            padding: '12px 16px',
                            background: '#fff',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            boxShadow: '0 1px 2px rgba(0,0,0,0.05)'
                        }}>
                            {/* Left: Icon & Name */}
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                <div style={{
                                    width: '32px', height: '32px',
                                    background: '#e0f2fe', color: '#0284c7',
                                    borderRadius: '6px', display: 'flex',
                                    alignItems: 'center', justifyContent: 'center',
                                    fontSize: '1.1rem'
                                }}>
                                    🔬
                                </div>
                                <div>
                                    <div style={{ fontWeight: '600', fontSize: '0.95rem', color: '#1e293b' }}>
                                        {lab.name}
                                    </div>
                                    <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
                                        {lab.availableDays?.length === 6 ? 'All Days' : `${lab.availableDays?.length} Days`} • {lab.availableSlots?.length === 8 ? 'All Slots' : `${lab.availableSlots?.length} Slots`}
                                    </div>
                                </div>
                            </div>

                            {/* Right: Controls */}
                            <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
                                {/* Capacity Stepper */}
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                    <label style={{ fontSize: '0.75rem', fontWeight: '600', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                                        Capacity:
                                    </label>
                                    <div className="number-stepper" style={{ display: 'flex', alignItems: 'center', gap: '4px', background: '#f8fafc', padding: '2px', borderRadius: '4px', border: '1px solid #cbd5e1' }}>
                                        <button
                                            onClick={() => handleCapacityChange(idx, -5)}
                                            style={{
                                                width: '24px', height: '24px',
                                                border: 'none', background: '#fff',
                                                borderRadius: '3px', cursor: 'pointer',
                                                color: '#334155', fontWeight: 'bold',
                                                boxShadow: '0 1px 1px rgba(0,0,0,0.05)'
                                            }}
                                        >
                                            −
                                        </button>
                                        <span style={{ fontWeight: '600', fontSize: '0.9rem', minWidth: '24px', textAlign: 'center', color: '#0f172a' }}>
                                            {lab.capacity || 25}
                                        </span>
                                        <button
                                            onClick={() => handleCapacityChange(idx, 5)}
                                            style={{
                                                width: '24px', height: '24px',
                                                border: 'none', background: '#fff',
                                                borderRadius: '3px', cursor: 'pointer',
                                                color: '#334155', fontWeight: 'bold',
                                                boxShadow: '0 1px 1px rgba(0,0,0,0.05)'
                                            }}
                                        >
                                            +
                                        </button>
                                    </div>
                                </div>

                                {/* Divider */}
                                <div style={{ width: '1px', height: '24px', background: '#e2e8f0' }}></div>

                                {/* Remove Button */}
                                <button
                                    onClick={() => handleRemoveLab(idx)}
                                    title="Remove Lab"
                                    style={{
                                        color: '#ef4444',
                                        background: '#fef2f2',
                                        border: 'none',
                                        width: '28px', height: '28px',
                                        borderRadius: '6px',
                                        cursor: 'pointer',
                                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                                        transition: 'all 0.2s'
                                    }}
                                >
                                    ✕
                                </button>
                            </div>
                        </div>
                    ))}
                </div>

                {sharedLabs.length < 3 && (
                    <div style={{
                        marginTop: 'var(--spacing-4)',
                        padding: 'var(--spacing-3)',
                        background: '#FEF3C7',
                        borderRadius: 'var(--radius-md)',
                        fontSize: 'var(--font-size-sm)',
                        color: '#92400E'
                    }}>
                        ⚠️ Recommended: At least 3 labs for better timetable flexibility
                    </div>
                )}


            </div>
        </div>
    )
}

export default Step6Rooms
