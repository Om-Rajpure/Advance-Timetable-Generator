import React from 'react';
import VersionCard from './VersionCard';
import './VersionList.css';

function VersionList({ versions, stats, onVersionSelect, onRestore, selectedVersionId }) {
    return (
        <div className="version-list">
            {stats && (
                <div className="version-list__stats">
                    <div className="stat-item">
                        <span className="stat-item__label">Total Versions</span>
                        <span className="stat-item__value">{stats.totalVersions}</span>
                    </div>
                    <div className="stat-item">
                        <span className="stat-item__label">Latest Quality</span>
                        <span className="stat-item__value">{stats.latestQuality}%</span>
                    </div>
                    <div className="stat-item">
                        <span className="stat-item__label">Average Quality</span>
                        <span className="stat-item__value">{stats.averageQuality}%</span>
                    </div>
                </div>
            )}

            {versions && versions.length > 0 ? (
                <div className="version-list__timeline">
                    {versions.map((version) => (
                        <VersionCard
                            key={version.versionId}
                            version={version}
                            onSelect={() => onVersionSelect(version)}
                            onRestore={() => onRestore(version)}
                            isSelected={version.versionId === selectedVersionId}
                        />
                    ))}
                </div>
            ) : (
                <div className="version-list__empty">
                    <div className="version-list__empty-icon">📜</div>
                    <div className="version-list__empty-text">No Version History</div>
                    <div className="version-list__empty-hint">
                        Generate or save a timetable to create your first version
                    </div>
                </div>
            )}
        </div>
    );
}

export default VersionList;
