import React from 'react'
import '../styles/formComponents.css'

function ReviewCard({ title, icon, onEdit, children }) {
    return (
        <div className="review-card">
            <div className="review-card-header">
                <div className="review-card-title">
                    <span className="review-card-icon">{icon}</span>
                    <h3>{title}</h3>
                </div>
                {onEdit && (
                    <button className="btn-edit" onClick={onEdit}>
                        <span>✏️</span>
                        Edit
                    </button>
                )}
            </div>
            <div className="review-card-content">
                {children}
            </div>
        </div>
    )
}

export default ReviewCard
