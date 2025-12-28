import React from 'react';
import './ConflictPanel.css';

function ConflictPanel({ conflicts }) {
    if (!conflicts || conflicts.length === 0) {
        return null;
    }

    return (
        <div className="conflict-panel">
            <h4>⚠️ Conflicts Detected</h4>
            {conflicts.map((conflict, index) => (
                <div
                    key={index}
                    className={`conflict-item ${conflict.severity?.toLowerCase() || 'soft'}`}
                >
                    <div className="conflict-icon">
                        {conflict.severity === 'HARD' ? '❌' : '⚠️'}
                    </div>
                    <div className="conflict-details">
                        <div className="conflict-rule">{conflict.constraint || 'Constraint Violation'}</div>
                        <div className="conflict-message">{conflict.message}</div>
                        {conflict.affectedSlots && conflict.affectedSlots.length > 0 && (
                            <div className="conflict-affected">
                                Affects: {conflict.affectedSlots.join(', ')}
                            </div>
                        )}
                    </div>
                </div>
            ))}
        </div>
    );
}

export default ConflictPanel;
