import React from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import './AdminLayout.css';

const AdminLayout = () => {
    const { logout, user } = useAuth();
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate('/');
    };

    return (
        <div className="admin-application">
            {/* Sidebar */}
            <aside className="admin-sidebar">
                <div className="admin-brand">
                    <span className="icon">🛡️</span>
                    <h2>Admin<span className="accent">Panel</span></h2>
                </div>

                <div className="admin-user-info">
                    <div className="avatar">OM</div>
                    <div className="details">
                        <span className="name">{user?.username || 'Admin'}</span>
                        <span className="role">Administrator</span>
                    </div>
                </div>

                <nav className="admin-nav">
                    <NavLink to="/admin" end className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
                        <span className="icon">📊</span> Dashboard
                    </NavLink>
                    <NavLink to="/admin/users" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
                        <span className="icon">👥</span> Users
                    </NavLink>
                    <NavLink to="/admin/timetables" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
                        <span className="icon">📅</span> Timetables
                    </NavLink>
                    <NavLink to="/admin/system" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
                        <span className="icon">⚙️</span> System
                    </NavLink>
                </nav>

                <div className="admin-footer">
                    <button onClick={handleLogout} className="logout-btn">
                        <span className="icon">🚪</span> Logout
                    </button>
                </div>
            </aside>

            {/* Main Content Area */}
            <main className="admin-main">
                <header className="admin-topbar">
                    <h2 className="page-title">Database Management</h2>
                    <div className="topbar-actions">
                        <span className="status-badge live">● Live Database</span>
                    </div>
                </header>
                <div className="content-scrollable">
                    <Outlet />
                </div>
            </main>
        </div>
    );
};

export default AdminLayout;
