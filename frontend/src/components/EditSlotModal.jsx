import React, { useState, useEffect } from 'react';
import { validateEdit } from '../utils/editValidator';
import ConflictPanel from './ConflictPanel';
import AutoFixButton from './AutoFixButton';
import './EditSlotModal.css';

function EditSlotModal({ slot, timetable, context, onSave, onClose }) {
    const [modifiedSlot, setModifiedSlot] = useState(slot);
    const [conflicts, setConflicts] = useState([]);
    const [validating, setValidating] = useState(false);
    const [isValid, setIsValid] = useState(true);

    // Available options
    const subjects = context?.smartInputData?.subjects || [];
    const teachers = context?.smartInputData?.teachers || [];
    const rooms = slot?.type === 'Practical'
        ? context?.branchData?.labs || []
        : context?.branchData?.rooms || [];

    useEffect(() => {
        // Validate on mount
        handleValidation(modifiedSlot);
    }, []);

    const handleFieldChange = async (field, value) => {
        const updated = { ...modifiedSlot, [field]: value };
        setModifiedSlot(updated);
        await handleValidation(updated);
    };

    const handleValidation = async (slotToValidate) => {
        setValidating(true);
        try {
            const result = await validateEdit(slotToValidate, timetable, context);
            setConflicts(result.conflicts || []);
            setIsValid(result.valid);
        } catch (error) {
            console.error('Validation error:', error);
        } finally {
            setValidating(false);
        }
    };

    const handleSave = () => {
        if (isValid) {
            onSave(modifiedSlot);
            onClose();
        }
    };

    const handleAutoFixApplied = (fixedSlot) => {
        setModifiedSlot(fixedSlot);
        handleValidation(fixedSlot);
    };

    const isPractical = slot?.type === 'Practical';

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                    <h2>Edit Slot</h2>
                    <p className="slot-info">
                        {slot?.day} - Slot {(slot?.slot || 0) + 1} - {slot?.year}-{slot?.division}
                    </p>
                </div>

                <div className="modal-body">
                    {isPractical && (
                        <div className="practical-warning">
                            ⚠️ This is a practical slot. Changes affect all batches.
                        </div>
                    )}

                    <div className="form-group">
                        <label>Subject</label>
                        <select
                            value={modifiedSlot.subject || ''}
                            onChange={(e) => handleFieldChange('subject', e.target.value)}
                        >
                            <option value="">Select subject...</option>
                            {subjects.map(sub => (
                                <option key={sub.name} value={sub.name}>
                                    {sub.name}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div className="form-group">
                        <label>Teacher</label>
                        <select
                            value={modifiedSlot.teacher || ''}
                            onChange={(e) => handleFieldChange('teacher', e.target.value)}
                        >
                            <option value="">Select teacher...</option>
                            {teachers.map(teacher => (
                                <option key={teacher.name} value={teacher.name}>
                                    {teacher.name}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div className="form-group">
                        <label>{isPractical ? 'Lab' : 'Room'}</label>
                        <select
                            value={modifiedSlot.room || ''}
                            onChange={(e) => handleFieldChange('room', e.target.value)}
                        >
                            <option value="">Select {isPractical ? 'lab' : 'room'}...</option>
                            {rooms.map(room => (
                                <option key={room} value={room}>
                                    {room}
                                </option>
                            ))}
                        </select>
                    </div>

                    {validating && (
                        <div className="validating">🔄 Validating...</div>
                    )}

                    <ConflictPanel conflicts={conflicts} />

                    {conflicts.length > 0 && (
                        <AutoFixButton
                            slot={modifiedSlot}
                            conflicts={conflicts}
                            timetable={timetable}
                            context={context}
                            onFixApplied={handleAutoFixApplied}
                        />
                    )}
                </div>

                <div className="modal-footer">
                    <button className="btn-cancel" onClick={onClose}>
                        Cancel
                    </button>
                    <button
                        className="btn-save"
                        onClick={handleSave}
                        disabled={!isValid || validating}
                    >
                        Save Changes
                    </button>
                </div>
            </div>
        </div>
    );
}

export default EditSlotModal;
