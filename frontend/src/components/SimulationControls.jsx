import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './SimulationControls.css';

const SimulationControls = ({ scenario, parameters, onParametersChange, branchId }) => {
    const [teachers, setTeachers] = useState([]);
    const [labs, setLabs] = useState([]);
    const [workingDays, setWorkingDays] = useState([]);

    useEffect(() => {
        if (branchId) {
            loadBranchData();
        }
    }, [branchId]);

    const loadBranchData = async () => {
        try {
            const response = await axios.get(`http://localhost:5000/api/branch/${branchId}`);
            const branch = response.data.branch;

            setLabs(branch.labs || []);
            setWorkingDays(branch.workingDays || ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']);

            // For teachers, you'd load from smart input data
            // For now, using sample data
            setTeachers(['Prof. Neha', 'Prof. Raj', 'Prof. Sharma']);
        } catch (err) {
            console.error('Failed to load branch data:', err);
        }
    };

    const handleChange = (key, value) => {
        onParametersChange({
            ...parameters,
            [key]: value
        });
    };

    // Render controls based on scenario type
    const renderControls = () => {
        switch (scenario.type) {
            case 'TEACHER_UNAVAILABLE':
                return renderTeacherUnavailableControls();
            case 'LAB_UNAVAILABLE':
                return renderLabUnavailableControls();
            case 'DAYS_REDUCED':
                return renderDaysReducedControls();
            default:
                return <div>Select a scenario to configure parameters</div>;
        }
    };

    const renderTeacherUnavailableControls = () => {
        const unavailableSpec = parameters.unavailableSpec || {};

        return (
            <div className="controls-form">
                <div className="form-group">
                    <label>Teacher</label>
                    <select
                        value={parameters.teacherName || ''}
                        onChange={(e) => handleChange('teacherName', e.target.value)}
                        className="form-control"
                    >
                        <option value="">Select teacher...</option>
                        {teachers.map(teacher => (
                            <option key={teacher} value={teacher}>{teacher}</option>
                        ))}
                    </select>
                </div>

                <div className="form-group">
                    <label>Unavailability Type</label>
                    <div className="radio-group">
                        <label className="radio-option">
                            <input
                                type="radio"
                                name="unavailabilityType"
                                checked={unavailableSpec.fullWeek === true}
                                onChange={() => handleChange('unavailableSpec', { fullWeek: true })}
                            />
                            <span>Full Week</span>
                        </label>
                        <label className="radio-option">
                            <input
                                type="radio"
                                name="unavailabilityType"
                                checked={unavailableSpec.fullWeek !== true}
                                onChange={() => handleChange('unavailableSpec', {})}
                            />
                            <span>Specific Days</span>
                        </label>
                    </div>
                </div>

                {!unavailableSpec.fullWeek && (
                    <div className="form-group">
                        <label>Select Unavailable Days</label>
                        <div className="checkbox-group">
                            {workingDays.map(day => (
                                <label key={day} className="checkbox-option">
                                    <input
                                        type="checkbox"
                                        checked={(unavailableSpec.days || []).includes(day)}
                                        onChange={(e) => {
                                            const days = unavailableSpec.days || [];
                                            const newDays = e.target.checked
                                                ? [...days, day]
                                                : days.filter(d => d !== day);
                                            handleChange('unavailableSpec', { ...unavailableSpec, days: newDays });
                                        }}
                                    />
                                    <span>{day}</span>
                                </label>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        );
    };

    const renderLabUnavailableControls = () => {
        return (
            <div className="controls-form">
                <div className="form-group">
                    <label>Lab</label>
                    <select
                        value={parameters.labName || ''}
                        onChange={(e) => handleChange('labName', e.target.value)}
                        className="form-control"
                    >
                        <option value="">Select lab...</option>
                        {labs.map(lab => (
                            <option key={lab} value={lab}>{lab}</option>
                        ))}
                    </select>
                </div>
            </div>
        );
    };

    const renderDaysReducedControls = () => {
        const selectedDays = parameters.newWorkingDays || workingDays;

        return (
            <div className="controls-form">
                <div className="form-group">
                    <label>New Working Days</label>
                    <div className="checkbox-group">
                        {workingDays.map(day => (
                            <label key={day} className="checkbox-option">
                                <input
                                    type="checkbox"
                                    checked={selectedDays.includes(day)}
                                    onChange={(e) => {
                                        const newDays = e.target.checked
                                            ? [...selectedDays, day]
                                            : selectedDays.filter(d => d !== day);
                                        handleChange('newWorkingDays', newDays);
                                    }}
                                />
                                <span>{day}</span>
                            </label>
                        ))}
                    </div>
                    <small className="help-text">
                        Currently selected: {selectedDays.length} day(s)
                    </small>
                </div>
            </div>
        );
    };

    return (
        <div className="simulation-controls">
            {renderControls()}
        </div>
    );
};

export default SimulationControls;
