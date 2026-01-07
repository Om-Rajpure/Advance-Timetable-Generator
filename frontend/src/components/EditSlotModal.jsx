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

    // Computed: Filter teachers based on subject
    const filteredTeachers = React.useMemo(() => {
        if (!modifiedSlot.subject) return []; // No subject selected -> No teachers

        const mapping = context?.smartInputData?.teacherSubjectMap || [];

        // CHECK: Do we have ANY mapping data?
        // If inferred context (Edit Existing), mapping might be empty and teacher.subjects empty.
        // In that case, we MUST fallback to showing ALL teachers.
        const hasMappingData = mapping.length > 0 || teachers.some(t => t.subjects && t.subjects.length > 0);

        if (!hasMappingData) {
            return teachers; // Fallback: No filter
        }

        // 1. Find valid teacher names from Map (Normalize for safety)
        const targetSubject = modifiedSlot.subject.trim().toLowerCase();

        const validFromMap = new Set(
            mapping
                .filter(m => (m.subjectName || '').trim().toLowerCase() === targetSubject)
                .map(m => m.teacherName)
        );

        return teachers.filter(t => {
            // Check Map OR Embedded subjects
            const hasSubject = t.subjects?.some(s => s.trim().toLowerCase() === targetSubject);
            return validFromMap.has(t.name) || hasSubject;
        });
    }, [modifiedSlot.subject, teachers, context]);

    const handleFieldChange = async (field, value) => {
        let updated = { ...modifiedSlot, [field]: value };

        // AUTO-RESET: specialized logic for subject change
        if (field === 'subject') {
            const newSubject = value;
            if (newSubject) {
                // Re-calculate valid teachers for this NEW subject
                const mapping = context?.smartInputData?.teacherSubjectMap || [];
                const validFromMap = new Set(
                    mapping.filter(m => m.subjectName === newSubject).map(m => m.teacherName)
                );

                // If current teacher is not valid for new subject, clear it
                // We check against the full list of teachers to satisfy the condition
                const isCurrentValid = teachers.some(t =>
                    t.name === modifiedSlot.teacher &&
                    (validFromMap.has(t.name) || t.subjects?.includes(newSubject))
                );

                if (!isCurrentValid) {
                    updated.teacher = '';
                }
            } else {
                updated.teacher = '';
            }
        }

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
                            disabled={!modifiedSlot.subject || filteredTeachers.length === 0}
                        >
                            <option value="">
                                {!modifiedSlot.subject
                                    ? "Select a subject first"
                                    : filteredTeachers.length === 0
                                        ? "No teachers available for this subject"
                                        : "Select teacher..."}
                            </option>
                            {filteredTeachers.map(teacher => (
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
