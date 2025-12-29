import React from 'react';
import QualityBadge from './QualityBadge';
import './VersionCard.css';

function VersionCard({ version, onSelect, onRestore, isSelected }) {
    const badgeColorClass = version.actionBadge?.color || 'gray';

    return (
        <div
            className={`version-card ${isSelected ? 'selected' : ''}`}
            onClick={onSelect}
        >
            <div className="version-card__header">
                <div className="version-card__left">
                    <div className="version-card__id">{version.versionId}</div>
                    <div className="version-card__time">{version.timestampFormatted}</div>
                </div>
                <div className={`version-card__badge ${badgeColorClass}`}>
                    <span>{version.actionBadge?.icon || '📝'}</span>
                    <span>{version.action}</span>
                </div>
            </div>

            <div className="version-card__description">
                {version.description}
            </div>

            <div className="version-card__footer">
                <div className="version-card__meta">
                    <div className="version-card__meta-item">
                        <span>⭐</span>
                        <span>{version.qualityLevel} ({version.qualityScore}%)</span>
                    </div>
                    {version.metadata?.slotCount && (
                        <div className="version-card__meta-item">
                            <span>📋</span>
                            <span>{version.metadata.slotCount} slots</span>
                        </div>
                    )}
                    <div className="version-card__meta-item">
                        <span>👤</span>
                        <span>{version.createdBy}</span>
                    </div>
                </div>

                <div className="version-card__actions">
                    <button
                        className="version-card__btn version-card__btn--primary"
                        onClick={(e) => {
                            e.stopPropagation();
                            onRestore();
                        }}
                    >
                        Restore
                    </button>
                </div>
            </div>
        </div>
    );
}

export default VersionCard;
