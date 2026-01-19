import React, { useState, useEffect } from 'react';
import { API_BASE_URL } from '../../config';
import { useAuth } from '../../auth/AuthContext';

const AdminTimetables = () => {
    const { token } = useAuth();
    const [timetables, setTimetables] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchTimetables = async () => {
            try {
                const res = await fetch(`${API_BASE_URL}/api/admin/timetables`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (res.ok) {
                    setTimetables(await res.json());
                }
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchTimetables();
    }, [token]);

    return (
        <div className="admin-page">
            <div className="page-header">
                <h2>Generated Timetables</h2>
            </div>

            <div className="table-container">
                <table className="admin-table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Owner ID</th>
                            <th>Academic Year</th>
                            <th>Status</th>
                            <th>Created At</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {timetables.map(t => (
                            <tr key={t.id}>
                                <td>#{t.id}</td>
                                <td>User #{t.userId}</td>
                                <td>{t.academicYear}</td>
                                <td><span className="status-pill success">{t.status}</span></td>
                                <td>{new Date(t.createdAt).toLocaleString()}</td>
                                <td>
                                    <button className="action-btn">Inspect</button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default AdminTimetables;
