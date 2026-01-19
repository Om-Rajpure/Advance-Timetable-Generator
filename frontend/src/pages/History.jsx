import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import VersionList from '../components/VersionList';
import HistoryEmptyState from '../components/HistoryEmptyState';
import { API_BASE_URL } from '../config'; // Import config
import { useAuth } from '../auth/AuthContext'; // Import Auth
import { useDashboardState } from '../hooks/useDashboardState';
import './ModulePage.css';

function History() {
    const { token } = useAuth(); // Get token
    const navigate = useNavigate();
    const { getBranchInfo } = useDashboardState();
    const branchInfo = getBranchInfo();
    const branchData = { name: branchInfo.name, years: branchInfo.years }; // Minimal context wrapper

    const [versions, setVersions] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchVersions();
    }, [token]);

    const fetchVersions = async () => {
        setLoading(true);
        try {
            // Use NEW secure endpoint
            const response = await fetch(`${API_BASE_URL}/api/timetables/my`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            const data = await response.json();

            // Map SQL data to UI format expected by VersionList
            if (response.ok) {
                const mappedVersions = data.map(t => ({
                    versionId: t.id, // Use DB ID
                    timestamp: t.createdAt,
                    action: 'Generated', // Default label
                    description: `Academic Year: ${t.academicYear}`,
                    metadata: { // Mock metadata to fit component
                        qualityScore: 100,
                        constraints: 0
                    }
                }));
                setVersions(mappedVersions);
            } else {
                console.error('Failed to fetch versions:', data.error);
            }
        } catch (error) {
            console.error('Error fetching versions:', error);
        } finally {
            setLoading(false);
        }
    };

    const fetchFullVersion = async (id) => {
        try {
            // Use NEW details endpoint
            const response = await fetch(`${API_BASE_URL}/api/timetables/${id}`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            const data = await response.json();

            if (response.ok) {
                // Transform entries back to grid format if needed
                // For now, returning the raw structure; might need adapter if VersionList expects grid
                // Actually EditableTimetable expects specific structure. 
                // We will reconstruction "timetableSnapshot" from "entries"

                const entries = data.entries || [];
                // Format: { "Monday": [ { ...slot... } ] }
                // Warning: Grid expects full structure.
                // We'll pass the entries and let the component handle or rebuild.

                // Quick rebuild:
                const timetable = {};
                entries.forEach(e => {
                    if (!timetable[e.day]) timetable[e.day] = [];
                    timetable[e.day].push({
                        slotIndex: e.slotIndex,
                        subject: e.subject,
                        teacher: e.teacher,
                        batch: e.batch,
                        room: e.room
                    });
                });

                return { timetableSnapshot: timetable }; // Mimic old structure
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

    // Branch check removed to allow viewing history even without active branch selection
    // or we can show a warning banner instead of blocking
    if (!branchInfo.exists) {
        // Optional: You can keep a check here if strictly required, but for "History" 
        // it makes sense to see past work even if current session has no branch selected.
        // We will just proceed.
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
                        branchName="My Workspace"
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
