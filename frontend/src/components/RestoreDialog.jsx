import React, { useState, useEffect } from 'react';
import './RestoreDialog.css';

function RestoreDialog({ version, branchId, context, onConfirm, onCancel }) {
    const [validation, setValidation] = useState(null);
    const [loading, setLoading] = useState(true);
    const [restoring, setRestoring] = useState(false);

    useEffect(() => {
        validateRestore();
    }, [version]);

    const validateRestore = async () => {
        setLoading(true);
        try {
            const response = await fetch('http://localhost:5000/api/history/restore', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    branchId,
                    versionId: version.versionId,
                    context
                })
            });

            const result = await response.json();
            setValidation(result);
        } catch (error) {
            console.error('Validation failed:', error);
            setValidation({
                success: false,
                canRestore: false,
                error: 'Failed to validate version'
            });
        } finally {
            setLoading(false);
        }
    };

    const handleConfirm = async () => {
        if (!validation?.canRestore) return;

        setRestoring(true);
        try {
            // Call onConfirm with the restored timetable
            await onConfirm(validation.timetable);
        } catch (error) {
            console.error('Restore failed:', error);
            alert('Failed to restore version');
        } finally {
            setRestoring(false);
        }
    };

    return (
        <div className="restore-dialog-overlay" onClick={onCancel}>
            <div className="restore-dialog" onClick={(e) => e.stopPropagation()}>
                <div className="restore-dialog__header">
                    <div className="restore-dialog__title">Restore Timetable Version</div>
                    <div className="restore-dialog__subtitle">
                        Review this version before restoring
                    </div>
                </div>

                <div className="restore-dialog__body">
                    <div className="restore-dialog__section">
                        <div className="restore-dialog__section-title">Version Details</div>
                        <div className="restore-dialog__version-info">
                            <div className="restore-dialog__info-row">
                                <span className="restore-dialog__label">Version ID:</span>
                                <span className="restore-dialog__value">{version.versionId}</span>
                            </div>
                            <div className="restore-dialog__info-row">
                                <span className="restore-dialog__label">Created:</span>
                                <span className="restore-dialog__value">{version.timestampFormatted}</span>
                            </div>
                            <div className="restore-dialog__info-row">
                                <span className="restore-dialog__label">Action:</span>
                                <span className="restore-dialog__value">{version.action}</span>
                            </div>
                            <div className="restore-dialog__info-row">
                                <span className="restore-dialog__label">Quality Score:</span>
                                <span className="restore-dialog__value">{version.qualityScore}%</span>
                            </div>
                        </div>
                    </div>

                    {loading && (
                        <div className="restore-dialog__section">
                            <div className="restore-dialog__warning">
                                <div className="restore-dialog__warning-icon">⏳</div>
                                <div className="restore-dialog__warning-text">
                                    Validating version compatibility...
                                </div>
                            </div>
                        </div>
                    )}

                    {!loading && validation && (
                        <>
                            {validation.canRestore ? (
                                <div className="restore-dialog__section">
                                    <div className="restore-dialog__warning">
                                        <div className="restore-dialog__warning-icon">⚠️</div>
                                        <div className="restore-dialog__warning-text">
                                            <strong>This will replace your current timetable.</strong>
                                            <br />
                                            Make sure you want to proceed with this action.
                                            {validation.validation?.warnings?.length > 0 && (
                                                <>
                                                    <br /><br />
                                                    <strong>Warnings:</strong>
                                                    <ul>
                                                        {validation.validation.warnings.map((w, i) => (
                                                            <li key={i}>{w.message}</li>
                                                        ))}
                                                    </ul>
                                                </>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            ) : (
                                <div className="restore-dialog__section">
                                    <div className="restore-dialog__error">
                                        <div className="restore-dialog__error-title">
                                            Cannot Restore This Version
                                        </div>
                                        {validation.validation?.errors && (
                                            <ul className="restore-dialog__error-list">
                                                {validation.validation.errors.map((err, i) => (
                                                    <li key={i} className="restore-dialog__error-item">
                                                        {err.message}
                                                    </li>
                                                ))}
                                            </ul>
                                        )}
                                        {validation.error && (
                                            <div className="restore-dialog__error-item">
                                                {validation.error}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}
                        </>
                    )}
                </div>

                <div className="restore-dialog__footer">
                    <button
                        className="restore-dialog__btn"
                        onClick={onCancel}
                        disabled={restoring}
                    >
                        Cancel
                    </button>
                    <button
                        className={`restore-dialog__btn ${validation?.canRestore ? 'restore-dialog__btn--primary' : 'restore-dialog__btn--danger'}`}
                        onClick={handleConfirm}
                        disabled={!validation?.canRestore || loading || restoring}
                    >
                        {restoring ? 'Restoring...' : validation?.canRestore ? 'Confirm Restore' : 'Cannot Restore'}
                    </button>
                </div>
            </div>
        </div>
    );
}

export default RestoreDialog;
