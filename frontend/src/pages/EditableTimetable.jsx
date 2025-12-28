import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import TimetableGrid from '../components/TimetableGrid';
import EditSlotModal from '../components/EditSlotModal';
import QualityBadge from '../components/QualityBadge';
import UndoControls from '../components/UndoControls';
import { saveTimetable } from '../utils/editValidator';
import './EditableTimetable.css';

function EditableTimetable() {
    const location = useLocation();

    // State from generation/validation
    const initialTimetable = location.state?.timetable || [];
    const initialContext = location.state?.context || {};
    const initialScore = location.state?.qualityScore || null;

    // Timetable state
    const [timetable, setTimetable] = useState(initialTimetable);
    const [savedTimetable, setSavedTimetable] = useState(initialTimetable);
    const [undoStack, setUndoStack] = useState([]);

    // UI state
    const [editingSlot, setEditingSlot] = useState(null);
    const [conflictingSlots, setConflictingSlots] = useState([]);
    const [qualityScore, setQualityScore] = useState(initialScore);
    const [scoreDelta, setScoreDelta] = useState(0);
    const [isSaving, setIsSaving] = useState(false);

    const context = initialContext;
    const hasChanges = JSON.stringify(timetable) !== JSON.stringify(savedTimetable);
    const canUndo = undoStack.length > 0;

    useEffect(() => {
        // Compute initial quality score if not provided
        if (!qualityScore && timetable.length > 0) {
            computeQualityScore(timetable);
        }
    }, []);

    const computeQualityScore = async (tt) => {
        try {
            const response = await fetch('http://localhost:5000/api/validate/quick', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    timetable: tt,
                    ...context
                })
            });

            if (response.ok) {
                const result = await response.json();
                const newScore = result.score || 0;
                const oldScore = qualityScore || newScore;
                setQualityScore(newScore);
                setScoreDelta(newScore - oldScore);
            }
        } catch (error) {
            console.error('Failed to compute quality score:', error);
        }
    };

    const handleSlotClick = (slot) => {
        setEditingSlot(slot);
    };

    const handleSlotSave = (modifiedSlot) => {
        // Add current state to undo stack
        setUndoStack(prev => [...prev, timetable]);

        // Update timetable
        const updatedTimetable = timetable.map(s =>
            s.id === modifiedSlot.id ? modifiedSlot : s
        );

        setTimetable(updatedTimetable);

        // Recompute quality score
        computeQualityScore(updatedTimetable);
    };

    const handleUndo = () => {
        if (canUndo) {
            const previousState = undoStack[undoStack.length - 1];
            setTimetable(previousState);
            setUndoStack(prev => prev.slice(0, -1));
            computeQualityScore(previousState);
        }
    };

    const handleReset = () => {
        if (window.confirm('Reset to last saved version? All unsaved changes will be lost.')) {
            setTimetable(savedTimetable);
            setUndoStack([]);
            computeQualityScore(savedTimetable);
        }
    };

    const handleSave = async () => {
        setIsSaving(true);
        try {
            const result = await saveTimetable(timetable, context);
            if (result.success) {
                setSavedTimetable(timetable);
                setUndoStack([]);
                alert('✅ Timetable saved successfully!');
            } else {
                alert('❌ Failed to save: ' + result.message);
            }
        } catch (error) {
            alert('❌ Error saving timetable: ' + error.message);
        } finally {
            setIsSaving(false);
        }
    };

    if (!timetable || timetable.length === 0) {
        return (
            <div className="editable-timetable">
                <div className="empty-state">
                    <h2>No Timetable Loaded</h2>
                    <p>Please generate or upload a timetable first.</p>
                </div>
            </div>
        );
    }

    return (
        <div className="editable-timetable">
            <div className="page-header">
                <div>
                    <h1>Edit Timetable</h1>
                    <p>Click any slot to edit. Changes are validated in real-time.</p>
                </div>
                {qualityScore !== null && (
                    <QualityBadge score={qualityScore} delta={scoreDelta} />
                )}
            </div>

            <UndoControls
                canUndo={canUndo}
                onUndo={handleUndo}
                onReset={handleReset}
                onSave={handleSave}
                hasChanges={hasChanges}
                isValid={conflictingSlots.length === 0}
                isSaving={isSaving}
            />

            <TimetableGrid
                timetable={timetable}
                conflictingSlots={conflictingSlots}
                onSlotClick={handleSlotClick}
            />

            {editingSlot && (
                <EditSlotModal
                    slot={editingSlot}
                    timetable={timetable}
                    context={context}
                    onSave={handleSlotSave}
                    onClose={() => setEditingSlot(null)}
                />
            )}
        </div>
    );
}

export default EditableTimetable;
