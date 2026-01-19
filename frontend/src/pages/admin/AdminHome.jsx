import React, { useState, useEffect } from 'react';
import { API_BASE_URL } from '../../config';
import { useAuth } from '../../auth/AuthContext';
import './AdminPages.css';

const AdminHome = () => {
    const { token } = useAuth();
    const [stats, setStats] = useState({ users: 0, timetables: 0 });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const headers = { 'Authorization': `Bearer ${token}` };
                const usersRes = await fetch(`${API_BASE_URL}/api/admin/users`, { headers });
                const timetablesRes = await fetch(`${API_BASE_URL}/api/admin/timetables`, { headers });

                if (usersRes.ok && timetablesRes.ok) {
                    const users = await usersRes.json();
                    const timetables = await timetablesRes.json();
                    setStats({ users: users.length, timetables: timetables.length });
                }
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchStats();
    }, [token]);

    return (
        <div className="admin-page">
            <div className="stats-grid">
                <div className="stat-card">
                    <div className="icon-wrapper blue">👥</div>
                    <div className="stat-info">
                        <h3>Total Users</h3>
                        <p className="value">{loading ? '-' : stats.users}</p>
                    </div>
                </div>
                <div className="stat-card">
                    <div className="icon-wrapper green">📅</div>
                    <div className="stat-info">
                        <h3>Total Timetables</h3>
                        <p className="value">{loading ? '-' : stats.timetables}</p>
                    </div>
                </div>
                <div className="stat-card">
                    <div className="icon-wrapper purple">⚡</div>
                    <div className="stat-info">
                        <h3>System Status</h3>
                        <p className="value text-sm">Operational</p>
                    </div>
                </div>
            </div>

            <div className="welcome-section">
                <h3>Welcome to Control Center</h3>
                <p>Select a module from the sidebar to manage the database.</p>
            </div>
        </div>
    );
};

export default AdminHome;
