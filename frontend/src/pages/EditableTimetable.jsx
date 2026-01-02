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
    // State from generation/validation or localStorage
    const getInitialTimetable = () => {
        if (location.state?.timetable) return location.state.timetable;
        const stored = localStorage.getItem('generatedTimetable');
        return stored ? JSON.parse(stored) : [];
    };

    const getInitialContext = () => {
        if (location.state?.context) return location.state.context;
        // Ideally context should also be stored or rebuilt. 
        // For now, let's assume we can survive without full context or load it if we had stored it.
        // SmartInput saves payload parts? 
        // Let's rely on stored 'branchConfig' for context reconstruction if needed.
        const branchConfig = localStorage.getItem('branchConfig');
        return branchConfig ? { branchData: JSON.parse(branchConfig) } : {};
    };


    const initialTimetable = getInitialTimetable();
    const initialContext = getInitialContext();
    const initialScore = location.state?.qualityScore || null;

    // Timetable state
    const [timetable, setTimetable] = useState(initialTimetable);
    const [savedTimetable, setSavedTimetable] = useState(initialTimetable);
    const [undoStack, setUndoStack] = useState([]);
    const [redoStack, setRedoStack] = useState([]);

    // UI state
    const [editingSlot, setEditingSlot] = useState(null);
    const [conflictingSlots, setConflictingSlots] = useState([]);
    const [qualityScore, setQualityScore] = useState(initialScore);
    const [scoreDelta, setScoreDelta] = useState(0);
    const [isSaving, setIsSaving] = useState(false);

    const context = initialContext;
    const hasChanges = JSON.stringify(timetable) !== JSON.stringify(savedTimetable);
    const canUndo = undoStack.length > 0;
    const canRedo = redoStack.length > 0;

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

        // Clear redo stack when new edit is made
        setRedoStack([]);

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

            // Add current state to redo stack
            setRedoStack(prev => [...prev, timetable]);

            setTimetable(previousState);
            setUndoStack(prev => prev.slice(0, -1));
            computeQualityScore(previousState);
        }
    };

    const handleRedo = () => {
        if (canRedo) {
            const nextState = redoStack[redoStack.length - 1];

            // Add current state to undo stack
            setUndoStack(prev => [...prev, timetable]);

            setTimetable(nextState);
            setRedoStack(prev => prev.slice(0, -1));
            computeQualityScore(nextState);
        }
    };

    const handleReset = () => {
        if (window.confirm('Reset to last saved version? All unsaved changes will be lost.')) {
            setTimetable(savedTimetable);
            setUndoStack([]);
            setRedoStack([]);
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
                    <div style={{ marginTop: '20px', padding: '10px', background: '#f5f5f5', borderRadius: '5px', fontSize: '12px', textAlign: 'left' }}>
                        <strong>Debug Info:</strong><br />
                        Location State: {location.state ? 'Present' : 'None'}<br />
                        LocalStorage 'generatedTimetable': {localStorage.getItem('generatedTimetable') ? 'Found' : 'Empty'}
                    </div>
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
                canRedo={canRedo}
                onUndo={handleUndo}
                onRedo={handleRedo}
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
