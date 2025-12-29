import React, { useEffect } from 'react';
import './UndoControls.css';

function UndoControls({ canUndo, canRedo, onUndo, onRedo, onReset, onSave, hasChanges, isValid, isSaving }) {
    useEffect(() => {
        const handleKeyDown = (e) => {
            // Ctrl+Z for Undo
            if (e.ctrlKey && e.key === 'z' && !e.shiftKey && canUndo) {
                e.preventDefault();
                onUndo();
            }
            // Ctrl+Y or Ctrl+Shift+Z for Redo
            if ((e.ctrlKey && e.key === 'y') || (e.ctrlKey && e.shiftKey && e.key === 'z')) {
                if (canRedo && onRedo) {
                    e.preventDefault();
                    onRedo();
                }
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [canUndo, canRedo, onUndo, onRedo]);

    return (
        <div className="undo-controls">
            <button
                className="control-button undo"
                onClick={onUndo}
                disabled={!canUndo}
                title="Undo last change (Ctrl+Z)"
            >
                ↶ Undo
            </button>

            {onRedo && (
                <button
                    className="control-button redo"
                    onClick={onRedo}
                    disabled={!canRedo}
                    title="Redo last undone change (Ctrl+Y)"
                >
                    ↷ Redo
                </button>
            )}

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
