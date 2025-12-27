import { useState, useEffect } from 'react'

const DRAFT_KEY = 'branchSetupDraft'
const DRAFT_TIMESTAMP_KEY = 'branchSetupDraftTimestamp'
const AUTO_SAVE_INTERVAL = 30000 // 30 seconds

/**
 * Hook for auto-saving and restoring draft branch setup data
 */
export function useDraftAutoSave(formData, setFormData) {
    const [lastSaved, setLastSaved] = useState(null)
    const [showSavedIndicator, setShowSavedIndicator] = useState(false)

    // Load draft on mount
    useEffect(() => {
        const savedDraft = localStorage.getItem(DRAFT_KEY)
        const savedTimestamp = localStorage.getItem(DRAFT_TIMESTAMP_KEY)

        if (savedDraft && savedTimestamp) {
            const draft = JSON.parse(savedDraft)
            const timestamp = new Date(savedTimestamp)

            // Only offer to restore if draft is less than 24 hours old and has content
            const hoursOld = (Date.now() - timestamp.getTime()) / (1000 * 60 * 60)
            if (hoursOld < 24 && draft.branchName) {
                const shouldRestore = window.confirm(
                    `Found an unsaved draft from ${timestamp.toLocaleString()}. Would you like to restore it?`
                )
                if (shouldRestore) {
                    setFormData(draft)
                    setLastSaved(timestamp)
                }
            }
        }
    }, []) // Only run on mount

    // Auto-save draft periodically
    useEffect(() => {
        const interval = setInterval(() => {
            // Only save if there's actual content (branch name at least)
            if (formData.branchName && formData.branchName.length > 0) {
                localStorage.setItem(DRAFT_KEY, JSON.stringify(formData))
                const now = new Date()
                localStorage.setItem(DRAFT_TIMESTAMP_KEY, now.toISOString())
                setLastSaved(now)

                // Show "saved" indicator briefly
                setShowSavedIndicator(true)
                setTimeout(() => setShowSavedIndicator(false), 2000)
            }
        }, AUTO_SAVE_INTERVAL)

        return () => clearInterval(interval)
    }, [formData])

    // Clear draft on successful submission
    const clearDraft = () => {
        localStorage.removeItem(DRAFT_KEY)
        localStorage.removeItem(DRAFT_TIMESTAMP_KEY)
        setLastSaved(null)
    }

    return {
        lastSaved,
        showSavedIndicator,
        clearDraft
    }
}
