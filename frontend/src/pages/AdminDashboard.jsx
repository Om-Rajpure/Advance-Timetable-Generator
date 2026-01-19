import React, { useState, useEffect } from 'react';
import { useAuth } from '../auth/AuthContext';
import { API_BASE_URL } from '../config';
import { useNavigate } from 'react-router-dom';
import MainNavbar from '../components/MainNavbar';
import './AdminDashboard.css'; // We'll create this simple CSS

const AdminDashboard = () => {
    const { user, token } = useAuth();
    const navigate = useNavigate();
    const [users, setUsers] = useState([]);
    const [timetables, setTimetables] = useState([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('users');
    const [error, setError] = useState(null);

    useEffect(() => {
        if (user && user.role !== 'admin') {
            navigate('/dashboard');
            return;
        }

        const fetchData = async () => {
            try {
                setLoading(true);
                const headers = {
                    'Authorization': `Bearer ${token}`
                };

                // Fetch Users
                const usersRes = await fetch(`${API_BASE_URL}/api/admin/users`, { headers });
                if (!usersRes.ok) throw new Error('Failed to fetch users');
                const usersData = await usersRes.json();
                setUsers(usersData);

                // Fetch Timetables
                const timetablesRes = await fetch(`${API_BASE_URL}/api/admin/timetables`, { headers });
                if (!timetablesRes.ok) throw new Error('Failed to fetch timetables');
                const timetablesData = await timetablesRes.json();
                setTimetables(timetablesData);

            } catch (err) {
                console.error(err);
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        if (token) {
            fetchData();
        }
    }, [user, token, navigate]);

    if (loading) return <div className="admin-loading">Loading Admin Panel...</div>;
    if (error) return <div className="admin-error">Error: {error}</div>;

    const [editingUser, setEditingUser] = useState(null);
    const [showModal, setShowModal] = useState(false);

    // Handler for Delete
    const handleDeleteUser = async (userId) => {
        if (!window.confirm('Are you sure you want to delete this user? This action cannot be undone.')) return;

        try {
            const response = await fetch(`${API_BASE_URL}/api/admin/users/${userId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                setUsers(users.filter(u => u.id !== userId));
            } else {
                const data = await response.json();
                alert(data.error || 'Failed to delete user');
            }
        } catch (err) {
            console.error(err);
            alert('Failed to delete user');
        }
    };

    // Handler for Edit Click
    const handleEditClick = (targetUser) => {
        console.log("Edit clicked for:", targetUser);
        setEditingUser({ ...targetUser }); // Copy to avoid direct mutation
        setShowModal(true);
    };

    // Handler for Save Edit
    const handleSaveUser = async () => {
        if (!editingUser) return;

        try {
            console.log("Saving user:", editingUser);
            const response = await fetch(`${API_BASE_URL}/api/admin/users/${editingUser.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    username: editingUser.username,
                    role: editingUser.role
                })
            });

            if (response.ok) {
                const updatedUser = await response.json();
                setUsers(users.map(u => u.id === updatedUser.id ? updatedUser : u));
                setShowModal(false);
                setEditingUser(null);
            } else {
                const data = await response.json();
                alert(data.error || 'Failed to update user');
            }
        } catch (err) {
            console.error(err);
            alert('Failed to update user');
        }
    };

    return (
        <div className="admin-dashboard">
            <div className="admin-header">
                <h1>🛡️ Admin Panel</h1>
                <div className="admin-stats">
                    <div className="stat-card">
                        <h3>Total Users</h3>
                        <p>{users.length}</p>
                    </div>
                    <div className="stat-card">
                        <h3>Total Timetables</h3>
                        <p>{timetables.length}</p>
                    </div>
                </div>
            </div>

            <div className="admin-tabs">
                <button
                    className={activeTab === 'users' ? 'active' : ''}
                    onClick={() => setActiveTab('users')}
                >
                    Users
                </button>
                <button
                    className={activeTab === 'timetables' ? 'active' : ''}
                    onClick={() => setActiveTab('timetables')}
                >
                    Timetables
                </button>
            </div>

            <div className="admin-content">
                {activeTab === 'users' && (
                    <table className="admin-table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Username</th>
                                <th>Role</th>
                                <th>Created At</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {users.map(u => (
                                <tr key={u.id}>
                                    <td>{u.id}</td>
                                    <td>{u.username}</td>
                                    <td>
                                        <span className={`role-badge ${u.role}`}>{u.role}</span>
                                    </td>
                                    <td>{new Date(u.created_at || u.createdAt).toLocaleString()}</td>
                                    <td>
                                        <button
                                            className="btn-action edit"
                                            onClick={() => handleEditClick(u)}
                                            title="Edit User"
                                        >
                                            Edit
                                        </button>
                                        <button
                                            className="btn-action delete"
                                            onClick={() => handleDeleteUser(u.id)}
                                            disabled={u.role === 'admin' && user && u.id === user.id}
                                            title="Delete User"
                                        >
                                            Delete
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}

                {activeTab === 'timetables' && (
                    <table className="admin-table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>User ID</th>
                                <th>Year</th>
                                <th>Status</th>
                                <th>Created At</th>
                            </tr>
                        </thead>
                        <tbody>
                            {timetables.map(t => (
                                <tr key={t.id}>
                                    <td>{t.id}</td>
                                    <td>{t.userId}</td>
                                    <td>{t.academicYear}</td>
                                    <td>{t.status}</td>
                                    <td>{new Date(t.createdAt).toLocaleString()}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>

            {/* Edit User Modal */}
            {showModal && editingUser && (
                <div className="modal-overlay">
                    <div className="modal-content">
                        <h2>Edit User</h2>
                        <div className="form-group">
                            <label>Username</label>
                            <input
                                type="text"
                                value={editingUser.username}
                                onChange={(e) => setEditingUser({ ...editingUser, username: e.target.value })}
                            />
                        </div>
                        <div className="form-group">
                            <label>Role</label>
                            <select
                                value={editingUser.role}
                                onChange={(e) => setEditingUser({ ...editingUser, role: e.target.value })}
                            >
                                <option value="user">User</option>
                                <option value="faculty">Faculty</option>
                                <option value="admin">Admin</option>
                            </select>
                        </div>
                        <div className="modal-actions">
                            <button onClick={() => setShowModal(false)} className="btn-cancel">Cancel</button>
                            <button onClick={handleSaveUser} className="btn-save">Save Changes</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default AdminDashboard;
