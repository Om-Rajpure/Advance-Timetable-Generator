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
    const [newLabCapacity, setNewLabCapacity] = useState('')

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
                { name: 'Computer Lab 1', capacity: 30 },
                { name: 'Computer Lab 2', capacity: 30 },
                { name: 'Electronics Lab', capacity: 25 }
            ])
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
                capacity: newLabCapacity ? parseInt(newLabCapacity) : null
            }
            onChange('sharedLabs', [...sharedLabs, newLab])
            setNewLabName('')
            setNewLabCapacity('')
        }
    }

    // Handle lab removal
    const handleRemoveLab = (index) => {
        onChange('sharedLabs', sharedLabs.filter((_, i) => i !== index))
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

                <div className="room-input-wrapper">
                    <input
                        type="text"
                        className="input-text"
                        placeholder="Lab name (e.g., Computer Lab 3)"
                        value={newLabName}
                        onChange={(e) => setNewLabName(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleAddLab()}
                    />
                    <input
                        type="number"
                        className="input-text"
                        placeholder="Capacity"
                        style={{ maxWidth: '120px' }}
                        value={newLabCapacity}
                        onChange={(e) => setNewLabCapacity(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleAddLab()}
                    />
                    <button className="btn-add" onClick={handleAddLab}>
                        + Add Lab
                    </button>
                </div>

                <div className="tag-list">
                    {sharedLabs.map((lab, idx) => (
                        <div key={idx} className="tag">
                            {lab.name} {lab.capacity && `(${lab.capacity})`}
                            <span className="tag-remove" onClick={() => handleRemoveLab(idx)}>
                                ×
                            </span>
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
