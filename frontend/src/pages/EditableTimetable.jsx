import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import TimetableGrid from '../components/TimetableGrid';
import EditSlotModal from '../components/EditSlotModal';
import UndoControls from '../components/UndoControls';
import { detectAllConflicts } from '../utils/conflictDetector';
import { transformToGrid } from '../utils/timetableTransforms';
import { generateFullTimetablePDF } from '../utils/pdfGenerator';
import './EditableTimetable.css';

function EditableTimetable() {
    const location = useLocation();

    // 1. Initialize State
    const [timetable, setTimetable] = useState(location.state?.timetable || []);
    const [conflicts, setConflicts] = useState(location.state?.conflicts || []);
    const [context, setContext] = useState(location.state?.context || {});

    // Undo/Redo
    const [undoStack, setUndoStack] = useState([]);
    const [redoStack, setRedoStack] = useState([]);

    // UI State
    const [editingSlot, setEditingSlot] = useState(null);
    const [selectedYear, setSelectedYear] = useState(null);
    const [selectedDiv, setSelectedDiv] = useState(null);

    // 1.5 Load from Storage if missing (Persistence Fix)
    useEffect(() => {
        if (timetable.length === 0) {
            const storedTimetable = localStorage.getItem('generatedTimetable');
            const storedStats = localStorage.getItem('generationStats'); // Optional stats

            if (storedTimetable) {
                try {
                    const parsedData = JSON.parse(storedTimetable);
                    console.log("🔄 Loaded Timetable from LocalStorage:", parsedData.length, "slots");
                    setTimetable(parsedData);

                    // Also try to restore context
                    if (!context.branchData) {
                        const savedBranch = localStorage.getItem('branchConfig');
                        const savedSmartInput = localStorage.getItem('smartInputData');
                        if (savedBranch || savedSmartInput) {
                            setContext(prev => ({
                                ...prev,
                                branchData: savedBranch ? JSON.parse(savedBranch) : {},
                                smartInputData: savedSmartInput ? JSON.parse(savedSmartInput) : {}
                            }));
                        }
                    }
                } catch (e) {
                    console.error("Failed to load timetable from storage", e);
                }
            }
        }
    }, []); // Run once on mount

    // 2. Build Inferred Context (if missing)
    useEffect(() => {
        if (!context.inferred && (context.smartInputData || context.branchData)) return;

        // Extract unique resources from timetable for dropdowns
        const uniqueTeachers = new Set();
        const uniqueSubjects = new Set();
        const uniqueRooms = new Set();
        const uniqueLabs = new Set();

        timetable.forEach(slot => {
            if (slot.teacher) uniqueTeachers.add(slot.teacher);
            if (slot.subject) uniqueSubjects.add(slot.subject);
            if (slot.room) uniqueRooms.add(slot.room);
            if (slot.type === 'Practical' && slot.room) uniqueLabs.add(slot.room);
        });

        const newContext = {
            inferred: true,
            smartInputData: {
                teachers: Array.from(uniqueTeachers).map(name => ({ name, subjects: [] })),
                subjects: Array.from(uniqueSubjects).map(name => ({ name, lecturesPerWeek: 3 })) // Dummy
            },
            branchData: {
                rooms: Array.from(uniqueRooms),
                labs: Array.from(uniqueLabs),
                years: [], // Will get from grid
                divisions: [] // Will get from grid
            }
        };
        setContext(newContext);
    }, []); // Run once on mount if needed

    // 3. Transform to View Grid
    const fullGrid = transformToGrid(timetable, context.branchData || {});
    const availableYears = Object.keys(fullGrid);

    // Auto-select view
    useEffect(() => {
        if (availableYears.length > 0 && !selectedYear) {
            setSelectedYear(availableYears[0]);
        }
        if (selectedYear && fullGrid[selectedYear]) {
            const divs = Object.keys(fullGrid[selectedYear]);
            if (divs.length > 0 && !selectedDiv) {
                setSelectedDiv(divs[0]);
            }
        }
    }, [fullGrid, selectedYear, selectedDiv]);

    // 4. Handle Edit
    const handleSlotClick = (slot) => {
        setEditingSlot(slot);
    };

    const handleSlotSave = (modifiedSlot) => {
        // Validation check (Real-time in Modal already, but double check)

        // Save for Undo
        setUndoStack(prev => [...prev, timetable]);
        setRedoStack([]);

        // Update Timetable
        const updatedTimetable = timetable.map(s =>
            s.id === modifiedSlot.id ? modifiedSlot : s
        );

        // Run Real-time Conflict Detection
        const conflictResult = detectAllConflicts(updatedTimetable, context.branchData, context.smartInputData);

        setTimetable(updatedTimetable);
        setConflicts(conflictResult.conflicts);
        setEditingSlot(null); // Close modal
    };

    const handleUndo = () => {
        if (undoStack.length === 0) return;
        const prev = undoStack[undoStack.length - 1];
        setRedoStack(prevStack => [...prevStack, timetable]);
        setTimetable(prev);
        setUndoStack(prevStack => prevStack.slice(0, -1));

        // Re-detect conflicts for restored state
        const conflictResult = detectAllConflicts(prev, context.branchData, context.smartInputData);
        setConflicts(conflictResult.conflicts);
    };

    const handleRedo = () => {
        if (redoStack.length === 0) return;
        const next = redoStack[redoStack.length - 1];
        setUndoStack(prevStack => [...prevStack, timetable]);
        setTimetable(next);
        setRedoStack(prevStack => prevStack.slice(0, -1));

        // Re-detect conflicts
        const conflictResult = detectAllConflicts(next, context.branchData, context.smartInputData);
        setConflicts(conflictResult.conflicts);
    };

    // Filter conflicts for simple ID list for the grid
    const conflictingSlotIds = conflicts.map(c => c.affectedSlots).flat();

    // Get current view data
    const viewData = (selectedYear && selectedDiv && fullGrid[selectedYear])
        ? fullGrid[selectedYear][selectedDiv]
        : {};

    const availableDivs = selectedYear && fullGrid[selectedYear] ? Object.keys(fullGrid[selectedYear]) : [];

    return (
        <div className="editable-timetable">
            {/* SIDEBAR NAVIGATION */}
            <div className="sidebar">
                <div className="sidebar-header">
                    <div className="sidebar-brand">SmartTimetable</div>
                </div>

                <div className="class-list">
                    {availableYears.map(year => (
                        <div key={year} className="year-group">
                            <div className="year-label">{year} Engineering</div>
                            <div className="division-list">
                                {fullGrid[year] && Object.keys(fullGrid[year]).map(div => (
                                    <div
                                        key={div}
                                        className={`nav-item ${selectedYear === year && selectedDiv === div ? 'active' : ''}`}
                                        onClick={() => {
                                            setSelectedYear(year);
                                            setSelectedDiv(div);
                                        }}
                                    >
                                        <span className="nav-icon">📅</span>
                                        Division {div}
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* MAIN CONTENT AREA */}
            <div className="main-content">
                <div className="page-header sticky-header">
                    <div className="header-content">
                        <h1>{selectedYear} - Division {selectedDiv}</h1>
                        {/* Dropdowns Removed */}
                    </div>

                    <div className="status-bar">
                        <div className="left-controls">
                            <div className={`status-indicator ${conflicts.length === 0 ? 'status-green' : 'status-red'}`}>
                                {conflicts.length === 0
                                    ? '✅ All Clear'
                                    : `🔴 ${conflicts.length} Conflicts Detected`
                                }
                            </div>
                            <div className="history-controls">
                                <button onClick={handleUndo} disabled={undoStack.length === 0} className="icon-btn" title="Undo">↩</button>
                                <button onClick={handleRedo} disabled={redoStack.length === 0} className="icon-btn" title="Redo">↪</button>
                            </div>
                        </div>

                        <div className="right-controls">
                            <button
                                onClick={() => generateFullTimetablePDF(transformToGrid(timetable, context.branchData), context.branchData)}
                                className="download-btn"
                                title="Download All Timetables"
                            >
                                📥 PDF
                            </button>
                            <button onClick={() => alert("Saved!")} className="save-btn">Save Changes</button>
                        </div>
                    </div>
                </div>

                <div className="grid-container">
                    <TimetableGrid
                        gridData={viewData}
                        conflictingSlots={conflictingSlotIds}
                        onSlotClick={handleSlotClick}
                    />
                </div>

                {editingSlot && (
                    <EditSlotModal
                        slot={editingSlot}
                        timetable={timetable}
                        context={context}
                        onSave={handleSlotSave}
                        onClose={() => setEditingSlot(null)}
                    />
                )}
            </div>
        </div>
    );
}

export default EditableTimetable;
