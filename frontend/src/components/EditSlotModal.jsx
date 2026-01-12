import React, { useState, useEffect, useMemo } from 'react';
import { validateEdit } from '../utils/editValidator';
import ConflictPanel from './ConflictPanel';
import AutoFixButton from './AutoFixButton';
import './EditSlotModal.css';

function EditSlotModal({ slot, timetable, context, onSave, onClose }) {
    const [modifiedSlot, setModifiedSlot] = useState(slot);
    const [conflicts, setConflicts] = useState([]);
    const [validating, setValidating] = useState(false);
    const [isValid, setIsValid] = useState(true);

    // Context Extraction
    const allSubjects = context?.smartInputData?.subjects || [];
    const allTeachers = context?.smartInputData?.teachers || [];

    // --- 1. SUBJECT FILTERING (Context-Aware: By Year/Div) ---
    const filteredSubjects = useMemo(() => {
        if (!slot || !slot.year) return allSubjects;

        const targetYear = slot.year.trim().toLowerCase();

        return allSubjects.filter(sub => {
            // Strict match: Year must match
            // Loose match: If subject has NO year, maybe show it? (Safer to be strict)
            const sYear = sub.year ? sub.year.trim().toLowerCase() : '';
            return sYear === targetYear;
        });
    }, [allSubjects, slot]);

    // --- 2. TEACHER FILTERING (Context-Aware: By Subject) ---
    const filteredTeachers = useMemo(() => {
        // If no subject selected in the modal yet
        if (!modifiedSlot.subject) return [];

        const targetSubjectName = modifiedSlot.subject.trim().toLowerCase();
        const mapping = context?.smartInputData?.teacherSubjectMap || [];

        // Strategy: 
        // 1. Look in Map (Input Phase Mapping)
        // 2. Look in Teacher Objects (if they have 'subjects' array)

        // A. From Map
        const mappedTeacherNames = new Set();
        mapping.forEach(m => {
            if (m.subjectName && m.subjectName.trim().toLowerCase() === targetSubjectName) {
                mappedTeacherNames.add(m.teacherName);
            }
        });

        // B. From Teacher Object
        // (Sometimes mapping is inferred or stored directly on teacher)
        allTeachers.forEach(t => {
            if (t.subjects && Array.isArray(t.subjects)) {
                if (t.subjects.some(s => s.trim().toLowerCase() === targetSubjectName)) {
                    mappedTeacherNames.add(t.name);
                }
            }
        });

        const allowedTeachers = allTeachers.filter(t => mappedTeacherNames.has(t.name));

        // Fallback: If NO teachers mapped at all for this subject, 
        // should we show ALL teachers? (Maybe it's a new subject).
        // Decision: Show ALL with a visual warning -> or just Disable?
        // User requested: "Disable teacher dropdown... Show message"
        return allowedTeachers;

    }, [modifiedSlot.subject, allTeachers, context]);

    const rooms = slot?.type === 'Practical' || slot?.isPractical
        ? context?.branchData?.labs || []
        : context?.branchData?.rooms || [];

    // --- 3. HANDLERS ---

    useEffect(() => {
        handleValidation(modifiedSlot);
    }, []); // Check initial state

    const handleFieldChange = async (field, value) => {
        let updated = { ...modifiedSlot, [field]: value };

        // Specialized Logic when changing Subject
        if (field === 'subject') {
            // Reset Teacher if current teacher doesn't teach valid subject
            // Or just reset always to force user to pick valid one? 
            // Better UX: Reset always to avoid invalid ghost state.
            updated.teacher = '';
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

    // --- 4. UI HELPERS ---
    const isPractical = slot?.type === 'Practical' || slot?.isPractical;
    const hasTeachers = filteredTeachers.length > 0;
    const subjectSelected = !!modifiedSlot.subject;

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="edit-slot-card" onClick={(e) => e.stopPropagation()}>

                {/* HEADER */}
                <div className="card-header">
                    <div className="header-icon">✏️</div>
                    <div className="header-info">
                        <h2>Edit Slot</h2>
                        <span className="slot-meta">
                            {slot?.day} • Slot {(slot?.slot || 0) + 1} • {slot?.year} - {slot?.division}
                        </span>
                    </div>
                    <button className="close-btn" onClick={onClose}>×</button>
                </div>

                {/* BODY */}
                <div className="card-body">

                    {/* Practical Warning */}
                    {isPractical && (
                        <div className="notice-box warning">
                            <span className="icon">⚠️</span>
                            <div className="text">
                                <strong>Practical Slot</strong><br />
                                Changes here apply to the entire batch block.
                            </div>
                        </div>
                    )}

                    <div className="input-grid">
                        {/* SUBJECT */}
                        <div className="form-group">
                            <label>Subject</label>
                            <select
                                value={modifiedSlot.subject || ''}
                                onChange={(e) => handleFieldChange('subject', e.target.value)}
                                className={!modifiedSlot.subject ? 'empty' : ''}
                            >
                                <option value="">Select a Subject...</option>
                                {filteredSubjects.map(sub => (
                                    <option key={sub.name} value={sub.name}>{sub.name}</option>
                                ))}
                            </select>
                            <div className="field-hint">{filteredSubjects.length} subjects found for {slot?.year}</div>
                        </div>

                        {/* TEACHER */}
                        <div className="form-group">
                            <label>Teacher</label>
                            <select
                                value={modifiedSlot.teacher || ''}
                                onChange={(e) => handleFieldChange('teacher', e.target.value)}
                                disabled={!subjectSelected || !hasTeachers}
                                className={!modifiedSlot.teacher ? 'empty' : ''}
                            >
                                <option value="">
                                    {!subjectSelected ? "First select a subject" :
                                        !hasTeachers ? "No teachers found" :
                                            "Select a Teacher..."}
                                </option>
                                {filteredTeachers.map(t => (
                                    <option key={t.name} value={t.name}>{t.name}</option>
                                ))}
                            </select>
                            {!hasTeachers && subjectSelected && (
                                <div className="error-text">No teachers available for this subject.</div>
                            )}
                        </div>

                        {/* ROOM */}
                        <div className="form-group">
                            <label>{isPractical ? "Lab Room" : "Classroom"}</label>
                            <select
                                value={modifiedSlot.room || ''}
                                onChange={(e) => handleFieldChange('room', e.target.value)}
                            >
                                <option value="">Select Room...</option>
                                {/* Combine simple strings or object names if robust */}
                                {rooms.map(r => {
                                    const rName = typeof r === 'string' ? r : r.name;
                                    return <option key={rName} value={rName}>{rName}</option>;
                                })}
                            </select>
                        </div>
                    </div>

                    {/* CONFLICTS */}
                    <div className="validation-section">
                        {validating && <div className="spinner-mini"></div>}
                        <ConflictPanel conflicts={conflicts} />

                        {conflicts.length > 0 && (
                            <div className="autofix-wrapper">
                                <AutoFixButton
                                    slot={modifiedSlot}
                                    conflicts={conflicts}
                                    timetable={timetable}
                                    context={context}
                                    onFixApplied={handleAutoFixApplied}
                                />
                            </div>
                        )}
                    </div>
                </div>

                {/* FOOTER */}
                <div className="card-footer">
                    <div className="status-indicator">
                        {isValid ?
                            <span className="status-valid">✔ Valid</span> :
                            <span className="status-invalid">Invalid Configuration</span>
                        }
                    </div>
                    <div className="actions">
                        <button className="btn-secondary" onClick={onClose}>Cancel</button>
                        <button
                            className="btn-primary"
                            onClick={handleSave}
                            disabled={!isValid || validating}
                        >
                            Save Changes
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default EditSlotModal;
