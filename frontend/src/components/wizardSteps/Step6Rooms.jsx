import React, { useState, useEffect } from 'react'
import '../../styles/formComponents.css'
import '../../styles/branchSetup.css'

function Step6Rooms({ formData, onChange }) {
    // Ensure classrooms is an array (Migration from old dict format)
    const [localRooms, setLocalRooms] = useState([])
    const [newRoomName, setNewRoomName] = useState('')

    // Shared Labs state
    const sharedLabs = formData.sharedLabs || []
    const [newLabName, setNewLabName] = useState('')
    const [newLabCapacity, setNewLabCapacity] = useState(25)

    // Default Config
    const DEFAULT_DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    const DEFAULT_SLOTS = [1, 2, 3, 4, 5, 6, 7, 8]

    // Initialize / Migrate Data
    useEffect(() => {
        let titleRooms = []

        if (Array.isArray(formData.classrooms)) {
            titleRooms = [...formData.classrooms]
        } else if (typeof formData.classrooms === 'object' && formData.classrooms !== null) {
            // Migration: Flatten existing year-wise rooms
            const allRooms = new Set()
            Object.values(formData.classrooms).forEach(rooms => {
                if (Array.isArray(rooms)) rooms.forEach(r => allRooms.add(r))
            })
            titleRooms = Array.from(allRooms)
        }

        // Defaults if empty
        if (titleRooms.length === 0) {
            titleRooms = ['Room-101', 'Room-102', 'Room-103', 'Seminar Hall']
            // Push changes immediately only if empty to avoid overriding user deletions on re-render?
            // Better to just update local state. Data sync happens via onChange.
            onChange('classrooms', titleRooms)
        }

        setLocalRooms(titleRooms)

        // Initialize shared labs if empty
        if (!formData.sharedLabs || formData.sharedLabs.length === 0) {
            onChange('sharedLabs', [
                { name: 'Computer Lab 1', availableDays: [...DEFAULT_DAYS], availableSlots: [...DEFAULT_SLOTS], capacity: 30 },
                { name: 'Physics Lab', availableDays: [...DEFAULT_DAYS], availableSlots: [...DEFAULT_SLOTS], capacity: 30 }
            ])
        }
    }, []) // Run once on mount to handle migration

    // -- ROOM HANDLERS --

    const handleAddRoom = () => {
        if (!newRoomName.trim()) return
        const updated = [...localRooms, newRoomName.trim()]
        setLocalRooms(updated)
        onChange('classrooms', updated)
        setNewRoomName('')
    }

    const handleRemoveRoom = (index) => {
        const updated = localRooms.filter((_, i) => i !== index)
        setLocalRooms(updated)
        onChange('classrooms', updated)
    }

    const handleQuickAddRooms = () => {
        const count = localRooms.length
        const added = [`Room-${101 + count}`, `Room-${102 + count}`, `Room-${103 + count}`]
        const updated = [...localRooms, ...added]
        setLocalRooms(updated)
        onChange('classrooms', updated)
    }

    // -- LAB HANDLERS --

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

    const handleRemoveLab = (index) => {
        onChange('sharedLabs', sharedLabs.filter((_, i) => i !== index))
    }

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
                Shared Rooms & Labs
            </h2>
            <p className="step-description">
                Define the pool of classrooms and labs available to the <strong>entire branch</strong>.<br />
                The scheduler will dynamically assign these resources to any class as needed.
            </p>

            {/* SHARED ROOMS SECTION */}
            <div className="room-section">
                <h3 className="room-section-title">
                    <span>🚪</span>
                    Branch Classrooms (Shared Pool)
                </h3>

                <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
                    <input
                        type="text"
                        className="input-text"
                        placeholder="e.g. Room-101, LH-5"
                        value={newRoomName}
                        onChange={(e) => setNewRoomName(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleAddRoom()}
                        style={{ flex: 1 }}
                    />
                    <button className="btn-add" onClick={handleAddRoom}>+ Add</button>
                    <button className="btn-quick-add" onClick={handleQuickAddRooms}>+ Quick 3</button>
                </div>

                <div className="tag-list">
                    {localRooms.map((room, idx) => (
                        <div key={idx} className="tag">
                            {room}
                            <span className="tag-remove" onClick={() => handleRemoveRoom(idx)}>×</span>
                        </div>
                    ))}
                    {localRooms.length === 0 && (
                        <div style={{ color: '#94a3b8', fontStyle: 'italic', padding: '8px' }}>
                            No rooms added. Please add at least one classroom.
                        </div>
                    )}
                </div>
            </div>

            {/* SHARED LABS SECTION */}
            <div className="room-section" style={{ marginTop: '32px' }}>
                <h3 className="room-section-title">
                    <span>🔬</span>
                    Shared Laboratories
                </h3>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1, marginBottom: '16px' }}>
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
                    <button className="btn-add" onClick={handleAddLab}>+ Add Lab</button>
                </div>

                <div className="labs-grid" style={{ display: 'grid', gap: '12px' }}>
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
                                        Capacity: {lab.capacity || 25}
                                    </div>
                                </div>
                            </div>

                            <button
                                onClick={() => handleRemoveLab(idx)}
                                style={{
                                    color: '#ef4444',
                                    background: '#fef2f2',
                                    border: 'none',
                                    width: '28px', height: '28px',
                                    borderRadius: '6px',
                                    cursor: 'pointer',
                                    display: 'flex', alignItems: 'center', justifyContent: 'center'
                                }}
                            >
                                ✕
                            </button>
                        </div>
                    ))}
                    {sharedLabs.length === 0 && (
                        <div style={{ color: '#94a3b8', fontStyle: 'italic', padding: '8px' }}>
                            No labs defined.
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}

export default Step6Rooms
