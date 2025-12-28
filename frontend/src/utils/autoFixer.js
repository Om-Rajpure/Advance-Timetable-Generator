/**
 * Auto-Fixer Utility
 * 
 * Client-side helper for getting auto-fix suggestions.
 */

const API_BASE = 'http://localhost:5000/api/edit';

export async function getSuggestedFix(slot, conflicts, timetable, context) {
    try {
        const response = await fetch(`${API_BASE}/suggest-fix`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                slot,
                conflicts,
                timetable,
                ...context
            })
        });

        if (!response.ok) {
            throw new Error('Auto-fix request failed');
        }

        return await response.json();
    } catch (error) {
        console.error('Auto-fix error:', error);
        return {
            fix: null,
            explanation: 'Failed to generate fix suggestions',
            strategy: null
        };
    }
}
