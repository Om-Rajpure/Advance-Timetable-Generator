import React from 'react'

/**
 * Loading state component for Suspense fallback
 * Provides visual feedback during lazy component loading
 */
function LoadingState({ message = 'Loading...' }) {
    return (
        <div className="loading-state">
            <div className="loading-spinner">
                <div className="spinner"></div>
            </div>
            <p className="loading-message">{message}</p>
        </div>
    )
}

export default LoadingState
