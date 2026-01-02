import React from 'react';
import './Timetable.css';

/**
 * Renders a single cell content (Lecture or Lab Batches)
 */
const TimetableCell = ({ entries, isRecess }) => {
    if (isRecess) {
        return <div className="tt-cell-recess">☕ RECESS</div>;
    }

    if (!entries || entries.length === 0) {
        return <div className="tt-cell-empty"></div>;
    }

    // Check if it's a Lab (Multiple entries or type='Practical')
    const isLab = entries.some(e => e.isPractical || e.type === 'Practical' || e.type === 'LAB');

    // Color generator
    const getColor = (str) => {
        let hash = 0;
        for (let i = 0; i < str.length; i++) hash = str.charCodeAt(i) + ((hash << 5) - hash);
        const c = (hash & 0x00FFFFFF).toString(16).toUpperCase();
        return '#' + '00000'.substring(0, 6 - c.length) + c;
    }

    // Light pastel background generator
    const getPastelColor = (str) => {
        const hash = str.split('').reduce((acc, char) => char.charCodeAt(0) + acc, 0);
        const hue = hash % 360;
        return `hsl(${hue}, 70%, 95%)`; // Very light background
    }

    const getBorderColor = (str) => {
        const hash = str.split('').reduce((acc, char) => char.charCodeAt(0) + acc, 0);
        const hue = hash % 360;
        return `hsl(${hue}, 60%, 80%)`; // Slightly darker border
    }

    if (isLab) {
        return (
            <div className="tt-cell-lab-container">
                {entries.map((entry, idx) => (
                    <div
                        key={idx}
                        className="tt-sub-batch-card"
                        style={{
                            backgroundColor: getPastelColor(entry.subject || ''),
                            borderColor: getBorderColor(entry.subject || '')
                        }}
                    >
                        <div className="tt-batch-badge">{entry.batch}</div>
                        <div className="tt-subject-name small">{entry.subject}</div>
                        <div className="tt-room-name small">📍 {entry.room}</div>
                        <div className="tt-teacher-name tiny">Unknown Teacher</div> {/* Teacher missing in some payloads? */}
                        {/* entry.teacher ?? 'Staff' */}
                        <div className="tt-teacher-name tiny">👨‍🏫 {entry.teacher || 'Staff'}</div>
                    </div>
                ))}
            </div>
        )
    }

    // Single Theory Lecture
    const entry = entries[0];
    return (
        <div
            className="tt-cell-theory-card"
            style={{
                backgroundColor: getPastelColor(entry.subject || ''),
                borderLeft: `4px solid ${getBorderColor(entry.subject || '')}`
            }}
        >
            <div className="tt-subject-name">{entry.subject}</div>
            <div className="tt-teacher-name">👨‍🏫 {entry.teacher}</div>
            <div className="tt-room-badge">📍 {entry.room || 'CR'}</div>
        </div>
    );
};

export default TimetableCell;
