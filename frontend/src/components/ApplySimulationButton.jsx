import React, { useState } from 'react';
import './ApplySimulationButton.css';

const ApplySimulationButton = ({ onApply, onDiscard, onTryAnother, feasible }) => {
    const [showConfirmModal, setShowConfirmModal] = useState(false);

    const handleApplyClick = () => {
        if (feasible) {
            setShowConfirmModal(true);
        } else {
            alert('Cannot apply an infeasible simulation. Please try a different scenario or parameters.');
        }
    };

    const confirmApply = () => {
        setShowConfirmModal(false);
        onApply();
    };

    const cancelApply = () => {
        setShowConfirmModal(false);
    };

    return (
        <>
            <div className="apply-simulation-buttons">
                <button
                    onClick={handleApplyClick}
                    className={`simulation-btn apply-btn ${!feasible ? 'disabled' : ''}`}
                    disabled={!feasible}
                >
                    ✅ Apply This Change
                </button>

                <button
                    onClick={onDiscard}
                    className="simulation-btn discard-btn"
                >
                    ❌ Discard Simulation
                </button>

                <button
                    onClick={onTryAnother}
                    className="simulation-btn try-another-btn"
                >
                    🔁 Try Another Scenario
                </button>
            </div>

            {showConfirmModal && (
                <div className="modal-overlay" onClick={cancelApply}>
                    <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                        <h3>⚠️ Confirm Application</h3>
                        <p>
                            Are you sure you want to apply this simulation? This will replace your current timetable with the simulated version.
                        </p>
                        <p className="modal-warning">
                            <strong>This action will overwrite your existing timetable.</strong>
                        </p>

                        <div className="modal-actions">
                            <button onClick={confirmApply} className="confirm-btn">
                                Yes, Apply Changes
                            </button>
                            <button onClick={cancelApply} className="cancel-btn">
                                Cancel
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
};

export default ApplySimulationButton;
