import React from 'react';
import './UndoControls.css';

function UndoControls({ canUndo, onUndo, onReset, onSave, hasChanges, isValid, isSaving }) {
    return (
        <div className="undo-controls">
            <button
                className="control-button undo"
                onClick={onUndo}
                disabled={!canUndo}
                title="Undo last change"
            >
                ↶ Undo
            </button>

            <button
                className="control-button reset"
                onClick={onReset}
                disabled={!hasChanges}
                title="Reset to last saved state"
            >
                ⟲ Reset
            </button>

            <button
                className="control-button save primary"
                onClick={onSave}
                disabled={!hasChanges || !isValid || isSaving}
                title={!isValid ? 'Fix conflicts before saving' : 'Save timetable'}
            >
                {isSaving ? '💾 Saving...' : '💾 Save Timetable'}
            </button>

            {!isValid && hasChanges && (
                <span className="validation-warning">
                    ⚠️ Fix conflicts before saving
                </span>
            )}
        </div>
    );
}

export default UndoControls;
