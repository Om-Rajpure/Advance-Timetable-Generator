import React, { useState } from 'react';
import { findAutoFix } from '../utils/autoFixer';
import './AutoFixButton.css';

function AutoFixButton({ slot, conflicts, timetable, context, onFixApplied }) {
    const [loading, setLoading] = useState(false);
    const [suggestion, setSuggestion] = useState(null);
    const [error, setError] = useState(null);

    const handleAutoFix = () => {
        setLoading(true);
        setSuggestion(null);
        setError(null);

        // Small delay to show "Finding..." state
        setTimeout(() => {
            const fix = findAutoFix(slot, timetable, context?.branchData);

            if (fix) {
                setSuggestion(fix);
            } else {
                setError("No available slot found. Please adjust manually.");
            }
            setLoading(false);
        }, 600);
    };

    const applyFix = () => {
        if (suggestion) {
            const fixedSlot = { ...slot, day: suggestion.day, slot: suggestion.slot };
            onFixApplied(fixedSlot);
            setSuggestion(null);
        }
    };

    return (
        <div className="auto-fix-container">
            <button
                className="auto-fix-button"
                onClick={handleAutoFix}
                disabled={loading || !conflicts || conflicts.length === 0}
            >
                {loading ? '🔄 Finding Fix...' : '🔧 Fix Automatically'}
            </button>

            {suggestion && (
                <div className="fix-suggestion">
                    <p className="success-msg">✅ Moved to {suggestion.day} Slot {suggestion.slot}. No clashes.</p>
                    <button className="apply-fix-button" onClick={applyFix}>
                        Apply Fix
                    </button>
                </div>
            )}

            {error && (
                <div className="fix-suggestion">
                    <p className="error-msg">❌ {error}</p>
                </div>
            )}
        </div>
    );
}

export default AutoFixButton;
