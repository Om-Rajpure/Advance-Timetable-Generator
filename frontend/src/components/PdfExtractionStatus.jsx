import React from 'react'
import PropTypes from 'prop-types'

function PdfExtractionStatus({ pdfInfo, isLoading, onContinue }) {
    if (!pdfInfo && !isLoading) return null

    return (
        <div className="pdf-extraction-status">
            <div className="extraction-card">
                {isLoading ? (
                    <div className="extraction-loading">
                        <div className="spinner"></div>
                        <h3>Analyzing PDF...</h3>
                        <p>This may take a moment</p>
                    </div>
                ) : (
                    <div className="extraction-result">
                        <div className="status-header">
                            <div className="status-icon">
                                {pdfInfo.type === 'scanned' ? '⚠️' : '✅'}
                            </div>
                            <h3>PDF Extraction Complete</h3>
                        </div>

                        <div className="extraction-details">
                            <div className="detail-item">
                                <span className="detail-label">PDF Type:</span>
                                <span className="detail-value">
                                    {pdfInfo.type === 'text-based' ? 'Text-based' : 'Scanned (OCR)'}
                                </span>
                            </div>
                            <div className="detail-item">
                                <span className="detail-label">Pages:</span>
                                <span className="detail-value">{pdfInfo.pages}</span>
                            </div>
                            <div className="detail-item">
                                <span className="detail-label">Extraction Method:</span>
                                <span className="detail-value">
                                    {pdfInfo.extractionMethod === 'ocr' ? 'OCR (Optical Character Recognition)' : 'Table Extraction'}
                                </span>
                            </div>
                            <div className="detail-item">
                                <span className="detail-label">Rows Extracted:</span>
                                <span className="detail-value">{pdfInfo.rowCount}</span>
                            </div>
                        </div>

                        {pdfInfo.type === 'scanned' && (
                            <div className="extraction-warning">
                                <div className="warning-icon">⚠️</div>
                                <div className="warning-content">
                                    <h4>Scanned PDF Detected</h4>
                                    <p>
                                        This PDF appears to be scanned. OCR extraction may not be fully accurate.
                                        <strong> Please review the extracted data carefully in the next step.</strong>
                                    </p>
                                </div>
                            </div>
                        )}

                        <div className="extraction-actions">
                            <button className="btn-continue" onClick={onContinue}>
                                Continue to Mapping →
                            </button>
                        </div>
                    </div>
                )}
            </div>

            <style jsx>{`
                .pdf-extraction-status {
                    display: flex;
                    justify-content: center;
                    padding: 2rem 0;
                }

                .extraction-card {
                    background: white;
                    border-radius: 12px;
                    padding: 2rem;
                    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
                    max-width: 600px;
                    width: 100%;
                }

                .extraction-loading {
                    text-align: center;
                    padding: 2rem;
                }

                .spinner {
                    width: 50px;
                    height: 50px;
                    border: 4px solid #f3f4f6;
                    border-top: 4px solid #6366f1;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    margin: 0 auto 1.5rem;
                }

                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }

                .extraction-loading h3 {
                    margin: 0 0 0.5rem;
                    color: #1f2937;
                }

                .extraction-loading p {
                    margin: 0;
                    color: #6b7280;
                }

                .extraction-result {
                    display: flex;
                    flex-direction: column;
                    gap: 1.5rem;
                }

                .status-header {
                    display: flex;
                    align-items: center;
                    gap: 1rem;
                }

                .status-icon {
                    font-size: 2.5rem;
                }

                .status-header h3 {
                    margin: 0;
                    color: #1f2937;
                }

                .extraction-details {
                    background: #f9fafb;
                    border-radius: 8px;
                    padding: 1.5rem;
                    display: flex;
                    flex-direction: column;
                    gap: 0.75rem;
                }

                .detail-item {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }

                .detail-label {
                    font-weight: 500;
                    color: #6b7280;
                }

                .detail-value {
                    color: #1f2937;
                    font-weight: 600;
                }

                .extraction-warning {
                    background: #fef3c7;
                    border: 2px solid #fbbf24;
                    border-radius: 8px;
                    padding: 1rem;
                    display: flex;
                    gap: 1rem;
                }

                .warning-icon {
                    font-size: 1.5rem;
                    flex-shrink: 0;
                }

                .warning-content h4 {
                    margin: 0 0 0.5rem;
                    color: #92400e;
                }

                .warning-content p {
                    margin: 0;
                    color: #78350f;
                    line-height: 1.6;
                }

                .extraction-actions {
                    display: flex;
                    justify-content: center;
                }

                .btn-continue {
                    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
                    color: white;
                    border: none;
                    padding: 0.875rem 2rem;
                    border-radius: 8px;
                    font-size: 1rem;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.3s ease;
                }

                .btn-continue:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 8px 20px rgba(99, 102, 241, 0.3);
                }
            `}</style>
        </div>
    )
}

PdfExtractionStatus.propTypes = {
    pdfInfo: PropTypes.shape({
        type: PropTypes.string,
        pages: PropTypes.number,
        extractionMethod: PropTypes.string,
        rowCount: PropTypes.number
    }),
    isLoading: PropTypes.bool,
    onContinue: PropTypes.func.isRequired
}

export default PdfExtractionStatus
