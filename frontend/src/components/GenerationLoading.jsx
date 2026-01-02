import React from 'react';
import '../styles/GenerationLoading.css';

const GenerationLoading = ({ status }) => {
    return (
        <div className="generation-loading-container">
            <div className="generation-content">
                <div className="ai-brain-pulse">
                    <div className="pulse-ring ring-1"></div>
                    <div className="pulse-ring ring-2"></div>
                    <div className="pulse-ring ring-3"></div>
                    <div className="brain-icon">🧠</div>
                </div>

                <h2 className="loading-title">Generating Intelligent Timetable</h2>
                <div className="loading-status-text">
                    {status || "Initializing AI Engine..."}
                </div>

                <div className="loading-steps">
                    <div className={`step ${status.includes('Preparing') ? 'active' : 'completed'}`}>
                        <span className="step-icon">📋</span> Validate Data
                    </div>
                    <div className={`step ${status.includes('Generating') ? 'active' : ''}`}>
                        <span className="step-icon">⚙️</span> Process Constraints
                    </div>
                    <div className={`step ${status.includes('Finalizing') ? 'active' : ''}`}>
                        <span className="step-icon">✨</span> Optimize Schedule
                    </div>
                </div>

                <p className="loading-tip">
                    Did you know? The engine evaluates over 10,000 possibilities to find the perfect fit.
                </p>
            </div>
        </div>
    );
};

export default GenerationLoading;
