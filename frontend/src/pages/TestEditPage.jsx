import React from 'react';
import { useNavigate } from 'react-router-dom';
import './TestEditPage.css';

function TestEditPage() {
    const navigate = useNavigate();

    const sampleTimetable = [
        {
            id: "mon_0_se_a",
            day: "Monday",
            slot: 0,
            year: "SE",
            division: "A",
            subject: "Machine Learning",
            teacher: "Neha",
            room: "Room-1",
            type: "Lecture"
        },
        {
            id: "mon_1_se_a",
            day: "Monday",
            slot: 1,
            year: "SE",
            division: "A",
            subject: "AI",
            teacher: "John",
            room: "Room-2",
            type: "Lecture"
        },
        {
            id: "tue_0_se_a",
            day: "Tuesday",
            slot: 0,
            year: "SE",
            division: "A",
            subject: "DBMS",
            teacher: "Sarah",
            room: "Room-1",
            type: "Lecture"
        },
        {
            id: "wed_0_se_a",
            day: "Wednesday",
            slot: 0,
            year: "SE",
            division: "A",
            subject: "Machine Learning",
            teacher: "Neha",
            room: "Room-2",
            type: "Lecture"
        }
    ];

    const context = {
        branchData: {
            academicYears: ["SE"],
            divisions: { SE: ["A"] },
            slotsPerDay: 6,
            rooms: ["Room-1", "Room-2", "Room-3"],
            labs: ["Lab-1", "Lab-2", "Lab-3"]
        },
        smartInputData: {
            subjects: [
                { name: "Machine Learning", year: "SE", division: "A", lecturesPerWeek: 2 },
                { name: "AI", year: "SE", division: "A", lecturesPerWeek: 2 },
                { name: "DBMS", year: "SE", division: "A", lecturesPerWeek: 2 }
            ],
            teachers: [
                { name: "Neha", subjects: ["Machine Learning"] },
                { name: "John", subjects: ["AI"] },
                { name: "Sarah", subjects: ["DBMS"] },
                { name: "David", subjects: [] }
            ]
        }
    };

    const handleNavigateToEdit = () => {
        navigate('/edit-timetable', {
            state: {
                timetable: sampleTimetable,
                context: context,
                qualityScore: 78.5
            }
        });
    };

    return (
        <div className="test-edit-page">
            <div className="test-container">
                <h1>🧪 Test Editable Timetable</h1>
                <p>Click the button below to test the editing interface with sample data</p>

                <div className="sample-info">
                    <h3>Sample Data:</h3>
                    <ul>
                        <li>✅ 4 lecture slots</li>
                        <li>✅ 3 subjects (ML, AI, DBMS)</li>
                        <li>✅ 4 teachers (Neha, John, Sarah, David)</li>
                        <li>✅ 3 rooms + 3 labs</li>
                        <li>✅ Quality Score: 78.5/100</li>
                    </ul>
                </div>

                <button className="test-button" onClick={handleNavigateToEdit}>
                    🚀 Open Editable Timetable
                </button>

                <div className="test-instructions">
                    <h3>What to Test:</h3>
                    <ol>
                        <li>Click any slot in the grid to edit</li>
                        <li>Try changing teacher/room/subject</li>
                        <li>See real-time validation</li>
                        <li>Try creating a conflict (assign busy teacher)</li>
                        <li>Click "Auto-Fix" button</li>
                        <li>Use Undo button</li>
                        <li>Try to Save</li>
                    </ol>
                </div>
            </div>
        </div>
    );
}

export default TestEditPage;
