import React, { useState } from 'react';
import { getSuggestedFix } from '../utils/autoFixer';
import './AutoFixButton.css';

function AutoFixButton({ slot, conflicts, timetable, context, onFixApplied }) {
    const [loading, setLoading] = useState(false);
    const [suggestion, setSuggestion] = useState(null);

    const handleAutoFix = async () => {
        setLoading(true);
        try {
            const fix = await getSuggestedFix(slot, conflicts, timetable, context);
            setSuggestion(fix);
        } catch (error) {
            console.error('Auto-fix failed:', error);
        } finally {
            setLoading(false);
        }
    };

    const applyFix = () => {
        if (suggestion && suggestion.fix) {
            onFixApplied(suggestion.fix);
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
                {loading ? '🔄 Finding Fix...' : '🔧 Auto-Fix'}
            </button>

            {suggestion && (
                <div className="fix-suggestion">
                    <div className="fix-explanation">
                        {suggestion.fix ? (
                            <>
                                <p>✅ {suggestion.explanation}</p>
                                <button className="apply-fix-button" onClick={applyFix}>
                                    Apply Fix
                                </button>
                            </>
                        ) : (
                            <p>❌ {suggestion.explanation}</p>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}

export default AutoFixButton;
