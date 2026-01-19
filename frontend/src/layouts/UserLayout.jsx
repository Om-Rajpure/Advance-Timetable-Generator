import React from 'react';
import { Outlet } from 'react-router-dom';
import MainNavbar from '../components/MainNavbar';

const UserLayout = () => {
    return (
        <div className="user-application">
            <MainNavbar />
            <main className="user-content">
                <Outlet />
            </main>
        </div>
    );
};

export default UserLayout;
