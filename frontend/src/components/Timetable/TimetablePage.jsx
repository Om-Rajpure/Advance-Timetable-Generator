import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import TimetableGrid from './TimetableGrid';
import { transformToGrid } from '../../utils/timetableTransforms';
import './Timetable.css';

// --- DEBUG DATA ---
const DEBUG_DATA = {
    "SE-A": {
        "Monday": [
            { id: "d1", slot: 1, subject: "DEBUG-THEORY", type: "THEORY", teacher: "TESTER", room: "101" },
            { id: "d2", slot: 2, subject: "DEBUG-LAB", type: "LAB", teacher: "TESTER", room: "LAB-A", batch: "B1" }
        ],
        "Tuesday": [
            { id: "d3", slot: 1, subject: "DEBUG-SUB", type: "THEORY", teacher: "TESTER", room: "101" }
        ]
    },
    "SE-B": {
        "Monday": [{ id: "d4", slot: 1, subject: "DEBUG-B", type: "THEORY", teacher: "TESTER", room: "102" }]
    }
};

const TimetablePage = () => {
    const location = useLocation();
    const navigate = useNavigate();

    // 1. Data Retrieval (Dual Channel)
    const [rawTimetable, setRawTimetable] = useState([]);
    const [branchConfig, setBranchConfig] = useState({});
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // DEBUG: Top Level Render Trace
    console.log(`🧩 [TimetablePage] RENDER. Loading=${loading}, RawTimetableType=${typeof rawTimetable}, IsArray=${Array.isArray(rawTimetable)}, Keys=${rawTimetable ? Object.keys(rawTimetable).length : 0}`);
    console.log("  > Location State:", location.state);

    // 2. View State
    const [selectedYear, setSelectedYear] = useState('');
    const [selectedDivision, setSelectedDivision] = useState('');
    const [gridData, setGridData] = useState({});
    const [availableYears, setAvailableYears] = useState([]);
    const [availableDivisions, setAvailableDivisions] = useState([]);

    // Debug: Log rawTimetable changes
    useEffect(() => {
        if (rawTimetable) {
            console.log("🧩 [TimetablePage] State 'rawTimetable' updated:", typeof rawTimetable, Array.isArray(rawTimetable));
            console.log("🧩 [TimetablePage] Keys:", Object.keys(rawTimetable));
        }
    }, [rawTimetable]);

    useEffect(() => {
        console.log("🧩 [TimetablePage] MOUNT Check Location:", location);

        const fetchData = async () => {
            try {
                // Priority 1: Navigation State (Fastest)
                let loadedTimetable = location.state?.timetable;
                let loadedContext = location.state?.context;

                // Priority 2: LocalStorage (Persistence)
                if (!loadedTimetable) {
                    const storedTimetable = localStorage.getItem('generatedTimetable');
                    if (storedTimetable) {
                        try {
                            loadedTimetable = JSON.parse(storedTimetable);
                            console.log("🧩 [TimetablePage] Loaded from Storage");
                        } catch (e) {
                            console.error("Storage Parse Error", e);
                        }
                    }
                }

                if (!loadedContext) {
                    const branchConfStr = localStorage.getItem('branchConfig');
                    if (branchConfStr) loadedContext = JSON.parse(branchConfStr);
                }

                if (loadedTimetable && (Array.isArray(loadedTimetable) || typeof loadedTimetable === 'object')) {
                    console.log("🧩 [TimetablePage] Data Retrieval: Setting rawTimetable", loadedTimetable);

                    // CRITICAL FIX: Deep Clone to avoid Proxy/Reference issues
                    const cleanData = JSON.parse(JSON.stringify(loadedTimetable));
                    setRawTimetable(cleanData);

                    setBranchConfig(loadedContext || {});

                    // Initialize View Options
                    let years = [];
                    let isCanonical = false;
                    const keys = Array.isArray(cleanData) ? [] : Object.keys(cleanData);

                    if (Array.isArray(cleanData)) {
                        years = [...new Set(cleanData.map(item => item.year))].sort();
                    } else {
                        // Check if keys are "Year-Div"
                        if (keys.some(k => k.includes('-'))) {
                            isCanonical = true;
                            const uniqueYears = new Set(keys.map(k => k.split('-')[0]));
                            years = [...uniqueYears].sort();
                        } else {
                            years = keys.sort();
                        }
                    }

                    console.log("🧩 [TimetablePage] Parsed Years:", years);
                    setAvailableYears(years);

                    if (years.length > 0) {
                        const firstYear = years[0];
                        setSelectedYear(firstYear);

                        // Divisions for first year
                        let divs = [];
                        if (Array.isArray(cleanData)) {
                            divs = [...new Set(cleanData.filter(t => t.year === firstYear).map(t => t.division))].sort();
                        } else if (isCanonical) {
                            // Filter keys starting with firstYear + "-"
                            const relevantKeys = keys.filter(k => k.startsWith(firstYear + '-'));
                            divs = relevantKeys.map(k => k.split('-')[1]).sort();
                        } else {
                            divs = Object.keys(cleanData[firstYear] || {}).sort();
                        }

                        console.log("🧩 [TimetablePage] Parsed Divisions:", divs);
                        setAvailableDivisions(divs);
                        if (divs.length > 0) setSelectedDivision(divs[0]);
                    }
                } else {
                    console.warn("⚠️ [TimetablePage] No Valid Timetable Data Found");
                    setError("No timetable data found. Please generate one first.");
                }
            } catch (err) {
                console.error("Timetable Load Error:", err);
                setError("Failed to load timetable data.");
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [location.state]); // Run once on mount

    // 3. Transformation Effect
    useEffect(() => {
        console.log("🧩 [TimetablePage] Transformation Effect Triggered");
        if (rawTimetable && Object.keys(rawTimetable).length > 0) {

            // NORMALIZE DATA STRUCTURE
            // Backend now sends: { Year: { Division: { timetable: { Day: [...] } } } }
            // Expected Grid: { Year: { Division: { Day: [...] } } }

            const normalized = {};

            Object.keys(rawTimetable).forEach(yearKey => {
                // If value is object and has divisions
                if (typeof rawTimetable[yearKey] === 'object' && !Array.isArray(rawTimetable[yearKey])) {
                    normalized[yearKey] = {};

                    Object.keys(rawTimetable[yearKey]).forEach(divKey => {
                        const divData = rawTimetable[yearKey][divKey];

                        // Unwrap 'timetable' key if present
                        if (divData && divData.timetable) {
                            normalized[yearKey][divKey] = divData.timetable;
                        } else {
                            // Already in correct format or raw array?
                            normalized[yearKey][divKey] = divData;
                        }
                    });
                } else {
                    // Fallback for flat structure or array
                    // Use transformToGrid for legacy support if needed, but for now assuming new structure
                    normalized[yearKey] = rawTimetable[yearKey];
                }
            });

            console.log("  > Normalized Grid Data:", Object.keys(normalized));
            setGridData(normalized);
        }
    }, [rawTimetable]);

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


    // Render Logic
    const currentGrid = (gridData[selectedYear] && gridData[selectedYear][selectedDivision])
        ? gridData[selectedYear][selectedDivision]
        : {};

    const renderMainContent = () => {
        if (loading) return <div className="tt-loading-container">Loading Timetable...</div>;

        if (error) {
            return (
                <div className="tt-permission-denied">
                    <h2>⚠️ {error}</h2>
                    <p>Debug Info:</p>
                    <small>Storage: {localStorage.getItem('generatedTimetable') ? 'Present' : 'Empty'}</small>
                    <br />
                    <button className="btn-download" onClick={() => navigate('/smart-input')} style={{ marginTop: 20 }}>
                        Go to Generator
                    </button>
                </div>
            );
        }

        return (
            <>
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

                {/* ⚠️ SYSTEM NOTIFICATION BANNER ⚠️ */}
                {/* Display if there are structural failures or validation warnings passed from generator */}
                {(location.state?.failures || (location.state?.validationErrors && location.state.validationErrors.length > 0)) && (
                    <div className="tt-warning-banner" style={{
                        background: '#fff3cd',
                        color: '#856404',
                        border: '1px solid #ffeeba',
                        padding: '15px',
                        margin: '20px 40px',
                        borderRadius: '8px',
                        fontSize: '14px'
                    }}>
                        <h4 style={{ margin: '0 0 10px 0', display: 'flex', alignItems: 'center' }}>
                            ⚠️ Generation Completeness Report
                        </h4>

                        {/* 1. Structural Failures (Missing Divisions) */}
                        {location.state.failures && Object.keys(location.state.failures).length > 0 && (
                            <div style={{ marginBottom: '10px' }}>
                                <strong>❌ Failed to Generate:</strong>
                                <ul style={{ margin: '5px 0', paddingLeft: '20px' }}>
                                    {Object.entries(location.state.failures).map(([cls, reason]) => (
                                        <li key={cls}>
                                            <b>{cls}</b>: {reason}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        {/* 2. Validation Warnings (Soft Errors) */}
                        {location.state.validationErrors && location.state.validationErrors.length > 0 && (
                            <div>
                                <strong>🔸 Validation Issues (Timetable Generated with Warnings):</strong>
                                <ul style={{ margin: '5px 0', paddingLeft: '20px' }}>
                                    {location.state.validationErrors.map((err, idx) => (
                                        <li key={idx}>
                                            <b>{err.division}</b>: {err.reason} {err.details ? `- ${err.details}` : ''}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        <div style={{ marginTop: '10px', fontSize: '12px', opacity: 0.8 }}>
                            Tip: You can manually fix these issues in the "Edit Data" mode.
                        </div>
                    </div>
                )}

                {/* Grid */}
                <TimetableGrid
                    gridData={currentGrid}
                    year={selectedYear}
                    division={selectedDivision}
                    branchData={branchConfig}
                />
            </>
        );
    };

    return (
        <div className="tt-page-container">
            {/* DEBUG PANEL - ALWAYS VISIBLE */}
            <div style={{
                position: 'fixed',
                top: 0,
                left: 0,
                width: '100%',
                zIndex: 99999,
                background: '#fffcd7',
                borderBottom: '2px solid #e6b800',
                padding: '10px',
                fontSize: '12px',
                fontFamily: 'monospace',
                maxHeight: '200px',
                overflowY: 'auto',
                boxShadow: '0 2px 10px rgba(0,0,0,0.2)'
            }}>
                <div style={{ marginBottom: '5px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <h3 style={{ margin: '0' }}>🔍 ALPHA OMEGA DEBUG</h3>
                    <button
                        onClick={() => {
                            console.log("🛠️ FORCING DUMMY DATA");
                            setRawTimetable(DEBUG_DATA);
                            setError(null); // Clear error if any
                            setLoading(false); // Ensure loading is off

                            // Initialize Views manually for Debug Data
                            setSelectedYear("SE");
                            setSelectedDivision("A");
                            setAvailableYears(["SE"]);
                            setAvailableDivisions(["A", "B"]);
                        }}
                        style={{ background: 'red', color: 'white', border: 'none', padding: '5px 10px', cursor: 'pointer', fontWeight: 'bold' }}
                    >
                        🛠️ FORCE DUMMY DATA
                    </button>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                    <div>
                        <p style={{ margin: '2px 0' }}><strong>Selected Year:</strong> "{selectedYear}"</p>
                        <p style={{ margin: '2px 0' }}><strong>Selected Division:</strong> "{selectedDivision}"</p>
                        <p style={{ margin: '2px 0' }}><strong>Current Grid Keys:</strong> {Object.keys(currentGrid).join(', ')}</p>
                    </div>
                    <div>
                        <p style={{ margin: '2px 0' }}><strong>Raw Keys:</strong> {rawTimetable ? Object.keys(rawTimetable || {}).length : 0}</p>
                        <p style={{ margin: '2px 0' }}><strong>Grid Data Years:</strong> {Object.keys(gridData).join(', ')}</p>
                        <p style={{ margin: '2px 0' }}><strong>Divs for "{selectedYear}":</strong> {gridData[selectedYear] ? Object.keys(gridData[selectedYear]).join(', ') : 'None'}</p>
                    </div>
                </div>
                <details>
                    <summary>Raw Data Sample</summary>
                    <pre>{JSON.stringify((rawTimetable && (Array.isArray(rawTimetable) ? rawTimetable[0] : Object.values(rawTimetable)[0])) || {}, null, 2)}</pre>
                </details>
            </div>

            {/* Main Content Rendered Below Debug Panel */}
            <div style={{ marginTop: '160px' }}>
                {renderMainContent()}
            </div>
        </div>
    );
};

export default TimetablePage;
