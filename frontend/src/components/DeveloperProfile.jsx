import React, { useEffect } from 'react';
import './DeveloperProfile.css';

/**
 * Developer Intro Card Overlay
 * Shows developer details and social links.
 */
function DeveloperProfile({ isOpen, onClose }) {

    // Close on Escape key
    useEffect(() => {
        const handleEsc = (e) => {
            if (e.key === 'Escape') onClose();
        };
        if (isOpen) {
            window.addEventListener('keydown', handleEsc);
            // Prevent body scroll when modal is open
            document.body.style.overflow = 'hidden';
        }
        return () => {
            window.removeEventListener('keydown', handleEsc);
            document.body.style.overflow = 'unset';
        };
    }, [isOpen, onClose]);

    if (!isOpen) return null;

    // GitHub Avatar
    const avatarUrl = "https://github.com/Om-Rajpure.png";
    const profileUrl = "https://github.com/Om-Rajpure";

    return (
        <div className="dev-modal-overlay" onClick={onClose}>
            <div className="dev-card" onClick={(e) => e.stopPropagation()}>
                <div className="dev-title">Developer</div>

                <div className="dev-avatar-container">
                    <img
                        src={avatarUrl}
                        alt="Om Rajpure"
                        className="dev-avatar"
                        onError={(e) => { e.target.src = "https://ui-avatars.com/api/?name=Om+Rajpure&background=6366f1&color=fff"; }}
                    />
                </div>

                <h2 className="dev-name">Om Rajpure</h2>
                <p className="dev-subtitle">3rd year AI&DS – B</p>

                <div className="dev-socials">
                    {/* GitHub */}
                    <a
                        href="https://github.com/Om-Rajpure"
                        target="_blank"
                        rel="noreferrer"
                        className="social-btn github"
                        title="GitHub"
                    >
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path>
                        </svg>
                    </a>

                    {/* LinkedIn */}
                    <a
                        href="https://www.linkedin.com/in/om-rajpure"
                        target="_blank"
                        rel="noreferrer"
                        className="social-btn linkedin"
                        title="LinkedIn"
                    >
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"></path>
                            <rect x="2" y="9" width="4" height="12"></rect>
                            <circle cx="4" cy="4" r="2"></circle>
                        </svg>
                    </a>

                    {/* YouTube */}
                    <a
                        href="https://youtube.com/@conceptsin5"
                        target="_blank"
                        rel="noreferrer"
                        className="social-btn youtube"
                        title="YouTube"
                    >
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M22.54 6.42a2.78 2.78 0 0 0-1.94-2C18.88 4 12 4 12 4s-6.88 0-8.6.46a2.78 2.78 0 0 0-1.94 2A29 29 0 0 0 1 11.75a29 29 0 0 0 .46 5.33A2.78 2.78 0 0 0 3.4 19c1.72.46 8.6.46 8.6.46s6.88 0 8.6-.46a2.78 2.78 0 0 0 1.94-2 29 29 0 0 0 .46-5.33 29 29 0 0 0-.46-5.33z"></path>
                            <polygon points="9.75 15.02 15.5 11.75 9.75 8.48 9.75 15.02"></polygon>
                        </svg>
                    </a>

                    {/* Instagram */}
                    <a
                        href="https://www.instagram.com/om_rajpure_"
                        target="_blank"
                        rel="noreferrer"
                        className="social-btn instagram"
                        title="Instagram"
                    >
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <rect x="2" y="2" width="20" height="20" rx="5" ry="5"></rect>
                            <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"></path>
                            <line x1="17.5" y1="6.5" x2="17.51" y2="6.5"></line>
                        </svg>
                    </a>
                </div>
            </div>
        </div>
    );
}

export default DeveloperProfile;
