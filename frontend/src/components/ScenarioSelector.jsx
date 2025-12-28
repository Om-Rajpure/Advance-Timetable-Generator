import React from 'react';
import './ScenarioSelector.css';

const ScenarioSelector = ({ scenarios, selectedScenario, onScenarioChange }) => {
    return (
        <div className="scenario-selector">
            <div className="scenario-grid">
                {scenarios.map((scenario) => (
                    <div
                        key={scenario.type}
                        className={`scenario-card ${selectedScenario?.type === scenario.type ? 'selected' : ''}`}
                        onClick={() => onScenarioChange(scenario)}
                    >
                        <div className="scenario-icon">{scenario.icon}</div>
                        <h3 className="scenario-name">{scenario.name}</h3>
                        <p className="scenario-description">{scenario.description}</p>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default ScenarioSelector;
