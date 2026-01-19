import React, { useState, useEffect } from 'react';
import { API_BASE_URL } from '../../config';
import { useAuth } from '../../auth/AuthContext';

const AdminUsers = () => {
    const { token, user } = useAuth();
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);

    const [editingUser, setEditingUser] = useState(null);
    const [showModal, setShowModal] = useState(false);

    const fetchUsers = async () => {
        try {
            const res = await fetch(`${API_BASE_URL}/api/admin/users`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                setUsers(await res.json());
            }
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchUsers();
    }, [token]);

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
        setEditingUser({ ...targetUser }); // Copy to avoid direct mutation
        setShowModal(true);
    };

    // Handler for Save Edit
    const handleSaveUser = async () => {
        if (!editingUser) return;

        try {
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
        <div className="admin-page">
            <div className="page-header">
                <h2>User Management</h2>
                <button className="refresh-btn" onClick={fetchUsers}>Refresh</button>
            </div>

            <div className="table-container">
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
                                <td>#{u.id}</td>
                                <td>
                                    <div className="user-cell">
                                        <div className="avatar-sm">{u.username[0].toUpperCase()}</div>
                                        <span>{u.username}</span>
                                    </div>
                                </td>
                                <td><span className={`role-badge ${u.role}`}>{u.role}</span></td>
                                <td>{new Date(u.created_at || u.createdAt).toLocaleDateString()}</td>
                                <td>
                                    <button
                                        className="action-btn edit"
                                        onClick={() => handleEditClick(u)}
                                    >
                                        Edit
                                    </button>
                                    <button
                                        className="action-btn delete"
                                        onClick={() => handleDeleteUser(u.id)}
                                        disabled={user && u.id === user.id}
                                    >
                                        Delete
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
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

export default AdminUsers;
