import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import VersionList from '../components/VersionList';
import HistoryEmptyState from '../components/HistoryEmptyState';
import './ModulePage.css';

function History() {
    const navigate = useNavigate();
    const [versions, setVersions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [branchName, setBranchName] = useState('');

    // Get current branch from localStorage
    const branchId = localStorage.getItem('currentBranchId');
    const branchData = JSON.parse(localStorage.getItem('currentBranchData') || '{}');

    useEffect(() => {
        if (branchData && branchData.branchName) {
            setBranchName(branchData.branchName);
        }
    }, [branchData]);

    useEffect(() => {
        if (branchId) {
            fetchVersions();
        } else {
            setLoading(false);
        }
    }, [branchId]);

    const fetchVersions = async () => {
        setLoading(true);
        try {
            const url = new URL('/api/history/versions', window.location.origin);
            url.searchParams.append('branchId', branchId);
            const response = await fetch(url);
            const data = await response.json();

            if (data.success) {
                setVersions(data.versions || []);
            } else {
                console.error('Failed to fetch versions:', data.error);
            }
        } catch (error) {
            console.error('Error fetching versions:', error);
        } finally {
            setLoading(false);
        }
    };

    const fetchFullVersion = async (versionId) => {
        try {
            const response = await fetch(`/api/history/version/${versionId}?branchId=${branchId}`);
            const data = await response.json();
            if (data.success) {
                return data.version;
            } else {
                alert('Failed to load version details.');
                return null;
            }
        } catch (error) {
            console.error('Error fetching full version:', error);
            alert('Error loading version.');
            return null;
        }
    };

    const handleView = async (version) => {
        const fullVersion = await fetchFullVersion(version.versionId);
        if (fullVersion) {
            navigate('/timetable', {
                state: {
                    timetable: fullVersion.timetableSnapshot,
                    readOnly: true,
                    context: { branchData } // Pass basic context
                }
            });
        }
    };

    const handleEdit = async (version) => {
        const fullVersion = await fetchFullVersion(version.versionId);
        if (fullVersion) {
            navigate('/timetable', {
                state: {
                    timetable: fullVersion.timetableSnapshot,
                    readOnly: false,
                    context: { branchData } // Context needed for editing
                }
            });
        }
    };

    const handleDuplicate = async (version) => {
        const fullVersion = await fetchFullVersion(version.versionId);
        if (fullVersion) {
            navigate('/timetable', {
                state: {
                    timetable: fullVersion.timetableSnapshot,
                    readOnly: false,
                    isDuplicate: true, // Marker for potential UI logic
                    context: { branchData }
                }
            });
        }
    };

    if (!branchId) {
        return (
            <div className="module-page">
                <div className="module-header">
                    <h1 className="module-title">History</h1>
                    <p className="module-description">Your previously generated timetables</p>
                </div>
                <div className="module-content">
                    <div className="info-card">
                        <h3>No Branch Selected</h3>
                        <p>Please select a branch from the Dashboard.</p>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="module-page">
            <div className="module-header">
                <h1 className="module-title">History</h1>
                <p className="module-description">
                    Your previously generated timetables
                </p>
            </div>

            <div className="module-content">
                {loading ? (
                    <div style={{ textAlign: 'center', padding: '60px', color: '#6b7280' }}>
                        <div style={{ fontSize: '48px', marginBottom: '16px', animation: 'pulse 2s infinite' }}>⏳</div>
                        <div>Loading your history...</div>
                    </div>
                ) : versions.length > 0 ? (
                    <VersionList
                        versions={versions}
                        branchName={branchName}
                        onView={handleView}
                        onEdit={handleEdit}
                        onDuplicate={handleDuplicate}
                    />
                ) : (
                    <HistoryEmptyState />
                )}
            </div>
        </div>
    );
}

export default History;
