import React from 'react';
import { useNavigate } from 'react-router-dom';

const HistoryEmptyState = () => {
    const navigate = useNavigate();

    return (
        <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '60px 20px',
            textAlign: 'center',
            backgroundColor: 'white',
            borderRadius: '12px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
            minHeight: '400px'
        }}>
            <div style={{
                fontSize: '64px',
                marginBottom: '24px',
                opacity: '0.8'
            }}>
                📭
            </div>

            <h2 style={{
                fontSize: '24px',
                fontWeight: '600',
                color: '#111827',
                marginBottom: '12px'
            }}>
                No timetables generated yet.
            </h2>

            <p style={{
                fontSize: '16px',
                color: '#6b7280',
                marginBottom: '32px',
                maxWidth: '400px'
            }}>
                Your generated timetables will appear here safely. Create your first one now!
            </p>

            <button
                onClick={() => navigate('/branch/setup')}
                style={{
                    backgroundColor: '#4f46e5',
                    color: 'white',
                    padding: '12px 24px',
                    borderRadius: '8px',
                    border: 'none',
                    fontSize: '16px',
                    fontWeight: '500',
                    cursor: 'pointer',
                    boxShadow: '0 4px 6px -1px rgba(79, 70, 229, 0.2)',
                    transition: 'all 0.2s',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                }}
                onMouseOver={(e) => e.currentTarget.style.transform = 'translateY(-1px)'}
                onMouseOut={(e) => e.currentTarget.style.transform = 'translateY(0)'}
            >
                <span>🚀</span>
                Generate New Timetable
            </button>
        </div>
    );
};

export default HistoryEmptyState;
