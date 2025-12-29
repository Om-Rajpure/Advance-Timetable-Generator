import React, { useState, useEffect } from 'react';
import VersionList from '../components/VersionList';
import RestoreDialog from '../components/RestoreDialog';
import './ModulePage.css';

function History() {
    const [versions, setVersions] = useState([]);
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [selectedVersion, setSelectedVersion] = useState(null);
    const [restoreVersion, setRestoreVersion] = useState(null);
    const [actionFilter, setActionFilter] = useState('');

    // Get current branch and context from localStorage or state management
    const branchId = localStorage.getItem('currentBranchId');
    const context = {
        branchData: JSON.parse(localStorage.getItem('currentBranchData') || '{}'),
        smartInputData: JSON.parse(localStorage.getItem('currentSmartInputData') || '{}')
    };

    useEffect(() => {
        if (branchId) {
            fetchVersions();
        } else {
            setLoading(false);
        }
    }, [branchId, actionFilter]);

    const fetchVersions = async () => {
        setLoading(true);
        try {
            const url = new URL('http://localhost:5000/api/history/versions');
            url.searchParams.append('branchId', branchId);
            if (actionFilter) {
                url.searchParams.append('action', actionFilter);
            }

            const response = await fetch(url);
            const data = await response.json();

            if (data.success) {
                setVersions(data.versions || []);
                setStats(data.stats || null);
            } else {
                console.error('Failed to fetch versions:', data.error);
            }
        } catch (error) {
            console.error('Error fetching versions:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleVersionSelect = (version) => {
        setSelectedVersion(version);
    };

    const handleRestoreClick = (version) => {
        setRestoreVersion(version);
    };

    const handleRestoreConfirm = async (timetable) => {
        // In a real implementation, you would:
        // 1. Update the timetable state in your app
        // 2. Navigate to the editable timetable page
        // 3. Show success message

        alert('Timetable restored successfully! Navigate to Edit Timetable to view.');
        setRestoreVersion(null);

        // Refresh versions list
        fetchVersions();
    };

    const handleRestoreCancel = () => {
        setRestoreVersion(null);
    };

    if (!branchId) {
        return (
            <div className="module-page">
                <div className="module-header">
                    <h1 className="module-title">📜 Timetable History</h1>
                    <p className="module-description">
                        View, restore, and compare previous timetable versions
                    </p>
                </div>

                <div className="module-content">
                    <div className="info-card">
                        <h3>No Branch Selected</h3>
                        <p>Please select or create a branch first to view version history.</p>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="module-page">
            <div className="module-header">
                <h1 className="module-title">📜 Timetable History</h1>
                <p className="module-description">
                    View, restore, and compare previous timetable versions
                </p>
            </div>

            <div className="module-content">
                <div style={{ marginBottom: '20px', display: 'flex', gap: '15px', alignItems: 'center' }}>
                    <label style={{ fontSize: '14px', fontWeight: '500' }}>
                        Filter by Action:
                    </label>
                    <select
                        value={actionFilter}
                        onChange={(e) => setActionFilter(e.target.value)}
                        style={{
                            padding: '8px 12px',
                            border: '1px solid #d1d5db',
                            borderRadius: '6px',
                            fontSize: '14px'
                        }}
                    >
                        <option value="">All Actions</option>
                        <option value="Generation">Generation</option>
                        <option value="Optimization">Optimization</option>
                        <option value="Manual Edit">Manual Edit</option>
                        <option value="Simulation Applied">Simulation Applied</option>
                        <option value="Restore">Restore</option>
                    </select>
                    <button
                        onClick={fetchVersions}
                        style={{
                            padding: '8px 16px',
                            background: '#6366f1',
                            color: 'white',
                            border: 'none',
                            borderRadius: '6px',
                            cursor: 'pointer',
                            fontSize: '14px',
                            fontWeight: '500'
                        }}
                    >
                        🔄 Refresh
                    </button>
                </div>

                {loading ? (
                    <div style={{ textAlign: 'center', padding: '60px', color: '#6b7280' }}>
                        <div style={{ fontSize: '48px', marginBottom: '16px' }}>⏳</div>
                        <div>Loading version history...</div>
                    </div>
                ) : (
                    <VersionList
                        versions={versions}
                        stats={stats}
                        onVersionSelect={handleVersionSelect}
                        onRestore={handleRestoreClick}
                        selectedVersionId={selectedVersion?.versionId}
                    />
                )}
            </div>

            {restoreVersion && (
                <RestoreDialog
                    version={restoreVersion}
                    branchId={branchId}
                    context={context}
                    onConfirm={handleRestoreConfirm}
                    onCancel={handleRestoreCancel}
                />
            )}
        </div>
    );
}

export default History;
