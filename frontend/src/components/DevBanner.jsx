import { isAuthEnabled } from '../auth/AuthContext'
import './DevBanner.css'

function DevBanner() {
    // Only show banner when authentication is bypassed
    if (isAuthEnabled) {
        return null
    }

    return (
        <div className="dev-banner">
            <div className="dev-banner-content">
                <span className="dev-banner-icon">🚧</span>
                <span className="dev-banner-text">
                    <strong>Development Mode:</strong> Authentication is temporarily disabled for core feature development
                </span>
            </div>
        </div>
    )
}

export default DevBanner
