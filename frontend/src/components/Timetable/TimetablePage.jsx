import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import TimetableGrid from './TimetableGrid';
import { transformToGrid } from '../../utils/timetableTransforms';
import './Timetable.css';

const TimetablePage = () => {
    const location = useLocation();
    const navigate = useNavigate();

    // 1. Data Retrieval (Dual Channel)
    const [rawTimetable, setRawTimetable] = useState([]);
    const [branchConfig, setBranchConfig] = useState({});
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // 2. View State
    const [selectedYear, setSelectedYear] = useState('');
    const [selectedDivision, setSelectedDivision] = useState('');
    const [gridData, setGridData] = useState({});
    const [availableYears, setAvailableYears] = useState([]);
    const [availableDivisions, setAvailableDivisions] = useState([]);

    useEffect(() => {
        try {
            // Priority 1: Navigation State (Fastest)
            let loadedTimetable = location.state?.timetable;
            let loadedContext = location.state?.context;

            // Priority 2: LocalStorage (Persistence)
            if (!loadedTimetable) {
                const storedTimetable = localStorage.getItem('generatedTimetable');
                if (storedTimetable) loadedTimetable = JSON.parse(storedTimetable);
            }

            if (!loadedContext) {
                const branchConfStr = localStorage.getItem('branchConfig');
                if (branchConfStr) loadedContext = JSON.parse(branchConfStr);
            }


            if (loadedTimetable && (Array.isArray(loadedTimetable) || typeof loadedTimetable === 'object')) {
                setRawTimetable(loadedTimetable);
                setBranchConfig(loadedContext || {});

                // Initialize View Options
                let years = [];
                let isCanonical = false;

                if (Array.isArray(loadedTimetable)) {
                    years = [...new Set(loadedTimetable.map(item => item.year))].sort();
                } else {
                    const keys = Object.keys(loadedTimetable);
                    // Check if keys are "Year-Div"
                    if (keys.some(k => k.includes('-'))) {
                        isCanonical = true;
                        const uniqueYears = new Set(keys.map(k => k.split('-')[0]));
                        years = [...uniqueYears].sort();
                    } else {
                        years = keys.sort();
                    }
                }

                setAvailableYears(years);
                if (years.length > 0) {
                    const firstYear = years[0];
                    setSelectedYear(firstYear);

                    // Divisions for first year
                    let divs = [];
                    if (Array.isArray(loadedTimetable)) {
                        divs = [...new Set(loadedTimetable.filter(t => t.year === firstYear).map(t => t.division))].sort();
                    } else if (isCanonical) {
                        // Filter keys starting with firstYear + "-"
                        const keys = Object.keys(loadedTimetable);
                        const relevantKeys = keys.filter(k => k.startsWith(firstYear + '-'));
                        divs = relevantKeys.map(k => k.split('-')[1]).sort();
                    } else {
                        divs = Object.keys(loadedTimetable[firstYear] || {}).sort();
                    }

                    setAvailableDivisions(divs);
                    if (divs.length > 0) setSelectedDivision(divs[0]);
                }
            } else {
                setError("No timetable data found. Please generate one first.");
            }
        } catch (err) {
            console.error("Timetable Load Error:", err);
            setError("Failed to load timetable data.");
        } finally {
            setLoading(false);
        }
    }, [location.state]); // Run once on mount

    // 3. Transformation Effect
    useEffect(() => {
        if (rawTimetable) { // Just check truthy, transform handles both
            const transformed = transformToGrid(rawTimetable, branchConfig);
            setGridData(transformed);
        }
    }, [rawTimetable, branchConfig]);

    // 4. Update Divisions when Year changes
    const handleYearChange = (year) => {
        console.log("Selected Year Changed:", year);
        setSelectedYear(year);

        let divs = [];

        // Detect Canonical (Object with "Year-Div" keys)
        const isCanonical = !Array.isArray(rawTimetable) && Object.keys(rawTimetable).some(k => k.includes('-'));

        if (Array.isArray(rawTimetable)) {
            divs = [...new Set(rawTimetable.filter(t => t.year === year).map(t => t.division))].sort();
        } else if (isCanonical) {
            const keys = Object.keys(rawTimetable);
            const relevantKeys = keys.filter(k => k.startsWith(year + '-'));
            divs = relevantKeys.map(k => k.split('-')[1]).sort();
        } else {
            // Legacy Nested Object
            divs = Object.keys(rawTimetable[year] || {}).sort();
        }

        console.log("Available Divisions for Year:", divs);
        setAvailableDivisions(divs);
        if (divs.length > 0) setSelectedDivision(divs[0]);
        else setSelectedDivision('');
    };


    // Render Helpers
    if (loading) return <div className="tt-loading-container">Loading Timetable...</div>;

    if (error) {
        return (
            <div className="tt-page-container">
                <div className="tt-permission-denied">
                    <h2>⚠️ {error}</h2>
                    <p>Debug Info:</p>
                    <small>Storage: {localStorage.getItem('generatedTimetable') ? 'Present' : 'Empty'}</small>
                    <br />
                    <button className="btn-download" onClick={() => navigate('/smart-input')} style={{ marginTop: 20 }}>
                        Go to Generator
                    </button>
                </div>
            </div>
        )
    }

    const currentGrid = (gridData[selectedYear] && gridData[selectedYear][selectedDivision])
        ? gridData[selectedYear][selectedDivision]
        : {};

    return (
        <div className="tt-page-container">
            {/* Header */}
            <div className="tt-header-section">
                <div className="tt-title">
                    <h1>Academic Timetable {new Date().getFullYear()}</h1>
                    <div className="tt-subtitle">Generated via Smart Scheduler AI</div>
                </div>

                <div className="tt-controls">
                    {/* Year Selector */}
                    <select
                        className="tt-select"
                        value={selectedYear}
                        onChange={(e) => handleYearChange(e.target.value)}
                    >
                        {availableYears.map(y => <option key={y} value={y}>{y}</option>)}
                    </select>

                    {/* Division Selector */}
                    <select
                        className="tt-select"
                        value={selectedDivision}
                        onChange={(e) => setSelectedDivision(e.target.value)}
                    >
                        {availableDivisions.map(d => <option key={d} value={d}>Division {d}</option>)}
                    </select>

                    <div style={{ width: 20 }}></div>

                    <button className="btn-download" onClick={() => window.print()}>
                        🖨️ Print / PDF
                    </button>

                    <button className="btn-download" onClick={() => navigate('/edit-timetable')}>
                        ✏️ Edit Data
                    </button>
                </div>
            </div>

            {/* Grid */}
            <TimetableGrid
                gridData={currentGrid}
                year={selectedYear}
                division={selectedDivision}
                branchData={branchConfig}
            />

        </div>
    );
};

export default TimetablePage;
