import React from 'react';
import VersionCard from './VersionCard';
import './VersionList.css';

function VersionList({ versions, onView, onEdit, onDuplicate, branchName }) {
    if (!versions || versions.length === 0) {
        return null;
    }

    return (
        <div className="version-list-container">
            <div className="version-grid">
                {versions.map((version) => (
                    <VersionCard
                        key={version.versionId}
                        version={version}
                        branchName={branchName}
                        onView={onView}
                        onEdit={onEdit}
                        onDuplicate={onDuplicate}
                    />
                ))}
            </div>
        </div>
    );
}

export default VersionList;
