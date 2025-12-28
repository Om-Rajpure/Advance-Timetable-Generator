/**
 * Edit Validator Utility
 * 
 * Client-side helper for validating timetable edits.
 */

const API_BASE = 'http://localhost:5000/api/edit';

export async function validateEdit(modifiedSlot, timetable, context) {
    try {
        const response = await fetch(`${API_BASE}/validate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                modifiedSlot,
                timetable,
                ...context
            })
        });

        if (!response.ok) {
            throw new Error('Validation request failed');
        }

        return await response.json();
    } catch (error) {
        console.error('Validation error:', error);
        return {
            valid: false,
            conflicts: [{
                severity: 'HARD',
                constraint: 'System Error',
                message: 'Failed to validate edit. Please try again.'
            }],
            affectedSlots: [],
            severity: 'HARD'
        };
    }
}

export async function getAlternatives(slot, timetable, context) {
    try {
        const response = await fetch(`${API_BASE}/alternatives`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                slot,
                timetable,
                ...context
            })
        });

        if (!response.ok) {
            throw new Error('Alternatives request failed');
        }

        return await response.json();
    } catch (error) {
        console.error('Alternatives error:', error);
        return { teachers: [], rooms: [] };
    }
}

export async function saveTimetable(timetable, context) {
    try {
        const response = await fetch(`${API_BASE}/save`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                timetable,
                ...context
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Save failed');
        }

        return await response.json();
    } catch (error) {
        console.error('Save error:', error);
        throw error;
    }
}
