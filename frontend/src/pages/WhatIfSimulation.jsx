import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './WhatIfSimulation.css';
import ScenarioSelector from '../components/ScenarioSelector';
import SimulationControls from '../components/SimulationControls';
import ImpactSummary from '../components/ImpactSummary';
import BeforeAfterCompare from '../components/BeforeAfterCompare';
import ApplySimulationButton from '../components/ApplySimulationButton';

const WhatIfSimulation = () => {
    const [branchId, setBranchId] = useState('');
    const [branches, setBranches] = useState([]);
    const [currentTimetable, setCurrentTimetable] = useState([]);
    const [selectedScenario, setSelectedScenario] = useState(null);
    const [availableScenarios, setAvailableScenarios] = useState([]);
    const [simulationParameters, setSimulationParameters] = useState({});
    const [simulationResult, setSimulationResult] = useState(null);
    const [isSimulating, setIsSimulating] = useState(false);
    const [error, setError] = useState(null);

    // Load available scenarios on mount
    useEffect(() => {
        loadScenarios();
        loadBranches();
    }, []);

    const loadScenarios = async () => {
        try {
            const response = await axios.get('http://localhost:5000/api/simulation/scenarios');
            setAvailableScenarios(response.data.scenarios);
        } catch (err) {
            console.error('Failed to load scenarios:', err);
        }
    };

    const loadBranches = async () => {
        try {
            const response = await axios.get('http://localhost:5000/api/branch/all');
            setBranches(response.data.branches);
        } catch (err) {
            console.error('Failed to load branches:', err);
        }
    };

    const handleScenarioChange = (scenario) => {
        setSelectedScenario(scenario);
        setSimulationParameters({});
        setSimulationResult(null);
        setError(null);
    };

    const handleParametersChange = (params) => {
        setSimulationParameters(params);
    };

    const runSimulation = async () => {
        setIsSimulating(true);
        setError(null);

        try {
            // For demo purposes, if no timetable is loaded, use a sample one
            const timetableToSimulate = currentTimetable.length > 0
                ? currentTimetable
                : generateSampleTimetable();

            const response = await axios.post('http://localhost:5000/api/simulation/run', {
                branchId: branchId,
                currentTimetable: timetableToSimulate,
                scenarioType: selectedScenario.type,
                parameters: simulationParameters
            });

            setSimulationResult(response.data);
        } catch (err) {
            setError(err.response?.data?.error || 'Failed to run simulation');
            console.error('Simulation error:', err);
        } finally {
            setIsSimulating(false);
        }
    };

    const applySimulation = async () => {
        if (!simulationResult) return;

        try {
            await axios.post('http://localhost:5000/api/simulation/apply', {
                branchId: branchId,
                simulatedTimetable: simulationResult.simulation.simulatedTimetable
            });

            alert('Simulation applied successfully!');
            setSimulationResult(null);
        } catch (err) {
            alert('Failed to apply simulation: ' + (err.response?.data?.error || err.message));
        }
    };

    const discardSimulation = () => {
        setSimulationResult(null);
    };

    const tryAnotherScenario = () => {
        setSelectedScenario(null);
        setSimulationParameters({});
        setSimulationResult(null);
        setError(null);
    };

    // Generate sample timetable for demo
    const generateSampleTimetable = () => {
        return [
            {
                id: 'Mon_0_FE_A',
                day: 'Monday',
                slot: 0,
                year: 'FE',
                division: 'A',
                subject: 'Mathematics',
                teacher: 'Prof. Neha',
                room: 'Room-101',
                type: 'Lecture'
            },
            {
                id: 'Mon_1_FE_A',
                day: 'Monday',
                slot: 1,
                year: 'FE',
                division: 'A',
                subject: 'Physics',
                teacher: 'Prof. Raj',
                room: 'Room-102',
                type: 'Lecture'
            }
            // Add more sample slots as needed
        ];
    };

    return (
        <div className="what-if-simulation">
            <div className="simulation-header">
                <h1>🔮 What-If Simulation Module</h1>
                <p className="subtitle">Test hypothetical changes safely before applying them</p>

                <div className="warning-banner">
                    <span className="warning-icon">⚠️</span>
                    <strong>This is a simulation.</strong> Your original timetable will not be changed unless you explicitly apply the results.
                </div>
            </div>

            {!simulationResult ? (
                <div className="simulation-setup">
                    {/* Branch Selection */}
                    <div className="setup-section">
                        <h2>1️⃣ Select Branch</h2>
                        <select
                            value={branchId}
                            onChange={(e) => setBranchId(e.target.value)}
                            className="branch-selector"
                        >
                            <option value="">Select a branch...</option>
                            {branches.map(branch => (
                                <option key={branch.id} value={branch.id}>
                                    {branch.branchName}
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Scenario Selection */}
                    <div className="setup-section">
                        <h2>2️⃣ Choose Scenario</h2>
                        <ScenarioSelector
                            scenarios={availableScenarios}
                            selectedScenario={selectedScenario}
                            onScenarioChange={handleScenarioChange}
                        />
                    </div>

                    {/* Parameter Configuration */}
                    {selectedScenario && (
                        <div className="setup-section">
                            <h2>3️⃣ Configure Parameters</h2>
                            <SimulationControls
                                scenario={selectedScenario}
                                parameters={simulationParameters}
                                onParametersChange={handleParametersChange}
                                branchId={branchId}
                            />
                        </div>
                    )}

                    {/* Run Button */}
                    {selectedScenario && (
                        <div className="run-simulation-section">
                            <button
                                onClick={runSimulation}
                                disabled={isSimulating || !branchId}
                                className="run-simulation-btn"
                            >
                                {isSimulating ? '⏳ Simulating...' : '▶️ Run Simulation'}
                            </button>
                        </div>
                    )}

                    {error && (
                        <div className="error-message">
                            <span className="error-icon">❌</span>
                            {error}
                        </div>
                    )}
                </div>
            ) : (
                <div className="simulation-results">
                    <h2>📊 Simulation Results</h2>

                    <Impact Summary report={simulationResult.report} />

                    <BeforeAfterCompare report={simulationResult.report} />

                    <ApplySimulationButton
                        onApply={applySimulation}
                        onDiscard={discardSimulation}
                        onTryAnother={tryAnotherScenario}
                        feasible={simulationResult.report.feasible}
                    />
                </div>
            )}
        </div>
    );
};

export default WhatIfSimulation;
