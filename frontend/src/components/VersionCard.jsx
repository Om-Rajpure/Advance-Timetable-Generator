import React from 'react';
import './VersionCard.css';

function VersionCard({ version, branchName, onView, onEdit, onDuplicate }) {

    // Parse timestamp for friendly display
    const dateObj = new Date(version.timestamp);
    const dateStr = dateObj.toLocaleDateString('en-US', { day: 'numeric', month: 'long', year: 'numeric' });
    const timeStr = dateObj.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });

    // Determine status and style based on action
    const getStatus = (action) => {
        const actionLower = action?.toLowerCase() || '';
        if (actionLower.includes('edit')) return { label: 'Edited', class: 'edited', icon: '✏️' };
        if (actionLower.includes('generation')) return { label: 'Generated', class: 'generated', icon: '✨' };
        if (actionLower.includes('simulation')) return { label: 'Simulation', class: 'draft', icon: '🔬' };
        if (actionLower.includes('restore')) return { label: 'Restored', class: 'draft', icon: '🔄' };
        return { label: 'Saved', class: 'draft', icon: '💾' };
    };

    const status = getStatus(version.action);

    // Format classes list nicely
    const classes = version.metadata?.divisions
        ? version.metadata.divisions.map(d => `Div ${d}`).join(', ')
        : 'All Classes';

    // Format branch nicely
    const displayBranch = branchName || 'General';

    return (
        <div className="version-card">
            <div className="version-card__header">
                <div className="version-card__time-group">
                    <div className="version-card__date">{dateStr}</div>
                    <div className="version-card__time">{timeStr}</div>
                </div>
                <div className={`version-card__status version-card__status--${status.class}`}>
                    <span>{status.icon}</span>
                    <span>{status.label}</span>
                </div>
            </div>

            <div className="version-card__details">
                <div className="version-card__detail-row">
                    <span className="version-card__icon">🏫</span>
                    <div className="version-card__detail-text">
                        <span className="version-card__detail-label">{displayBranch}</span>
                    </div>
                </div>
                <div className="version-card__detail-row">
                    <span className="version-card__icon">📘</span>
                    <div className="version-card__detail-text classes-list" title={classes}>
                        {classes}
                    </div>
                </div>
            </div>

            <div className="version-card__actions">
                <button
                    className="version-card__btn version-card__btn--view"
                    onClick={() => onView(version)}
                    title="View as Read-Only"
                >
                    <span>👁️</span> View
                </button>
                <button
                    className="version-card__btn version-card__btn--edit"
                    onClick={() => onEdit(version)}
                    title="Edit this version"
                >
                    <span>✏️</span> Edit
                </button>
                <button
                    className="version-card__btn version-card__btn--duplicate"
                    onClick={() => onDuplicate(version)}
                    title="Create a copy"
                >
                    <span>📄</span> Duplicate
                </button>
            </div>
        </div>
    );
}

export default VersionCard;
